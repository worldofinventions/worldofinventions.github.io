"""«Музей изобретений русских людей» внутри общего сервера экосистемы.

miniapp/server.py подключает это приложение под префиксом /ru:

* /ru/                   — Mini App (сборка ru/miniapp/web)
* /ru/api/...            — JSON API поверх ru/data и базы ru/data/museum.db
* /ru/exhibits/<id>.jpg  — фото экспонатов (ru/site/public/exhibits)
* /ru/telegram-webhook   — обновления для @lshpdigitalmuseumbot

Бот работает только если задан RU_BOT_TOKEN. На хостинге (WEBHOOK_BASE_URL /
RENDER_EXTERNAL_URL) он получает обновления через webhook, локально — через
long polling. Внимание: и то и другое переключает бота с прежнего хостинга
(ManyBot) на этот сервер.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
import random
import time
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import parse_qsl

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import MenuButtonWebApp, WebAppInfo

from . import database as dbms
from . import handlers as museum
from .config import ADMIN_ID, BOT_TOKEN

HERE = Path(__file__).resolve().parent
WEB_DIR = HERE / "miniapp" / "web"
EXHIBIT_IMAGES_DIR = HERE / "site" / "public" / "exhibits"
PREFIX = "/ru"
WEBHOOK_PATH = "/telegram-webhook"
# Telegram присылает этот секрет с каждым обновлением; допустимы только A-Z, a-z, 0-9, _ и -.
WEBHOOK_SECRET = (
    os.getenv("RU_WEBHOOK_SECRET", "").strip()
    or (hashlib.sha256(BOT_TOKEN.encode()).hexdigest()[:48] if BOT_TOKEN else "")
)

log = logging.getLogger("ru-museum")

FEEDBACK_LIMIT = 4000
QUIZ_SESSIONS: dict[int, dict] = {}
QUIZ_SESSION_TTL = 6 * 60 * 60  # секунд

_bot: Bot | None = None


def enabled() -> bool:
    return bool(BOT_TOKEN)


def get_bot(telegram_disabled: bool) -> Bot | None:
    global _bot
    if telegram_disabled or not BOT_TOKEN:
        return None
    if _bot is None:
        _bot = Bot(token=BOT_TOKEN)
    return _bot


_dispatcher: Dispatcher | None = None


def build_dispatcher() -> Dispatcher:
    """Один диспетчер на процесс: роутер aiogram можно подключить только один раз."""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = Dispatcher(storage=MemoryStorage())
        _dispatcher.include_router(museum.router)
    return _dispatcher


# ------------------------------------------------------------------ авторизация Telegram
def verify_init_data(raw: str) -> dict | None:
    """Проверка initData Telegram WebApp (HMAC-SHA256, по документации Telegram)."""
    if not BOT_TOKEN:
        return None
    try:
        pairs = dict(parse_qsl(raw, keep_blank_values=True))
    except Exception:
        return None
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        return None
    data_check_string = "\n".join(f"{key}={pairs[key]}" for key in sorted(pairs))
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_hash, received_hash):
        return None
    try:
        auth_date = int(pairs.get("auth_date", "0"))
    except ValueError:
        return None
    if not auth_date or time.time() - auth_date > 86400:
        return None
    try:
        user = json.loads(pairs.get("user", "null"))
    except ValueError:
        return None
    if not isinstance(user, dict) or not user.get("id"):
        return None
    return user


def resolve_user(request: web.Request) -> dict:
    """Настоящий пользователь Telegram из initData или демо-пользователь при локальной разработке."""
    raw = request.headers.get("X-Telegram-Init-Data", "")
    user = verify_init_data(raw) if raw else None
    if user:
        return user
    if not request.app["webhook_base_url"]:
        try:
            uid = int(request.query.get("uid", "0")) or 900000001
        except ValueError:
            uid = 900000001
        return {"id": uid, "first_name": "Гость", "last_name": "", "username": "dev_user"}
    raise web.HTTPUnauthorized(text="Не удалось проверить авторизацию Telegram")


async def read_json(request: web.Request) -> dict:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def json_error(status: int, message: str) -> web.Response:
    return web.json_response({"error": message}, status=status)


@web.middleware
async def api_middleware(request: web.Request, handler):
    try:
        response = await handler(request)
    except web.HTTPException:
        raise
    except asyncio.CancelledError:
        raise
    except Exception:
        log.exception("Unhandled error on %s %s", request.method, request.path)
        response = json_error(500, "Что-то пошло не так. Попробуйте ещё раз.")
    if request.path.startswith(f"{PREFIX}/api"):
        response.headers["Cache-Control"] = "no-store"
    return response


# ------------------------------------------------------------------ данные
def stats_payload(raw_stats: dict) -> dict:
    raw_stats = dict(raw_stats)
    raw_stats["studied_exhibits"] = min(raw_stats["studied_exhibits"], len(museum.INVENTIONS))
    raw_stats["opened_halls"] = min(raw_stats["opened_halls"], len(museum.HALLS))
    total_answers = raw_stats["total_answers"]
    raw_stats["accuracy"] = round(100 * raw_stats["correct_answers"] / total_answers) if total_answers else None
    return raw_stats


def bootstrap_payload(user: dict, favorites: list[str], stats: dict) -> dict:
    exhibits = museum.INVENTIONS
    counts = Counter(country for item in exhibits for country in item["map_countries"])
    countries = [
        {
            "name": country,
            "flag": museum.COUNTRY_INFO[country][0],
            "continent": museum.COUNTRY_INFO[country][1],
            "count": counts[country],
        }
        for country in museum.COUNTRIES
    ]
    halls = [
        {
            "id": hall_id,
            "title": hall["title"],
            "name": hall["name"],
            "description": hall["description"],
            "count": sum(1 for item in exhibits if str(item["hall"]) == hall_id),
        }
        for hall_id, hall in museum.HALLS.items()
    ]
    return {
        "museum_name": museum.MUSEUM_NAME,
        "user": {
            "id": user["id"],
            "name": " ".join(filter(None, [user.get("first_name"), user.get("last_name")])).strip()
            or "Посетитель",
            "username": user.get("username"),
        },
        "exhibits": exhibits,
        "halls": halls,
        "countries": countries,
        "periods": museum.PERIODS,
        "favorites": favorites,
        "stats": stats_payload(stats),
        "totals": {"exhibits": len(exhibits), "halls": len(halls)},
    }


def history_payload(today: date) -> dict:
    exact = sorted(
        (e for e in museum.HISTORY if (e["month"], e["day"]) == (today.month, today.day)),
        key=lambda e: e["year"],
    )
    events: list[dict] = []
    if exact:
        for event in exact[:3]:
            events.append(_history_event(event, None))
    else:
        upcoming = min(museum.HISTORY, key=lambda e: museum.next_occurrence(e, today))
        past = max(museum.HISTORY, key=lambda e: museum.previous_occurrence(e, today))
        ahead = (museum.next_occurrence(upcoming, today) - today).days
        behind = (today - museum.previous_occurrence(past, today)).days
        ordered = [past, upcoming] if behind <= ahead else [upcoming, past]
        for event in ordered:
            day_label = f"{event['day']} {museum.MONTH_NAMES[event['month'] - 1]}"
            if event is upcoming:
                when = "завтра" if ahead == 1 else f"через {ahead} {museum.days_word(ahead)}"
            else:
                when = "вчера" if behind == 1 else f"{behind} {museum.days_word(behind)} назад"
            events.append(_history_event(event, f"{when} · {day_label}"))
    related: list[str] = []
    for event in events:
        related_id = event.get("related_id")
        if related_id and related_id not in related:
            related.append(related_id)
    return {
        "date_label": f"{today.day} {museum.MONTH_NAMES[today.month - 1]}",
        "exact": bool(exact),
        "events": events,
        "related": related,
    }


def _history_event(event: dict, when: str | None) -> dict:
    return {
        "icon": museum.HISTORY_KIND_ICONS.get(event["kind"], "📅"),
        "year": event["year"],
        "title": event["title"],
        "text": event["text"],
        "related_id": event.get("related_id"),
        "when": when,
    }


def prune_quiz_sessions() -> None:
    now = time.time()
    for user_id in [uid for uid, s in QUIZ_SESSIONS.items() if now - s["ts"] > QUIZ_SESSION_TTL]:
        QUIZ_SESSIONS.pop(user_id, None)


def quiz_question_payload(session: dict) -> dict:
    question = museum.QUIZ[session["order"][session["index"]]]
    options = [question["options"][i] for i in session["option_orders"][session["index"]]]
    return {
        "index": session["index"],
        "total": len(session["order"]),
        "question": question["question"],
        "options": options,
    }


# ------------------------------------------------------------------ API
async def api_bootstrap(request: web.Request) -> web.Response:
    user = resolve_user(request)
    favorites = await museum.db_call(dbms.get_favorites, user["id"], default=[])
    favorites = [i for i in favorites if i in museum.BY_ID]
    raw = await museum.db_call(dbms.get_stats, user["id"])
    if raw is None:
        raw = {"studied_exhibits": 0, "correct_answers": 0, "total_answers": 0, "quizzes_completed": 0,
               "opened_halls": 0, "favorites": 0}
    return web.json_response(bootstrap_payload(user, favorites, raw))


async def api_progress_studied(request: web.Request) -> web.Response:
    user = resolve_user(request)
    body = await read_json(request)
    invention_id = str(body.get("id", ""))
    if invention_id not in museum.BY_ID:
        return json_error(404, "Экспонат не найден.")
    await museum.db_call(dbms.mark_exhibit_studied, user["id"], invention_id)
    return web.json_response({"ok": True})


async def api_progress_hall(request: web.Request) -> web.Response:
    user = resolve_user(request)
    body = await read_json(request)
    hall_id = str(body.get("hall", ""))
    if hall_id not in museum.HALLS:
        return json_error(404, "Зал не найден.")
    await museum.db_call(dbms.mark_hall_opened, user["id"], hall_id)
    return web.json_response({"ok": True})


async def api_favorite_toggle(request: web.Request) -> web.Response:
    user = resolve_user(request)
    invention_id = request.match_info["invention_id"]
    if invention_id not in museum.BY_ID:
        return json_error(404, "Экспонат не найден.")
    saved = await museum.db_call(dbms.toggle_favorite, user["id"], invention_id)
    if saved is None:
        return json_error(500, "Избранное сейчас недоступно.")
    return web.json_response({"saved": saved})


async def api_stats(request: web.Request) -> web.Response:
    user = resolve_user(request)
    raw = await museum.db_call(dbms.get_stats, user["id"])
    if raw is None:
        return json_error(500, "Статистика сейчас недоступна.")
    return web.json_response(stats_payload(raw))


async def api_history_today(request: web.Request) -> web.Response:
    resolve_user(request)
    return web.json_response(history_payload(museum.today_date()))


async def api_quiz_start(request: web.Request) -> web.Response:
    user = resolve_user(request)
    prune_quiz_sessions()
    round_size = min(museum.QUIZ_ROUND_SIZE, len(museum.QUIZ))
    order = random.sample(range(len(museum.QUIZ)), k=round_size)
    option_orders = []
    for question_index in order:
        option = list(range(len(museum.QUIZ[question_index]["options"])))
        random.shuffle(option)
        option_orders.append(option)
    QUIZ_SESSIONS[user["id"]] = {"order": order, "option_orders": option_orders, "index": 0, "score": 0, "ts": time.time()}
    return web.json_response(quiz_question_payload(QUIZ_SESSIONS[user["id"]]))


async def api_quiz_answer(request: web.Request) -> web.Response:
    user = resolve_user(request)
    session = QUIZ_SESSIONS.get(user["id"])
    if session is None:
        return json_error(404, "Викторина не начата. Начните новый раунд.")
    body = await read_json(request)
    try:
        choice = int(body.get("choice"))
    except (TypeError, ValueError):
        return json_error(400, "Неверный ответ.")
    if session["index"] >= len(session["order"]):
        return json_error(404, "Этот раунд уже закончен.")
    if not 0 <= choice < len(session["option_orders"][session["index"]]):
        return json_error(400, "Неверный ответ.")
    question = museum.QUIZ[session["order"][session["index"]]]
    original_index = session["option_orders"][session["index"]][choice]
    correct = original_index == question["answer"]
    await museum.db_call(dbms.record_answer, user["id"], correct)
    session["score"] += int(correct)
    session["index"] += 1
    session["ts"] = time.time()
    finished = session["index"] >= len(session["order"])
    if finished:
        await museum.db_call(dbms.record_quiz_completed, user["id"])
    return web.json_response({
        "correct": correct,
        "correct_option": question["options"][question["answer"]],
        "fact": question["fact"],
        "score": session["score"],
        "answered": session["index"],
        "total": len(session["order"]),
        "finished": finished,
    })


async def api_quiz_next(request: web.Request) -> web.Response:
    user = resolve_user(request)
    session = QUIZ_SESSIONS.get(user["id"])
    if session is None:
        return json_error(404, "Викторина не начата. Начните новый раунд.")
    if session["index"] >= len(session["order"]):
        return json_error(404, "Этот раунд уже закончен.")
    return web.json_response(quiz_question_payload(session))


async def api_feedback(request: web.Request) -> web.Response:
    user = resolve_user(request)
    body = await read_json(request)
    feedback = str(body.get("message", "")).strip()
    if not feedback:
        return json_error(400, "Сообщение пустое.")
    feedback = feedback[:FEEDBACK_LIMIT]
    bot = get_bot(request.app["telegram_disabled"])
    if bot is None:
        return json_error(503, "Telegram в этом запуске отключён, отзыв отправить нельзя.")
    if not ADMIN_ID:
        log.warning("Feedback received but ADMIN_ID is not configured. User ID: %s; message: %s", user["id"], feedback)
        return json_error(503, "Почтовый ящик проекта ещё не настроен.")
    username = f"@{user['username']}" if user.get("username") else "нет имени пользователя"
    full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
    report = (
        "📩 Новый отзыв из мини-приложения (Музей изобретений русских людей)\n\n"
        f"От: {full_name}\n"
        f"Имя пользователя: {username}\n"
        f"Telegram ID: {user['id']}\n\n"
        f"Сообщение:\n{feedback}"
    )
    try:
        await bot.send_message(ADMIN_ID, report)
    except Exception as exc:
        log.warning("Could not deliver feedback from %s: %s", user["id"], exc)
        return json_error(502, "Не получилось доставить сообщение. Попробуйте позже.")
    return web.json_response({"ok": True})


async def health(request: web.Request) -> web.Response:
    app = request.app
    mode = "disabled" if app["telegram_disabled"] or not BOT_TOKEN else ("webhook" if app["webhook_base_url"] else "polling")
    return web.Response(text=f"Russian Inventions museum is running. Telegram: {mode}. "
                             f"{len(museum.INVENTIONS)} exhibits.")


async def index(_request: web.Request) -> web.Response:
    if not (WEB_DIR / "index.html").is_file():
        return web.Response(status=503, text="Mini App ещё не собрана: cd ru/miniapp/ui && npm run build")
    response = web.FileResponse(WEB_DIR / "index.html")
    response.headers["Cache-Control"] = "no-cache"
    return response


# ------------------------------------------------------------------ Telegram
async def set_menu_button(bot: Bot, base_url: str) -> None:
    """Кнопка меню рядом с полем ввода открывает Mini App музея."""
    url = f"{base_url}{PREFIX}/"
    if not url.startswith("https://"):
        log.info("RU menu button left as is (the mini app URL is not public https).")
        return
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="🏛 Музей", web_app=WebAppInfo(url=url))
        )
        log.info("RU mini app is now the bot's menu button: %s", url)
    except Exception as exc:
        log.warning("Could not set the RU menu button: %s", exc)


async def set_bot_profile(bot: Bot) -> None:
    """Описание и команды бота. Прежнее описание (из ManyBot) заменяется."""
    from aiogram.types import BotCommand
    try:
        await bot.set_my_commands([
            BotCommand(command="start", description="Главное меню музея"),
            BotCommand(command="help", description="Что умеет бот"),
        ])
        await bot.set_my_description(
            "Музей изобретений русских людей: образовательный проект Ломоносовской школы-пансиона. "
            f"{len(museum.INVENTIONS)} {museum.exhibits_word(len(museum.INVENTIONS))} в четырёх залах, от глаголицы до графена. "
            "Викторина, «Этот день в истории» и избранное. Нажмите «Запустить»."
        )
    except Exception as exc:
        log.warning("Could not update the RU bot profile: %s", exc)


async def on_startup(app: web.Application) -> None:
    bot = get_bot(app["telegram_disabled"])
    if bot is None:
        log.info("RU museum: Telegram is off (no RU_BOT_TOKEN or MINIAPP_DISABLE_TELEGRAM=1).")
        return
    base = app["webhook_base_url"]
    if base:
        await bot.set_webhook(f"{base}{PREFIX}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET, drop_pending_updates=False)
        await set_menu_button(bot, base)
        await set_bot_profile(bot)
        from branding import RU_AVATAR, RU_NAME, apply_branding
        await apply_branding(
            bot, RU_NAME,
            "Изобретения и открытия из истории России. Соседний музей на английском: @worldofinventions_app",
            RU_AVATAR,
        )
        log.info("RU museum webhook: %s%s%s", base, PREFIX, WEBHOOK_PATH)
    else:
        dispatcher = build_dispatcher()
        try:
            await bot.delete_webhook(drop_pending_updates=False)
        except Exception as exc:
            log.warning("Could not delete the RU webhook: %s", exc)
        app["ru_polling_task"] = asyncio.create_task(dispatcher.start_polling(bot, handle_signals=False))
        log.info("RU museum: polling mode.")


async def on_cleanup(app: web.Application) -> None:
    task = app.get("ru_polling_task")
    if task:
        task.cancel()
    if _bot is not None:
        try:
            await _bot.session.close()
        except Exception:
            pass


def build_subapp(webhook_base_url: str, telegram_disabled: bool) -> web.Application:
    """Приложение, которое miniapp/server.py монтирует под /ru."""
    dbms.init_db()
    app = web.Application(middlewares=[api_middleware])
    app["webhook_base_url"] = webhook_base_url
    app["telegram_disabled"] = telegram_disabled
    app.router.add_get("/healthz", health)

    bot = get_bot(telegram_disabled)
    if webhook_base_url and bot is not None:
        from aiogram.webhook.aiohttp_server import SimpleRequestHandler

        SimpleRequestHandler(dispatcher=build_dispatcher(), bot=bot, secret_token=WEBHOOK_SECRET).register(
            app, path=WEBHOOK_PATH
        )

    app.router.add_get("/api/bootstrap", api_bootstrap)
    app.router.add_post("/api/progress/studied", api_progress_studied)
    app.router.add_post("/api/progress/hall", api_progress_hall)
    app.router.add_post("/api/favorites/{invention_id}/toggle", api_favorite_toggle)
    app.router.add_get("/api/stats", api_stats)
    app.router.add_get("/api/history/today", api_history_today)
    app.router.add_post("/api/quiz/start", api_quiz_start)
    app.router.add_post("/api/quiz/answer", api_quiz_answer)
    app.router.add_post("/api/quiz/next", api_quiz_next)
    app.router.add_post("/api/feedback", api_feedback)

    app.router.add_get("/", index)
    EXHIBIT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    app.router.add_static("/exhibits/", EXHIBIT_IMAGES_DIR, name="ru-exhibit-images")
    WEB_DIR.mkdir(parents=True, exist_ok=True)
    app.router.add_static("/", WEB_DIR, name="ru-web")
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app


def mount(parent: web.Application, webhook_base_url: str, telegram_disabled: bool) -> None:
    """Подключает русский музей к общему серверу: /ru/... и редирект /ru → /ru/."""

    async def redirect(_request: web.Request) -> web.Response:
        raise web.HTTPFound(f"{PREFIX}/")

    parent.router.add_get(PREFIX, redirect)
    parent.add_subapp(PREFIX, build_subapp(webhook_base_url, telegram_disabled))
