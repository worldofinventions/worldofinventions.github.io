import os

from dotenv import load_dotenv

load_dotenv()

# Токен бота @lshpdigitalmuseumbot. Без него русский музей просто не запускается,
# а основной бот World of Inventions работает как раньше.
BOT_TOKEN = os.getenv("RU_BOT_TOKEN", "").strip()
# Отзывы приходят тому же администратору, что и у основного бота.
ADMIN_ID_RAW = (os.getenv("RU_ADMIN_ID") or os.getenv("ADMIN_ID") or "").strip()
ADMIN_ID = int(ADMIN_ID_RAW) if ADMIN_ID_RAW.isdigit() else None
MUSEUM_NAME = "Музей изобретений русских людей"

# Экосистема: соседний англоязычный музей и сайты обоих музеев.
WORLD_BOT_URL = os.getenv("WORLD_BOT_URL", "https://t.me/worldofinventions_app").strip()
SITE_URL = os.getenv("RU_SITE_URL", "https://worldofinventions.github.io/ru/").strip()
