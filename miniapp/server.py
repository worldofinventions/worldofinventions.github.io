"""World of Inventions — Telegram Mini App server (project version 2).

What it does
------------
* Serves the mini app itself (static files from ``miniapp/web``).
* Serves a JSON API (favorites, statistics, quiz, "This Day in History",
  feedback, ...) that runs on top of the SAME data files and SQLite database
  the Telegram bot uses, so progress made in the mini app and in the bot
  chat is one and the same.
* Keeps the Telegram bot itself alive in the same process:
  - on a host (``WEBHOOK_BASE_URL`` / ``RENDER_EXTERNAL_URL`` set):
    Telegram webhook delivery, and the mini app is registered as the bot's
    menu button automatically;
  - locally (no webhook URL): long polling in a background task;
  - ``MINIAPP_DISABLE_TELEGRAM=1``: web/API only — handy for UI development
    in a normal browser (no Telegram connection at all).

Run from the project root:  python miniapp/server.py
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
import random
import sys
import time
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import parse_qsl

from aiohttp import web

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import aiohttp  # noqa: E402
from aiogram import Bot  # noqa: E402
from aiogram.types import MenuButtonWebApp, WebAppInfo  # noqa: E402

import database as dbms  # noqa: E402
import handlers as museum  # noqa: E402
from bot import (  # noqa: E402
    KEEP_AWAKE_MINUTES,
    WEBHOOK_BASE_URL,
    WEBHOOK_PATH,
    WEBHOOK_SECRET,
    build_dispatcher,
)
from config import ADMIN_ID, BOT_TOKEN  # noqa: E402
from database import init_db  # noqa: E402

WEB_DIR = Path(__file__).resolve().parent / "web"
EXHIBIT_IMAGES_DIR = ROOT / "site" / "public" / "exhibits"
# With Telegram disabled the server only hosts the web app and the API.
TELEGRAM_DISABLED = os.getenv("MINIAPP_DISABLE_TELEGRAM", "").strip() == "1"

log = logging.getLogger("miniapp")

CONTINENT_ICONS = {"Europe": "🌍", "North America": "🌎", "Oceania": "🌏", "International": "🌐"}
FEEDBACK_LIMIT = 4000

# One active quiz round per user (the bot keeps the same state in FSM storage).
QUIZ_SESSIONS: dict[int, dict] = {}
QUIZ_SESSION_TTL = 6 * 60 * 60  # seconds

_bot: Bot | None = None


def get_bot() -> Bot | None:
    """The single Bot instance used for webhook delivery, polling and feedback."""
    global _bot
    if TELEGRAM_DISABLED:
        return None
    if _bot is None:
        _bot = Bot(token=BOT_TOKEN)
    return _bot


# ------------------------------------------------------------------ Telegram authorization
def verify_init_data(raw: str) -> dict | None:
    """Validate Telegram WebApp initData (HMAC-SHA256, see Telegram docs)."""
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
    # A day is generous: the mini app may stay open for a long session.
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
    """The real Telegram user from initData, or a demo user in local development."""
    raw = request.headers.get("X-Telegram-Init-Data", "")
    user = verify_init_data(raw) if raw else None
    if user:
        return user
    # Local mode only: a browser visitor gets a temporary demo identity,
    # chosen with ?uid=<number> if several people test at once.
    if not WEBHOOK_BASE_URL:
        try:
            uid = int(request.query.get("uid", "0")) or 900000001
        except ValueError:
            uid = 900000001
        return {"id": uid, "first_name": "Dev", "last_name": "User", "username": "dev_user"}
    raise web.HTTPUnauthorized(text="Telegram authorization failed")


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
        response = json_error(500, "Something went wrong. Please try again.")
    if request.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-store"
    return response


# ------------------------------------------------------------------ payloads
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
        "museum_name": museum.MUSEUM_NAME if hasattr(museum, "MUSEUM_NAME") else "World of Inventions",
        "user": {
            "id": user["id"],
            "name": " ".join(filter(None, [user.get("first_name"), user.get("last_name")])).strip()
            or "Explorer",
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
                when = "tomorrow" if ahead == 1 else f"in {ahead} days"
            else:
                when = "yesterday" if behind == 1 else f"{behind} days ago"
            events.append(_history_event(event, f"{when} · on {day_label}"))
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


# ------------------------------------------------------------------ API routes
async def api_bootstrap(request: web.Request) -> web.Response:
    user = resolve_user(request)
    favorites = await museum.db_call(dbms.get_favorites, user["id"], default=[])
    favorites = [i for i in favorites if i in museum.BY_ID]
    raw = await museum.db_call(dbms.get_stats, user["id"])
    if raw is None:
        raw = {
            "studied_exhibits": 0,
            "correct_answers": 0,
            "total_answers": 0,
            "quizzes_completed": 0,
        }
    return web.json_response(bootstrap_payload(user, favorites, raw))


async def api_progress_studied(request: web.Request) -> web.Response:
    user = resolve_user(request)
    body = await read_json(request)
    invention_id = str(body.get("id", ""))
    if invention_id not in museum.BY_ID:
        return json_error(404, "Exhibit not found.")
    await museum.db_call(dbms.mark_exhibit_studied, user["id"], invention_id)
    return web.json_response({"ok": True})


async def api_progress_hall(request: web.Request) -> web.Response:
    user = resolve_user(request)
    body = await read_json(request)
    hall_id = str(body.get("hall", ""))
    if hall_id not in museum.HALLS:
        return json_error(404, "Hall not found.")
    await museum.db_call(dbms.mark_hall_opened, user["id"], hall_id)
    return web.json_response({"ok": True})


async def api_favorite_toggle(request: web.Request) -> web.Response:
    user = resolve_user(request)
    invention_id = request.match_info["invention_id"]
    if invention_id not in museum.BY_ID:
        return json_error(404, "Exhibit not found.")
    saved = await museum.db_call(dbms.toggle_favorite, user["id"], invention_id)
    if saved is None:
        return json_error(500, "Favorites are not available right now.")
    return web.json_response({"saved": saved})


async def api_stats(request: web.Request) -> web.Response:
    user = resolve_user(request)
    raw = await museum.db_call(dbms.get_stats, user["id"])
    if raw is None:
        return json_error(500, "Statistics are not available right now.")
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
    QUIZ_SESSIONS[user["id"]] = {
        "order": order,
        "option_orders": option_orders,
        "index": 0,
        "score": 0,
        "ts": time.time(),
    }
    return web.json_response(quiz_question_payload(QUIZ_SESSIONS[user["id"]]))


async def api_quiz_answer(request: web.Request) -> web.Response:
    user = resolve_user(request)
    session = QUIZ_SESSIONS.get(user["id"])
    if session is None:
        return json_error(404, "No active quiz. Start a new round.")
    body = await read_json(request)
    try:
        choice = int(body.get("choice"))
    except (TypeError, ValueError):
        return json_error(400, "Invalid answer.")
    if session["index"] >= len(session["order"]):
        return json_error(404, "This round is already finished.")
    if not 0 <= choice < len(session["option_orders"][session["index"]]):
        return json_error(400, "Invalid answer.")
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
    return web.json_response(
        {
            "correct": correct,
            "correct_option": question["options"][question["answer"]],
            "fact": question["fact"],
            "score": session["score"],
            "answered": session["index"],
            "total": len(session["order"]),
            "finished": finished,
        }
    )


async def api_quiz_next(request: web.Request) -> web.Response:
    user = resolve_user(request)
    session = QUIZ_SESSIONS.get(user["id"])
    if session is None:
        return json_error(404, "No active quiz. Start a new round.")
    if session["index"] >= len(session["order"]):
        return json_error(404, "This round is already finished.")
    return web.json_response(quiz_question_payload(session))


async def api_feedback(request: web.Request) -> web.Response:
    user = resolve_user(request)
    body = await read_json(request)
    feedback = str(body.get("message", "")).strip()
    if not feedback:
        return json_error(400, "Your message seems to be empty.")
    feedback = feedback[:FEEDBACK_LIMIT]
    bot = get_bot()
    if bot is None:
        return json_error(503, "Telegram is disabled in this run, so feedback cannot be sent.")
    if not ADMIN_ID:
        log.warning(
            "Feedback received but ADMIN_ID is not configured. User ID: %s; message: %s",
            user["id"],
            feedback,
        )
        return json_error(503, "The feedback inbox has not been configured yet.")
    username = f"@{user['username']}" if user.get("username") else "No username"
    report = (
        "📩 New museum feedback (mini app)\n\n"
        f"From: {user.get('first_name', '')} {user.get('last_name', '')}".strip() + "\n"
        f"Username: {username}\n"
        f"Telegram ID: {user['id']}\n\n"
        f"Message:\n{feedback}"
    )
    try:
        await bot.send_message(ADMIN_ID, report)
    except Exception as exc:
        log.warning("Could not deliver feedback from %s: %s", user["id"], exc)
        return json_error(502, "Sorry, the message could not be delivered right now.")
    return web.json_response({"ok": True})


async def api_map_send(request: web.Request) -> web.Response:
    """Sends the bot's map screen to the visitor's chat. Its first button opens the
    separate interactive map mini app (WEBAPP_URL, site/miniapp.html)."""
    user = resolve_user(request)
    bot = get_bot()
    if bot is None:
        return json_error(503, "Telegram is disabled in this run, so the map cannot be sent.")
    if not museum.WEBAPP_URL:
        return json_error(503, "The interactive map is turned off on this server.")
    from keyboards import countries_keyboard
    try:
        await bot.send_message(
            user["id"],
            museum.build_map_text(),
            reply_markup=countries_keyboard(museum.COUNTRIES, museum.COUNTRY_LABELS, webapp_url=museum.WEBAPP_URL),
        )
    except Exception as exc:
        log.warning("Could not send the map to %s: %s", user["id"], exc)
        return json_error(502, "The bot could not write to you. Open the chat with the bot once and try again.")
    return web.json_response({"ok": True})


async def health(_request: web.Request) -> web.Response:
    mode = "disabled" if TELEGRAM_DISABLED else ("webhook" if WEBHOOK_BASE_URL else "polling")
    version = os.getenv("RENDER_GIT_COMMIT", "local")[:7]
    return web.Response(text=f"World of Inventions mini app is running. Telegram: {mode}. Version {version}.")


async def index(_request: web.Request) -> web.Response:
    response = web.FileResponse(WEB_DIR / "index.html")
    response.headers["Cache-Control"] = "no-cache"
    return response


# ------------------------------------------------------------------ Telegram (webhook / polling)
async def set_museum_menu_button(bot: Bot) -> None:
    """The menu button opens this full mini app. The map mini app (WEBAPP_URL,
    site/miniapp.html) keeps its own place: the bot's map screen has the
    'Open Interactive Map' inline button for it. bot.build_dispatcher() also
    registers a menu-button hook; whichever runs last wins, so this one is
    always registered (polling) or called (webhook) after the bot's."""
    url = WEBHOOK_BASE_URL
    if not url.startswith("https://"):
        # Telegram only accepts https addresses; local http runs keep the
        # button the bot set (or none) and the app stays reachable in a browser.
        log.info("Menu button left as is (the mini app URL is not public https).")
        return
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="🏛 Museum", web_app=WebAppInfo(url=url))
        )
        log.info("The mini app is now the bot's menu button: %s", url)
    except Exception as exc:
        log.warning("Could not set the menu button: %s", exc)


