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

# Интерактивная карта (ru/site/miniapp.html на GitHub Pages) как Telegram Mini App.
# RU_WEBAPP_URL=off — бот работает только с текстовой картой.
# Отдельной страницы с картой на русском сайте нет: карта открывается в Mini App музея.
_WEBAPP_RAW = os.getenv("RU_WEBAPP_URL", "off").strip()
WEBAPP_URL = None if _WEBAPP_RAW.lower() in {"", "off", "no", "false", "0"} else _WEBAPP_RAW

# Экосистема: соседний англоязычный музей и сайты обоих музеев.
WORLD_BOT_URL = os.getenv("WORLD_BOT_URL", "https://t.me/jdjsbehenbot").strip()
SITE_URL = os.getenv("RU_SITE_URL", "https://worldofinventions.github.io/ru/").strip()
