import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID_RAW = os.getenv("ADMIN_ID", "").strip()
ADMIN_ID = int(ADMIN_ID_RAW) if ADMIN_ID_RAW.isdigit() else None
MUSEUM_NAME = "World of Inventions"

# The interactive map, opened inside Telegram as a Mini App (site/miniapp.html).
# Set WEBAPP_URL=off to run the bot exactly as before, with only the text map.
_WEBAPP_RAW = os.getenv("WEBAPP_URL", "https://worldofinventions.github.io/miniapp.html").strip()
WEBAPP_URL = None if _WEBAPP_RAW.lower() in {"", "off", "no", "false", "0"} else _WEBAPP_RAW

# The sister bot of the ecosystem: the Russian-language museum (ru/ package).
RU_BOT_URL = os.getenv("RU_BOT_URL", "https://t.me/lshpdigitalmuseumbot").strip()

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing. Add your bot token to the .env file.")