async def keep_awake() -> None:
    """Ping this service regularly so a free host does not fall asleep."""
    await asyncio.sleep(60)
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        while True:
            try:
                async with session.get(f"{WEBHOOK_BASE_URL}/healthz") as response:
                    log.info("keep-awake ping: HTTP %s", response.status)
            except Exception as exc:
                log.warning("keep-awake ping failed: %s", exc)
            await asyncio.sleep(KEEP_AWAKE_MINUTES * 60)


async def on_startup(app: web.Application) -> None:
    bot = get_bot()
    if bot is None:
        log.info("MINIAPP_DISABLE_TELEGRAM=1 — running web/API only, without Telegram.")
        return
    if WEBHOOK_BASE_URL:
        await bot.set_webhook(
            f"{WEBHOOK_BASE_URL}{WEBHOOK_PATH}",
            secret_token=WEBHOOK_SECRET,
            drop_pending_updates=False,
        )
        await set_museum_menu_button(bot)
        from branding import EN_AVATAR, EN_NAME, apply_branding
        await apply_branding(
            bot, EN_NAME,
            "Inventions that changed the world, from telescopes to the web. Sister museum in Russian: @lshpdigitalmuseumbot",
            EN_AVATAR,
        )
        if KEEP_AWAKE_MINUTES > 0:
            app["keep_awake_task"] = asyncio.create_task(keep_awake())
        log.info("Webhook mode: %s%s", WEBHOOK_BASE_URL, WEBHOOK_PATH)
    else:
        dispatcher = build_dispatcher()
        # bot.build_dispatcher() registers its own menu-button hook (the map mini
        # app); registered after it, ours runs last and the full app wins.
        dispatcher.startup.register(set_museum_menu_button)
        try:
            await bot.delete_webhook(drop_pending_updates=False)
        except Exception as exc:
            log.warning("Could not delete the webhook: %s", exc)
        # The bot keeps working in the chat while the mini app server runs.
        app["polling_task"] = asyncio.create_task(dispatcher.start_polling(bot))
        log.info("Polling mode: the bot answers in the chat and the API serves the mini app.")


