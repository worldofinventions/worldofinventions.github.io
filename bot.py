import asyncio
import hashlib
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from aiogram.types import MenuButtonDefault, MenuButtonWebApp, WebAppInfo

from config import BOT_TOKEN, WEBAPP_URL
from database import init_db
from handlers import router

# On a host such as Render the bot runs as a web service and Telegram delivers
# updates to it (webhook). Render sets RENDER_EXTERNAL_URL by itself; elsewhere
# set WEBHOOK_BASE_URL. Without either, the bot polls Telegram (local run).
WEBHOOK_BASE_URL = (os.getenv("WEBHOOK_BASE_URL") or os.getenv("RENDER_EXTERNAL_URL") or "").rstrip("/")
WEBHOOK_PATH = "/telegram-webhook"
# Telegram sends this secret with every update, so strangers cannot post fake ones.
# Telegram allows only A-Z, a-z, 0-9, _ and - here; by default it is derived from the token.
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "").strip() or hashlib.sha256(BOT_TOKEN.encode()).hexdigest()[:48]
PORT = int(os.getenv("PORT", "10000"))
# A free Render service falls asleep after 15 minutes without incoming requests.
# The bot calls its own public address every few minutes so it stays awake 24/7
# (one service running all month fits Render's 750 free hours). 0 turns it off.
KEEP_AWAKE_MINUTES = float(os.getenv("KEEP_AWAKE_MINUTES", "10"))


async def setup_menu_button(bot: Bot):
    """The button next to the message field: the interactive map, or Telegram's usual
    command menu when the Mini App is turned off (WEBAPP_URL=off)."""
    try:
        if WEBAPP_URL:
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(text="🗺 Map", web_app=WebAppInfo(url=WEBAPP_URL))
            )
        else:
            await bot.set_chat_menu_button(menu_button=MenuButtonDefault())
    except Exception as exc:
        # The bot works without it; only the shortcut is missing.
        logging.warning("Could not set the menu button: %s", exc)


def build_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(router)
    dispatcher.startup.register(setup_menu_button)
    return dispatcher


async def run_polling():
    bot = Bot(token=BOT_TOKEN)
    dispatcher = build_dispatcher()
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        print("World of Inventions is running (polling)!")
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    if WEBHOOK_BASE_URL:
        # On a host the full Mini App server takes over: it serves the bot's webhook,
        # the Mini App and its API, the Russian museum under /ru/ and keep-awake.
        from miniapp.server import main as serve_miniapp
        serve_miniapp()
    else:
        asyncio.run(run_polling())


if __name__ == "__main__":
    main()