async def on_cleanup(app: web.Application) -> None:
    for key in ("keep_awake_task", "polling_task"):
        task = app.get(key)
        if task:
            task.cancel()
    if _bot is not None:
        try:
            await _bot.session.close()
        except Exception:
            pass


def mount_russian_museum(app: web.Application) -> None:
    try:
        from ru import server as ru_server
    except Exception:
        log.exception("The Russian museum (ru/) could not be loaded; World of Inventions keeps running.")
        return
    if not (ru_server.enabled() or TELEGRAM_DISABLED):
        log.info("RU_BOT_TOKEN is not set: the Russian museum is not mounted.")
        return
    ru_server.mount(app, WEBHOOK_BASE_URL, TELEGRAM_DISABLED)
    log.info("The Russian museum is mounted under /ru/.")


def build_app() -> web.Application:
    app = web.Application(middlewares=[api_middleware])
    app.router.add_get("/healthz", health)

    if WEBHOOK_BASE_URL and not TELEGRAM_DISABLED:
        from aiogram.webhook.aiohttp_server import SimpleRequestHandler

        SimpleRequestHandler(
            dispatcher=build_dispatcher(),
            bot=get_bot(),
            secret_token=WEBHOOK_SECRET,
        ).register(app, path=WEBHOOK_PATH)

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
    app.router.add_post("/api/map/send", api_map_send)

    # The Russian-language museum of the same ecosystem (@lshpdigitalmuseumbot):
    # its mini app, API and webhook live under /ru/. It is mounted before the
    # catch-all static route below, and only when RU_BOT_TOKEN is set or the
    # server runs without Telegram (local UI development).
    mount_russian_museum(app)

    app.router.add_get("/", index)
    app.router.add_static("/exhibits/", EXHIBIT_IMAGES_DIR, name="exhibit-images")
    app.router.add_static("/", WEB_DIR, name="web")
    return app


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    init_db()
    app = build_app()
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    port = int(os.getenv("PORT", "10000"))
    mode = "disabled" if TELEGRAM_DISABLED else ("webhook" if WEBHOOK_BASE_URL else "polling")
    log.info("Serving the mini app on http://0.0.0.0:%s (web: %s, telegram: %s)", port, WEB_DIR, mode)
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
