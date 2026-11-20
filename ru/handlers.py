import asyncio
import json
import random
import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path

import aiohttp
from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, BufferedInputFile, FSInputFile, InputMediaPhoto

from .config import MUSEUM_NAME, ADMIN_ID, SITE_URL
from .database import (
    toggle_favorite, get_favorites, is_favorite, mark_exhibit_studied,
    mark_hall_opened, record_answer, record_quiz_completed, get_stats,
)
from .keyboards import (
    main_keyboard, museum_keyboard, halls_keyboard, items_keyboard,
    navigation_keyboard, back_keyboard, quiz_answer_keyboard,
    quiz_result_keyboard, quiz_result_keyboard_continue, favorites_keyboard,
    how_keyboard, info_keyboard, results_keyboard,
    history_keyboard, filters_keyboard, hall_filter_keyboard,
    period_filter_keyboard, hall_items_keyboard, relabel_favorite, team_keyboard,
    ITEMS_PER_PAGE,
)

router = Router(name="ru-museum")
DATA_FILE = Path(__file__).resolve().parent / "data" / "inventions.json"
HISTORY_FILE = Path(__file__).resolve().parent / "data" / "history.json"
# Фото экспонатов лежат в проекте (сайт отдаёт те же файлы),
# поэтому бот не зависит от того, жива ли чужая ссылка на картинку.
IMAGE_DIR = Path(__file__).resolve().parent / "site" / "public" / "exhibits"

HALLS = {
    "1": {"title": "V–X века", "name": "Истоки письменности и культуры",
          "description": "Славянская азбука, первые книги и то, как жили и путешествовали на Руси до XI века."},
    "2": {"title": "XI–XV века", "name": "Средневековые технологии",
          "description": "Книжное дело, письма на бересте, музыка и первые пушки средневековой Руси."},
    "3": {"title": "XVI–XIX века", "name": "Научный и промышленный прорыв",
          "description": "Книгопечатание, станки, паровые машины, электричество и первые шаги радио."},
    "4": {"title": "XX–XXI века", "name": "Изобретения, изменившие мир",
          "description": "Авиация, телевидение, атомная энергия, космос, компьютерные игры и новые материалы."},
}

# Банк вопросов. В каждом раунде случайно выбираются 10 вопросов, варианты перемешиваются.
QUIZ_ROUND_SIZE = 10
QUIZ = [
    {"question": "Кто создал первую славянскую азбуку, глаголицу?", "options": ["Константин (Кирилл) Философ", "Иван Фёдоров", "Нестор-летописец", "Ярослав Мудрый"], "answer": 0, "fact": "Константин создал азбуку около 863 года для миссии в Великую Моравию вместе с братом Мефодием."},
    {"question": "Где сложилась кириллица?", "options": ["В Первом Болгарском царстве", "В Великом Новгороде", "В Константинополе", "В Киеве"], "answer": 0, "fact": "Кириллицу создали книжники Преславской школы в Болгарии в конце IX — начале X века."},
    {"question": "Каким годом датирован самый нижний ярус мостовых Великой улицы в Новгороде?", "options": ["953", "1147", "1240", "1564"], "answer": 0, "fact": "Год узнали по годовым кольцам брёвен. Всего на Неревском раскопе открыли 28 ярусов мостовой."},
    {"question": "Чем писали на берестяных грамотах?", "options": ["Процарапывали острым писалом", "Гусиным пером и чернилами", "Углём", "Кисточкой и краской"], "answer": 0, "fact": "Писало — стержень из кости или металла с острым концом. Чернила для бересты не требовались."},
    {"question": "В каком городе в 1951 году нашли первую берестяную грамоту?", "options": ["В Великом Новгороде", "В Москве", "В Пскове", "В Суздале"], "answer": 0, "fact": "Её нашли 26 июля 1951 года в экспедиции Артемия Арциховского."},
    {"question": "Как звали новгородского мальчика XIII века, оставившего рисунки на бересте?", "options": ["Онфим", "Садко", "Словиша", "Остромир"], "answer": 0, "fact": "Онфим нарисовал себя всадником и записывал на бересте азбуку и учебные слоги."},
    {"question": "Какая книга — самая древняя из точно датированных древнерусских книг?", "options": ["Остромирово Евангелие", "«Апостол» 1564 года", "«Слово о полку Игореве»", "«Азбука» Фёдорова"], "answer": 0, "fact": "Её переписал дьякон Григорий в 1056–1057 годах для посадника Остромира."},
    {"question": "При обороне от какого хана летопись впервые упоминает пушки в Москве?", "options": ["Тохтамыша", "Батыя", "Мамая", "Ахмата"], "answer": 0, "fact": "Это было в 1382 году. Орудия на стенах назывались «тюфяки» и «пушки»."},
    {"question": "Кто вместе с Петром Мстиславцем напечатал «Апостол» 1564 года?", "options": ["Иван Фёдоров", "Андрей Чохов", "Андрей Нартов", "Михаил Ломоносов"], "answer": 0, "fact": "«Апостол» — первая точно датированная печатная книга в России."},
    {"question": "Кто отлил Царь-пушку?", "options": ["Андрей Чохов", "Иван Ползунов", "Иван Кулибин", "Ефим Черепанов"], "answer": 0, "fact": "Царь-пушку отлили в 1586 году на московском Пушечном дворе. Её калибр — 890 миллиметров."},
    {"question": "Сколько косточек на одном прутке русских счётов?", "options": ["Десять", "Пять", "Семь", "Двенадцать"], "answer": 0, "fact": "Каждый пруток — один десятичный разряд, поэтому косточек ровно десять."},
    {"question": "Какую деталь станка Андрей Нартов сделал механической задолго до англичан?", "options": ["Суппорт, держащий резец", "Шестерёнку", "Педаль", "Ремень"], "answer": 0, "fact": "Механический суппорт ровно двигал резец винтом, и деталь получалась точнее, чем рукой."},
    {"question": "Для чего Ломоносов создал «ночезрительную трубу»?", "options": ["Чтобы видеть предметы в сумерках", "Чтобы измерять температуру", "Чтобы предсказывать погоду", "Чтобы зажигать огонь"], "answer": 0, "fact": "Большой объектив собирал больше света, и в сумерках картинка была ярче."},
    {"question": "Что Ломоносов открыл у Венеры в 1761 году?", "options": ["Атмосферу", "Спутник", "Кольца", "Вулканы"], "answer": 0, "fact": "Он наблюдал прохождение Венеры по диску Солнца и заметил светлый ободок вокруг планеты."},
    {"question": "В каком городе Иван Ползунов построил свою паровую машину?", "options": ["В Барнауле", "В Туле", "В Нижнем Тагиле", "В Петербурге"], "answer": 0, "fact": "Машина приводила в действие мехи плавильных печей Барнаульского завода."},
    {"question": "Какой мост через Неву придумал Иван Кулибин?", "options": ["Деревянный, из одной арки", "Разводной железный", "Подвесной на цепях", "Понтонный на лодках"], "answer": 0, "fact": "Модель в 1/10 величины выдержала нагрузку больше 50 тонн, но мост так и не построили."},
    {"question": "Кто построил первый паровоз в России?", "options": ["Ефим и Мирон Черепановы", "Братья Райт", "Иван Ползунов", "Павел Шиллинг"], "answer": 0, "fact": "Паровоз Черепановых 1834 года ходил по чугунной колее Выйского завода в Нижнем Тагиле."},
    {"question": "Что изобрёл Павел Шиллинг в 1832 году?", "options": ["Электромагнитный телеграф", "Телефон", "Электрическую лампу", "Фотоаппарат"], "answer": 0, "fact": "Он показал телеграф в Петербурге за несколько лет до телеграфа Морзе."},
    {"question": "Какие скульптуры сделаны методом гальванопластики Якоби?", "options": ["Скульптуры Исаакиевского собора", "Медный всадник", "Кони Клодта", "Царь-колокол"], "answer": 0, "fact": "Гальванопластика позволяет осадить медь на форму с помощью электрического тока."},
    {"question": "Какую повязку Николай Пирогов применял при переломах?", "options": ["Гипсовую", "Пластиковую", "Резиновую", "Деревянную шину"], "answer": 0, "fact": "Он широко применял гипс во время Крымской войны, и это спасло тысячи раненых."},
    {"question": "Какой элемент НЕ входил в число предсказанных Менделеевым?", "options": ["Кислород", "Галлий", "Скандий", "Германий"], "answer": 0, "fact": "Кислород открыли ещё в XVIII веке, а галлий, скандий и германий нашли после 1869 года, как и предсказал Менделеев."},
    {"question": "Как в Париже называли свет свечей Яблочкова?", "options": ["«Русский свет»", "«Северное сияние»", "«Свет звезды»", "«Электрический огонь»"], "answer": 0, "fact": "В 1878 году свечами Яблочкова осветили парижскую авеню Оперы."},
    {"question": "Из чего Лодыгин позже предложил делать нити ламп накаливания?", "options": ["Из вольфрама и молибдена", "Из меди", "Из серебра", "Из алюминия"], "answer": 0, "fact": "Вольфрамовые нити используют в лампах накаливания до сих пор."},
    {"question": "Как Николай Бенардос назвал свой способ дуговой сварки?", "options": ["«Электрогефест»", "«Электрофор»", "«Молния»", "«Искра»"], "answer": 0, "fact": "Гефест — древнегреческий бог кузнечного дела."},
    {"question": "Как называют ротор асинхронного двигателя Доливо-Добровольского?", "options": ["«Беличья клетка»", "«Ласточкин хвост»", "«Чёртово колесо»", "«Птичье гнездо»"], "answer": 0, "fact": "В роторе нет щёток и скользящих контактов, поэтому двигатель простой и надёжный."},
    {"question": "Какой праздник отмечают в России 7 мая?", "options": ["День радио", "День космонавтики", "День науки", "День изобретателя"], "answer": 0, "fact": "7 мая 1895 года Александр Попов показал свой прибор для приёма электромагнитных волн."},
    {"question": "Для какой выставки Шухов построил первую гиперболоидную башню?", "options": ["Нижегородской 1896 года", "Парижской 1889 года", "Московской 1872 года", "Лондонской 1851 года"], "answer": 0, "fact": "После выставки башню перевезли в усадьбу Полибино, где она стоит до сих пор."},
    {"question": "Как Прокудин-Горский получал цветные фотографии?", "options": ["Три снимка через красный, зелёный и синий фильтры", "Раскрашивал снимки красками", "Снимал на цветную плёнку", "Печатал цветными чернилами"], "answer": 0, "fact": "Его коллекция хранится в Библиотеке Конгресса США и открыта для всех."},
    {"question": "Чем был знаменит самолёт «Русский витязь» 1913 года?", "options": ["Это первый в мире четырёхмоторный самолёт", "Это первый реактивный самолёт", "Он облетел Землю", "Он взлетал с воды"], "answer": 0, "fact": "Самолёт построил Игорь Сикорский на Русско-Балтийском вагонном заводе."},
    {"question": "Что изобрёл Глеб Котельников?", "options": ["Ранцевый парашют", "Вертолёт", "Воздушный шар", "Дельтаплан"], "answer": 0, "fact": "Свой парашют РК-1 он проверил, раскрыв его у мчащегося автомобиля."},
    {"question": "Как играют на терменвоксе?", "options": ["Двигают руками возле антенн, не касаясь", "Дуют в трубку", "Щиплют струны", "Нажимают клавиши"], "answer": 0, "fact": "Одна рука меняет высоту звука, другая — громкость."},
    {"question": "Какое изобретение Владимира Зворыкина стало основой электронного телевидения?", "options": ["Иконоскоп", "Транзистор", "Магнитофон", "Лазер"], "answer": 0, "fact": "Зворыкин работал в США, в лаборатории компании RCA."},
    {"question": "Какую схему вертолёта предложил Сикорский в VS-300?", "options": ["Один несущий винт и хвостовой винт", "Два винта друг над другом", "Четыре винта по углам", "Крылья и пропеллер"], "answer": 0, "fact": "Эту схему используют большинство вертолётов в мире."},
    {"question": "В каком городе в 1954 году заработала первая в мире АЭС?", "options": ["В Обнинске", "В Курчатове", "В Дубне", "В Сарове"], "answer": 0, "fact": "Её мощность была 5 мегаватт, а теперь в здании станции музей."},
    {"question": "Кто руководил созданием Спутника-1 и корабля «Восток»?", "options": ["Сергей Королёв", "Константин Циолковский", "Игорь Курчатов", "Андрей Туполев"], "answer": 0, "fact": "ОКБ-1 Королёва построило и спутник, и корабль, на котором полетел Гагарин."},
    {"question": "Сколько минут длился полёт Юрия Гагарина?", "options": ["108", "45", "90", "180"], "answer": 0, "fact": "12 апреля 1961 года «Восток» облетел Землю один раз."},
    {"question": "Где сейчас стоит атомный ледокол «Ленин»?", "options": ["В Мурманске, это музей", "Во Владивостоке", "В Архангельске", "Его разобрали"], "answer": 0, "fact": "Это первое в мире надводное судно с атомной энергетической установкой."},
    {"question": "Как расшифровывается слово «токамак»?", "options": ["Тороидальная камера с магнитными катушками", "Термоядерная камера максимальной мощности", "Точный канал магнитного контроля", "Ток, камера, магнит, кольцо"], "answer": 0, "fact": "Плазму в токамаке удерживает магнитное поле, чтобы она не касалась стенок."},
    {"question": "Сколько колёс было у «Лунохода-1»?", "options": ["Восемь", "Четыре", "Шесть", "Три"], "answer": 0, "fact": "Им управляли с Земли, и он проехал по Луне около 10,5 километра."},
    {"question": "На каком компьютере появился Тетрис?", "options": ["«Электроника-60»", "ZX Spectrum", "IBM PC", "«Агат»"], "answer": 0, "fact": "Алексей Пажитнов закончил первую версию 6 июня 1984 года."},
    {"question": "Какой рекорд установил космонавт Валерий Поляков на станции «Мир»?", "options": ["437 суток в одном полёте", "Первый выход в открытый космос", "Первая посадка на Луну", "Самый быстрый полёт"], "answer": 0, "fact": "Станция «Мир» проработала на орбите 15 лет, с 1986 по 2001 год."},
    {"question": "Чем Гейм и Новосёлов впервые отделили графен от графита?", "options": ["Липкой лентой", "Лазером", "Ножом", "Кислотой"], "answer": 0, "fact": "За опыты с графеном они получили Нобелевскую премию по физике 2010 года."},
]


# Страны изобретений: (флаг, часть света).
COUNTRY_INFO = {
    "Россия": ("🇷🇺", "Евразия"),
    "Казахстан": ("🇰🇿", "Евразия"),
    "Украина": ("🇺🇦", "Евразия"),
    "Болгария": ("🇧🇬", "Евразия"),
    "Чехия": ("🇨🇿", "Евразия"),
    "Германия": ("🇩🇪", "Евразия"),
    "Франция": ("🇫🇷", "Евразия"),
    "Великобритания": ("🇬🇧", "Евразия"),
    "США": ("🇺🇸", "Северная Америка"),
}
PERIOD_ORDER = ["IX век", "X век", "XI век", "XI–XV века", "XIV век", "XVI век", "XVIII век", "XIX век", "XX век", "XXI век"]
MONTH_NAMES = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля",
               "августа", "сентября", "октября", "ноября", "декабря"]
HISTORY_KIND_ICONS = {"invention": "💡", "discovery": "🔬", "milestone": "🚀"}


class SearchState(StatesGroup):
    waiting_for_query = State()


class FeedbackState(StatesGroup):
    waiting_for_message = State()


def load_inventions():
    with DATA_FILE.open("r", encoding="utf-8") as file:
        items = json.load(file)

    required = {"id", "name", "hall", "period", "year", "inventor", "country",
                "origin", "features", "significance", "further_facts", "sources",
                "how_it_works", "map_countries"}
    ids = []
    for item in items:
        missing = required - item.keys()
        if missing:
            raise ValueError(f"Invention {item.get('id', '?')} is missing fields: {sorted(missing)}")
        if str(item["hall"]) not in HALLS:
            raise ValueError(f"Invention {item['id']} has an invalid hall: {item['hall']}")
        unknown = [c for c in item["map_countries"] if c not in COUNTRY_INFO]
        if unknown or not item["map_countries"]:
            raise ValueError(f"Invention {item['id']} has invalid map_countries: {item['map_countries']}")
        ids.append(item["id"])
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate invention IDs found in ru/data/inventions.json")
    return items


INVENTIONS = load_inventions()
BY_ID = {item["id"]: item for item in INVENTIONS}


IMAGE_REQUEST_HEADERS = {"User-Agent": "RussianInventionsMuseumBot/1.0 (educational project)"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # лимит Telegram для фото


CAPTION_LIMIT = 1024  # лимит Telegram для подписи к фото

# file_id каждого уже загруженного фото: следующие карточки берут его мгновенно.
PHOTO_FILE_IDS: dict[str, str] = {}


def local_photo(item):
    path = IMAGE_DIR / f"{item['id']}.jpg"
    return FSInputFile(path, filename=path.name) if path.is_file() else None


def remember_photo(item, sent):
    photo = getattr(sent, "photo", None)
    if photo:
        PHOTO_FILE_IDS[item["id"]] = photo[-1].file_id


def load_history():
    with HISTORY_FILE.open("r", encoding="utf-8") as file:
        events = json.load(file)
    required = {"month", "day", "year", "kind", "title", "text"}
    for event in events:
        missing = required - event.keys()
        if missing:
            raise ValueError(f"History event {event.get('title', '?')} is missing fields: {sorted(missing)}")
        date(2001, event["month"], event["day"])  # ValueError для невозможных дат
        related = event.get("related_id")
        if related is not None and related not in BY_ID:
            raise ValueError(f"History event {event['title']} refers to an unknown exhibit: {related}")
    return events


HISTORY = load_history()

# Страны изобретений, сначала те, где их больше.
_country_counts = Counter(c for item in INVENTIONS for c in item["map_countries"])
COUNTRIES = [c for c, _ in sorted(_country_counts.items(), key=lambda pair: (-pair[1], pair[0]))]
COUNTRY_LABELS = {c: f"{COUNTRY_INFO[c][0]} {c}" for c in COUNTRIES}
PERIODS = sorted(
    {item["period"] for item in INVENTIONS},
    key=lambda p: PERIOD_ORDER.index(p) if p in PERIOD_ORDER else len(PERIOD_ORDER),
)


# --------------------------------------------------------------------------- helpers
def utf16_length(text: str) -> int:
    """Telegram считает длину подписи в единицах UTF-16 (эмодзи — за две)."""
    return len(text.encode("utf-16-le")) // 2


async def db_call(func, *args, default=None):
    """Выполняет (блокирующую) функцию базы данных, не замораживая бота.
    Ошибка базы пишется в лог и никогда не ломает сам музей."""
    try:
        return await asyncio.to_thread(func, *args)
    except Exception as exc:
        print(f"Database error in {func.__name__}: {exc}")
        return default


def is_not_modified(exc: Exception) -> bool:
    return "message is not modified" in str(exc)


def message_has_button(message: Message, callback_data: str) -> bool:
    markup = message.reply_markup
    if not markup:
        return False
    return any(b.callback_data == callback_data for row in markup.inline_keyboard for b in row)


def message_has_button_prefix(message: Message, prefix: str) -> bool:
    markup = message.reply_markup
    if not markup:
        return False
    return any(
        (b.callback_data or "").startswith(prefix)
        for row in markup.inline_keyboard for b in row
    )


async def safe_delete(message: Message):
    try:
        await message.delete()
    except Exception as exc:
        print(f"Could not delete the previous message: {exc}")


async def download_image(item):
    """Скачивает картинку экспоната сами (с нормальным User-Agent), чтобы загрузить её в Telegram."""
    url = item.get("image_url")
    if not url:
        return None
    try:
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(headers=IMAGE_REQUEST_HEADERS, timeout=timeout) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                if not response.headers.get("Content-Type", "").startswith("image/"):
                    raise ValueError("the URL did not return an image")
                data = await response.content.read(MAX_IMAGE_BYTES + 1)
        if len(data) > MAX_IMAGE_BYTES:
            raise ValueError("the image is larger than 5 MB")
        return BufferedInputFile(data, filename=f"{item['id']}.jpg")
    except Exception as exc:
        print(f"Could not download the exhibit image for {item['id']}: {exc}")
        return None


async def show_text(message: Message, text: str, reply_markup=None, **kwargs):
    """Показывает текстовый экран вместо текущего сообщения бота.
    Текст редактируется на месте; фото нельзя превратить в текст, поэтому
    отправляется новое сообщение, а старое с фото удаляется."""
    if message.photo:
        await message.answer(text, reply_markup=reply_markup, **kwargs)
        await safe_delete(message)
        return
    try:
        await message.edit_text(text, reply_markup=reply_markup, **kwargs)
    except TelegramBadRequest as exc:
        if not is_not_modified(exc):
            raise


async def show_card_text(message: Message, text: str, reply_markup):
    """Заменяет текст карточки экспоната (например, на «Как это работает»).
    Фото остаётся на месте; без фото это обычный текстовый экран."""
    if message.photo:
        if utf16_length(text) <= CAPTION_LIMIT:
            try:
                await message.edit_caption(caption=text, reply_markup=reply_markup)
                return
            except TelegramBadRequest as exc:
                if is_not_modified(exc):
                    return
                print(f"Could not edit the caption: {exc}")
            except Exception as exc:
                print(f"Could not edit the caption: {exc}")
    await show_text(message, text, reply_markup=reply_markup, disable_web_page_preview=True)


async def show_item_card(message: Message, item, text: str, reply_markup, reuse_photo: bool = False):
    """Показывает экспонат ОДНИМ сообщением: фото и текст экспоната в подписи.
    Если текущее сообщение уже с фото, карточка редактируется на месте, иначе
    заменяет его. Без картинки (или если текст не влезает в подпись) — просто текст."""
    has_photo = bool(PHOTO_FILE_IDS.get(item["id"]) or local_photo(item) or item.get("image_url"))
    url = has_photo or None
    caption_length = utf16_length(text)
    if url and caption_length > CAPTION_LIMIT:
        print(f"Exhibit {item['id']}: text is {caption_length} characters; a caption allows {CAPTION_LIMIT}. Showing text only.")
        url = None
    if url and reuse_photo and message.photo:
        # Возврат с экрана «Как это работает»: фото уже то, что нужно.
        try:
            await message.edit_caption(caption=text, reply_markup=reply_markup)
            return
        except TelegramBadRequest as exc:
            if is_not_modified(exc):
                return
            print(f"Could not restore the caption for {item['id']}: {exc}")
        except Exception as exc:
            print(f"Could not restore the caption for {item['id']}: {exc}")
    if url:
        # Порядок: file_id из Telegram, фото из проекта, затем удалённая image_url
        # (сначала её забирает Telegram, потом скачивает сам бот).
        for attempt in ("file_id", "local", "url", "download"):
            if attempt == "file_id":
                media = PHOTO_FILE_IDS.get(item["id"])
            elif attempt == "local":
                media = local_photo(item)
            elif attempt == "url":
                media = item.get("image_url")
            else:
                media = await download_image(item) if item.get("image_url") else None
            if media is None:
                continue
            try:
                if message.photo:
                    sent = await message.edit_media(
                        InputMediaPhoto(media=media, caption=text), reply_markup=reply_markup
                    )
                else:
                    sent = await message.answer_photo(photo=media, caption=text, reply_markup=reply_markup)
                    await safe_delete(message)
                remember_photo(item, sent)
                return
            except TelegramBadRequest as exc:
                if is_not_modified(exc):
                    return
                print(f"Could not show the image for {item['id']} ({attempt}): {exc}")
            except Exception as exc:
                print(f"Could not show the image for {item['id']} ({attempt}): {exc}")
    await show_text(message, text, reply_markup=reply_markup, disable_web_page_preview=True)


# Поиск не различает «е» и «ё»: «Королев» найдёт «Королёв».
SPELLING_VARIANTS = {
    "ё": "е",
}


def normalize_text(text: str) -> str:
    """Переводит текст в нижний регистр и заменяет «ё» на «е»."""
    return re.sub(r"[ё]", lambda m: SPELLING_VARIANTS.get(m.group(0), m.group(0)), text.casefold())


def format_invention(item):
    text = (
        f"🏺 {item['name']}\n\n"
        f"📅 Период: {item['period']}\n"
        f"Год: {item['year']}\n"
        f"👤 Изобретатель: {item['inventor']}\n"
        f"🌍 Где: {item['country']}\n\n"
        f"📜 Происхождение\n{item['origin']}\n\n"
        f"⚙️ Особенности\n{item['features']}\n\n"
        f"🌐 Значение\n{item['significance']}\n\n"
        f"💡 Интересный факт\n{item['further_facts']}"
    )
    sources = item.get("sources", [])
    if sources:
        text += "\n\n📚 Источники"
        for source in sources:
            text += f"\n• {source['title']}: {source['url']}"
    return text


def main_menu_text():
    return (
        f"Добро пожаловать в «{MUSEUM_NAME}»! 🏛\n\n"
        "Здесь собраны изобретения и открытия, связанные с историей России: "
        "от славянской азбуки до спутника и графена. Узнайте, кто их придумал, "
        "как они работают, и проверьте себя в викторине.\n\n"
        "Выберите раздел:"
    )


# ------------------------------------------------------------------ Deep links from the site
# https://t.me/<бот>?start=<payload> открывает бота и отправляет «/start <payload>».
# Каждый payload открывает тот же экран, что и соответствующая кнопка меню.
DEEP_LINKS = {
    "museum": "museum", "halls": "halls", "catalog": "catalog",
    "favorites": "favorites", "stats": "stats", "today": "history:today",
    "search": "search", "quiz": "quiz:start",
    "feedback": "feedback", "team": "team",
    **{f"hall{n}": f"hall:{n}" for n in HALLS},
}


class DeepLinkCallback:
    """Изображает нажатие кнопки, чтобы глубокая ссылка использовала тот же обработчик."""

    def __init__(self, message: Message, user, data: str):
        self.message = message
        self.from_user = user
        self.data = data

    async def answer(self, text: str | None = None, show_alert: bool = False, **kwargs):
        if text:
            await self.message.answer(text)


def deep_link_target(payload: str) -> str | None:
    payload = (payload or "").strip()
    if payload.startswith("item_") and payload[5:] in BY_ID:
        return f"item:{payload[5:]}"
    return DEEP_LINKS.get(payload)


async def open_deep_link(message: Message, state: FSMContext, data: str):
    screen = await message.answer("⏳ Открываю…")
    callback = DeepLinkCallback(screen, message.from_user, data)
    handlers = {
        "museum": enter_museum, "halls": show_halls, "catalog": show_catalog,
        "favorites": show_favorites, "stats": show_stats, "history:today": this_day_in_history,
        "search": begin_search, "quiz:start": start_quiz,
        "feedback": begin_feedback, "team": project_team,
    }
    if data.startswith("hall:"):
        await show_hall(callback, state)
    elif data.startswith("item:"):
        await show_item(callback, state)
    else:
        handler = handlers[data]
        takes_state = handler.__code__.co_argcount > 1
        await (handler(callback, state) if takes_state else handler(callback))


@router.message(Command("start"))
async def start(message: Message, state: FSMContext, command: CommandObject | None = None):
    await state.clear()
    target = deep_link_target(command.args if command else None)
    if target:
        try:
            await open_deep_link(message, state, target)
            return
        except Exception as exc:
            print(f"Could not open the deep link {target!r}: {exc}")
    await message.answer(main_menu_text(), reply_markup=main_keyboard())


@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "Кнопки под сообщениями ведут по музею: залы и каталог, избранное, личная "
        "статистика, «Этот день в истории», поиск с фильтрами, "
        "викторина и отзывы.\n\n"
        "/start — главное меню\n/help — эта подсказка",
        reply_markup=main_keyboard(),
    )


@router.callback_query(F.data == "home")
async def home(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_text(callback.message, main_menu_text(), reply_markup=main_keyboard())
    await callback.answer()


@router.callback_query(F.data == "museum")
async def enter_museum(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_text(callback.message,
        "🏛 Добро пожаловать в музей\n\nКак хотите смотреть экспонаты?",
        reply_markup=museum_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "team")
async def project_team(callback: CallbackQuery):
    await show_text(callback.message,
        "👥 Команда проекта\n\n"
        "«Музей изобретений русских людей» сделан как образовательный проект "
        "Ломоносовской школы-пансиона. Его создали:\n\n"
        "• Костенко Григорий\n"
        "• Мазанова Анфиса\n"
        "• Диденко Екатерина\n"
        "• Конопелько Александр\n\n"
        "Музей входит в одну экосистему с англоязычным World of Inventions: "
        "там собраны изобретения со всего мира.",
        reply_markup=team_keyboard(SITE_URL),
    )
    await callback.answer()


@router.callback_query(F.data == "feedback")
async def begin_feedback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FeedbackState.waiting_for_message)
    await show_text(callback.message,
        "💬 Предложения и отзывы\n\n"
        "Есть идея, нашли ошибку или хотите предложить изобретение? "
        "Напишите сообщение, и бот перешлёт его команде проекта.\n\n"
        "Отправьте одно текстовое сообщение. /start — отменить.",
    )
    await callback.answer()


@router.message(FeedbackState.waiting_for_message, F.text)
async def receive_feedback(message: Message, state: FSMContext, bot: Bot):
    feedback = message.text.strip()
    if not feedback:
        await message.answer("Сообщение пустое. Попробуйте ещё раз.")
        return

    if not ADMIN_ID:
        await state.clear()
        await message.answer(
            "Спасибо за отзыв! Почтовый ящик проекта ещё не настроен, поэтому "
            "сообщение не удалось переслать. Попробуйте позже.",
            reply_markup=main_keyboard(),
        )
        # Лог на сервере, чтобы разработчик заметил, что настройки не хватает.
        print(f"Feedback received but ADMIN_ID is not configured. User ID: {message.from_user.id}; message: {feedback}")
        return

    sender = message.from_user
    username = f"@{sender.username}" if sender.username else "нет имени пользователя"
    report = (
        "📩 Новый отзыв (Музей изобретений русских людей)\n\n"
        f"От: {sender.full_name}\n"
        f"Имя пользователя: {username}\n"
        f"Telegram ID: {sender.id}\n\n"
        f"Сообщение:\n{feedback}"
    )
    try:
        await bot.send_message(ADMIN_ID, report)
    except Exception:
        await state.clear()
        await message.answer(
            "Не получилось доставить сообщение. Попробуйте позже.",
            reply_markup=main_keyboard(),
        )
        return

    await state.clear()
    await message.answer(
        "Спасибо! Сообщение отправлено команде проекта. 💙",
        reply_markup=main_keyboard(),
    )


@router.message(FeedbackState.waiting_for_message)
async def feedback_non_text(message: Message):
    await message.answer("Пришлите отзыв текстовым сообщением или отправьте /start, чтобы отменить.")


@router.callback_query(F.data == "halls")
async def show_halls(callback: CallbackQuery):
    await show_text(callback.message, "🏛 Залы музея\n\nВыберите историческую эпоху:", reply_markup=halls_keyboard())
    await callback.answer()


# ------------------------------------------------------------------ Exhibit lists (paged)
LIST_BACK_LABELS = {
    "hall": "⬅️ Зал", "catalog": "⬅️ Каталог", "fav": "⬅️ Избранное",
    "country": "⬅️ Страна", "res": "⬅️ Результаты",
}


def hall_items(hall_id: str):
    return [item for item in INVENTIONS if str(item["hall"]) == str(hall_id)]


def exhibits_word(n: int) -> str:
    """«экспонат», «экспоната» или «экспонатов» — по правилам русского языка."""
    if n % 10 == 1 and n % 100 != 11:
        return "экспонат"
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return "экспоната"
    return "экспонатов"


async def build_list(key: str, state: FSMContext, user_id: int, page: int = 0):
    """Возвращает (текст, клавиатура) одной страницы списка экспонатов или None для
    неизвестного ключа. Весь список запоминается как контекст: на карточке кнопки
    ◀️ Назад и Дальше ▶️ листают его, а кнопка возврата ведёт на ту же страницу."""
    kind, _, value = key.partition(":")
    if kind == "catalog":
        items = INVENTIONS
        text = f"📚 Весь каталог\n\n{len(items)} {exhibits_word(len(items))}. Выберите:"
        markup = items_keyboard(items, key="catalog", page=page)
    elif kind == "hall" and value in HALLS:
        hall = HALLS[value]
        items = hall_items(value)
        text = f"🏛 {hall['name']}\n{hall['title']}\n\n{hall['description']}\n\n"
        text += "Выберите экспонат." if items else "Зал готовится к открытию. Загляните позже."
        markup = hall_items_keyboard(items, value, page)
    elif kind == "fav":
        ids = await db_call(get_favorites, user_id, default=[])
        items = [BY_ID[i] for i in ids if i in BY_ID]
        if not items:
            await state.update_data(nav_key=None, nav_ids=[])
            return (
                "⭐ Избранное\n\nВы пока ничего не сохранили.\n"
                "Откройте экспонат и нажмите «В избранное», чтобы он появился здесь.",
                info_keyboard(),
            )
        text = f"⭐ Избранное\n\nСохранено: {len(items)} {exhibits_word(len(items))}. Нажмите, чтобы открыть:"
        markup = favorites_keyboard(items, page)
    elif kind == "res":
        data = await state.get_data()
        filters, query = read_filters(data), data.get("f_query")
        items = search_matches(filters, query)
        text = results_text(items, filters, query)
        markup = results_keyboard(items, page)
    else:
        return None
    await state.update_data(nav_key=key, nav_ids=[i["id"] for i in items])
    return text, markup


async def open_list(callback: CallbackQuery, state: FSMContext, key: str, page: int = 0):
    built = await build_list(key, state, callback.from_user.id, page)
    if built is None:
        await callback.answer("Этот список больше недоступен.", show_alert=True)
        return
    text, markup = built
    await show_text(callback.message, text, reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data.startswith("hall:"))
async def show_hall(callback: CallbackQuery, state: FSMContext):
    hall_id = callback.data.split(":", 1)[1]
    if hall_id not in HALLS:
        await callback.answer("Зал не найден.", show_alert=True)
        return
    await db_call(mark_hall_opened, callback.from_user.id, hall_id)
    await open_list(callback, state, f"hall:{hall_id}")


@router.callback_query(F.data == "catalog")
async def show_catalog(callback: CallbackQuery, state: FSMContext):
    await open_list(callback, state, "catalog")


@router.callback_query(F.data.startswith("pg:"))
async def change_page(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":", 2)
    try:
        page, key = int(parts[1]), parts[2]
    except (IndexError, ValueError):
        await callback.answer("Неверная страница.", show_alert=True)
        return
    await open_list(callback, state, key, page)


@router.callback_query(F.data == "noop")
async def do_nothing(callback: CallbackQuery):
    await callback.answer()


# ------------------------------------------------------------------ Exhibit card
async def exhibit_context(state: FSMContext, item) -> dict:
    """Листалка и кнопка возврата карточки — по списку, из которого пришёл посетитель.
    Без списка (например, после перезапуска) берётся зал самого экспоната."""
    data = await state.get_data()
    key = data.get("nav_key")
    ids = [i for i in (data.get("nav_ids") or []) if i in BY_ID]
    if not key or item["id"] not in ids:
        key = f"hall:{item['hall']}"
        ids = [i["id"] for i in hall_items(item["hall"])]
        await state.update_data(nav_key=key, nav_ids=ids)
    index = ids.index(item["id"])
    count = len(ids)
    kind = key.partition(":")[0]
    context = {
        "back": (LIST_BACK_LABELS.get(kind, "⬅️ Назад"), f"pg:{index // ITEMS_PER_PAGE}:{key}"),
    }
    if count > 1:
        context.update(
            prev_id=ids[(index - 1) % count],
            next_id=ids[(index + 1) % count],
            position=(index + 1, count),
        )
    return context


@router.callback_query(F.data.startswith("item:"))
async def show_item(callback: CallbackQuery, state: FSMContext):
    item_id = callback.data.split(":", 1)[1]
    item = BY_ID.get(item_id)
    if item is None:
        await callback.answer("Экспонат не найден.", show_alert=True)
        return
    user_id = callback.from_user.id
    await db_call(mark_exhibit_studied, user_id, item_id)
    saved = bool(await db_call(is_favorite, user_id, item_id, default=False))
    context = await exhibit_context(state, item)
    # Возврат с экрана «Как это работает» этого же экспоната: у того экрана нет кнопки
    # «how:», но есть «item:<id>», поэтому фото остаётся.
    reuse_photo = (
        bool(callback.message.photo)
        and not message_has_button_prefix(callback.message, "how:")
        and message_has_button(callback.message, callback.data)
    )
    await show_item_card(
        callback.message, item, format_invention(item),
        navigation_keyboard(item, saved, **context), reuse_photo=reuse_photo,
    )
    await callback.answer()


# ------------------------------------------------------------------ How It Works
@router.callback_query(F.data.startswith("how:"))
async def show_how_it_works(callback: CallbackQuery, state: FSMContext):
    item = BY_ID.get(callback.data.split(":", 1)[1])
    if item is None:
        await callback.answer("Экспонат не найден.", show_alert=True)
        return
    saved = bool(await db_call(is_favorite, callback.from_user.id, item["id"], default=False))
    context = await exhibit_context(state, item)
    text = f"⚙️ Как это работает · {item['name']}\n\n{item['how_it_works']}"
    await show_card_text(callback.message, text, how_keyboard(item, saved, back=context["back"]))
    await callback.answer()


# ------------------------------------------------------------------ Favorites
@router.callback_query(F.data.startswith("favorite:toggle:"))
async def toggle_favorite_handler(callback: CallbackQuery):
    item = BY_ID.get(callback.data.split(":", 2)[2])
    if item is None:
        await callback.answer("Экспонат не найден.", show_alert=True)
        return
    saved = await db_call(toggle_favorite, callback.from_user.id, item["id"])
    if saved is None:
        await callback.answer("Не удалось обновить избранное. Попробуйте ещё раз.", show_alert=True)
        return
    # Меняется только подпись кнопки избранного; листалка и остальные кнопки остаются.
    new_markup = relabel_favorite(callback.message.reply_markup, item["id"], saved)
    if new_markup is not None:
        try:
            await callback.message.edit_reply_markup(reply_markup=new_markup)
        except TelegramBadRequest as exc:
            if not is_not_modified(exc):
                raise
    await callback.answer("⭐ Добавлено в избранное" if saved else "Убрано из избранного")


@router.callback_query(F.data == "favorites")
async def show_favorites(callback: CallbackQuery, state: FSMContext):
    await open_list(callback, state, "fav")


# ------------------------------------------------------------------ Personal statistics
@router.callback_query(F.data == "stats")
async def show_stats(callback: CallbackQuery):
    stats = await db_call(get_stats, callback.from_user.id)
    if stats is None:
        await callback.answer("Статистика сейчас недоступна.", show_alert=True)
        return
    studied = min(stats["studied_exhibits"], len(INVENTIONS))
    halls = min(stats["opened_halls"], len(HALLS))
    total_answers = stats["total_answers"]
    if total_answers:
        accuracy = round(100 * stats["correct_answers"] / total_answers)
        answers_line = f"{stats['correct_answers']} из {total_answers} ({accuracy}%)"
    else:
        answers_line = "пока нет ответов"
    await show_text(
        callback.message,
        "📊 Личная статистика\n\n"
        f"📚 Изучено экспонатов: {studied} из {len(INVENTIONS)}\n"
        f"🏛 Открыто залов: {halls} из {len(HALLS)}\n"
        f"⭐ В избранном: {stats['favorites']}\n"
        f"🧠 Верных ответов в викторине: {answers_line}\n"
        f"🏁 Пройдено викторин: {stats['quizzes_completed']}\n\n"
        "Экспонат считается изученным, когда вы его открываете.",
        reply_markup=info_keyboard(),
    )
    await callback.answer()


# ------------------------------------------------------------------ This Day in History
def today_date() -> date:
    """Сегодняшняя дата по Москве: сервер может стоять в другом часовом поясе."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/Moscow")).date()
    except Exception:
        return datetime.now().date()


def next_occurrence(event, today: date) -> date:
    """Ближайшая дата, когда наступят день и месяц события (29 февраля в календаре нет)."""
    this_year = date(today.year, event["month"], event["day"])
    return this_year if this_year >= today else date(today.year + 1, event["month"], event["day"])


def previous_occurrence(event, today: date) -> date:
    this_year = date(today.year, event["month"], event["day"])
    return this_year if this_year <= today else date(today.year - 1, event["month"], event["day"])


def history_line(event) -> str:
    icon = HISTORY_KIND_ICONS.get(event["kind"], "📅")
    return f"{icon} {event['year']} — {event['title']}\n{event['text']}"


def days_word(n: int) -> str:
    if n % 10 == 1 and n % 100 != 11:
        return "день"
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return "дня"
    return "дней"


def build_history(today: date):
    """Возвращает (текст, id связанных экспонатов). Показываются события ровно на сегодня;
    если их нет, показываются ближайшие события до и после."""
    heading = f"📅 Этот день в истории · {today.day} {MONTH_NAMES[today.month - 1]}"
    exact = sorted(
        (e for e in HISTORY if (e["month"], e["day"]) == (today.month, today.day)),
        key=lambda e: e["year"],
    )
    if exact:
        events = exact[:3]
        text = heading + "\n\n" + "\n\n".join(history_line(e) for e in events)
    else:
        upcoming = min(HISTORY, key=lambda e: next_occurrence(e, today))
        past = max(HISTORY, key=lambda e: previous_occurrence(e, today))
        ahead = (next_occurrence(upcoming, today) - today).days
        behind = (today - previous_occurrence(past, today)).days
        events = [past, upcoming] if behind <= ahead else [upcoming, past]
        lines = []
        for e in events:
            day_label = f"{e['day']} {MONTH_NAMES[e['month'] - 1]}"
            if e is upcoming:
                when = "завтра" if ahead == 1 else f"через {ahead} {days_word(ahead)}"
            else:
                when = "вчера" if behind == 1 else f"{behind} {days_word(behind)} назад"
            lines.append(f"({when}, {day_label})\n{history_line(e)}")
        text = (
            heading + "\n\nВ нашем календаре нет события ровно на сегодня. "
            "Ближайшие даты:\n\n" + "\n\n".join(lines)
        )
    related = []
    for e in events:
        if e.get("related_id") and e["related_id"] not in related:
            related.append(e["related_id"])
    return text, related


@router.callback_query(F.data == "history:today")
async def this_day_in_history(callback: CallbackQuery, state: FSMContext):
    await state.update_data(nav_key=None, nav_ids=[])  # у экспонатов отсюда нет списка для листания
    text, related = build_history(today_date())
    await show_text(
        callback.message, text, reply_markup=history_keyboard([BY_ID[i] for i in related])
    )
    await callback.answer()


# ------------------------------------------------------------------ Search & filters
def read_filters(data: dict) -> dict:
    return {"hall": data.get("f_hall"), "period": data.get("f_period")}


def apply_filters(items, filters: dict):
    return [
        item for item in items
        if (not filters["hall"] or str(item["hall"]) == filters["hall"])
        and (not filters["period"] or item["period"] == filters["period"])
    ]


def search_matches(filters: dict, query: str | None):
    """Экспонаты, которые проходят фильтры и (если задано) содержат слово поиска."""
    items = apply_filters(INVENTIONS, filters)
    if not query or not query.strip():
        return items
    needle = normalize_text(query.strip())
    return [
        item for item in items
        if needle in normalize_text(" ".join(str(item.get(key, "")) for key in (
            "name", "period", "year", "inventor", "country", "origin", "features",
            "significance", "further_facts"
        )))
    ]


def describe_filters(filters: dict) -> str:
    hall = f"Зал {filters['hall']} · {HALLS[filters['hall']]['title']}" if filters["hall"] else "все"
    period = filters["period"] or "все"
    return f"Зал: {hall}\nПериод: {period}"


def filters_active(filters: dict) -> bool:
    return any(filters.values())


def results_text(items, filters: dict, query: str | None) -> str:
    head = f"🔎 Результаты по запросу «{query}»" if query else "📋 Результаты"
    if items:
        head += f" · {len(items)} {exhibits_word(len(items))}"
    parts = [head]
    if filters_active(filters):
        parts.append(f"Фильтры:\n{describe_filters(filters)}")
    if not items:
        parts.append("Ничего не найдено. Попробуйте другое слово или измените фильтры.")
    return "\n\n".join(parts)


async def render_filters(message: Message, state: FSMContext):
    # Пока открыт экран фильтров, написанный текст ищется внутри выбранных фильтров.
    await state.set_state(SearchState.waiting_for_query)
    filters = read_filters(await state.get_data())
    matches = apply_filters(INVENTIONS, filters)
    await show_text(
        message,
        "🔎 Поиск и фильтры\n\n"
        f"{describe_filters(filters)}\n\n"
        f"Подходит экспонатов: {len(matches)}\n\n"
        "Выберите фильтры и нажмите «Показать» или напишите слово "
        "(изобретение, изобретатель, страна, год…), чтобы искать внутри фильтров.",
        reply_markup=filters_keyboard(HALLS, len(matches), active=filters),
    )


@router.callback_query(F.data == "search")
async def begin_search(callback: CallbackQuery, state: FSMContext):
    await state.update_data(f_query=None)
    await render_filters(callback.message, state)
    await callback.answer()


@router.callback_query(F.data == "filter:reset")
async def reset_filters(callback: CallbackQuery, state: FSMContext):
    await state.update_data(f_hall=None, f_period=None, f_query=None)
    await render_filters(callback.message, state)
    await callback.answer("Фильтры сброшены")


@router.callback_query(F.data == "filter:results")
async def show_filter_results(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SearchState.waiting_for_query)
    await state.update_data(f_query=None)
    await open_list(callback, state, "res")


@router.callback_query(F.data.startswith("filter:"))
async def choose_filter(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":", 2)
    if len(parts) != 3:
        await callback.answer("Неверный фильтр.", show_alert=True)
        return
    _, kind, value = parts
    filters = read_filters(await state.get_data())

    if kind == "hall" and value == "menu":
        await show_text(
            callback.message, "🏛 Фильтр по залу\n\nВыберите зал:",
            reply_markup=hall_filter_keyboard(HALLS, active=filters["hall"]),
        )
        await callback.answer()
        return
    if kind == "period" and value == "menu":
        await show_text(
            callback.message, "📅 Фильтр по периоду\n\nВыберите период:",
            reply_markup=period_filter_keyboard(PERIODS, active=filters["period"]),
        )
        await callback.answer()
        return

    if kind == "hall" and (value == "all" or value in HALLS):
        await state.update_data(f_hall=None if value == "all" else value)
    elif kind == "period" and (value == "all" or value in PERIODS):
        await state.update_data(f_period=None if value == "all" else value)
    else:
        await callback.answer("Неверный фильтр.", show_alert=True)
        return
    await render_filters(callback.message, state)
    await callback.answer()


@router.message(SearchState.waiting_for_query, F.text)
async def search(message: Message, state: FSMContext):
    query = message.text.strip()
    if not normalize_text(query):
        await message.answer("Напишите слово для поиска.")
        return
    await state.update_data(f_query=query[:60])
    text, markup = await build_list("res", state, message.from_user.id)
    await message.answer(text, reply_markup=markup)


@router.message(SearchState.waiting_for_query)
async def search_non_text(message: Message):
    await message.answer("Напишите запрос текстом или отправьте /start, чтобы отменить.")


@router.callback_query(F.data == "quiz:start")
async def start_quiz(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    round_size = min(QUIZ_ROUND_SIZE, len(QUIZ))
    question_order = random.sample(range(len(QUIZ)), k=round_size)
    # У каждого вопроса свой порядок вариантов. Храним исходные индексы, чтобы
    # после перемешивания всё равно знать правильный ответ.
    option_orders = []
    for question_index in question_order:
        order = list(range(len(QUIZ[question_index]["options"])))
        random.shuffle(order)
        option_orders.append(order)

    await state.update_data(
        quiz_order=question_order,
        quiz_option_orders=option_orders,
        quiz_index=0,
        quiz_score=0,
    )
    await send_quiz_question(callback.message, state, edit=True)
    await callback.answer()


async def send_quiz_question(message: Message, state: FSMContext, edit: bool = False):
    data = await state.get_data()
    round_index = data.get("quiz_index", 0)
    question_order = data.get("quiz_order", [])
    option_orders = data.get("quiz_option_orders", [])

    if round_index >= len(question_order):
        return

    question = QUIZ[question_order[round_index]]
    shuffled_options = [question["options"][i] for i in option_orders[round_index]]
    text = (
        f"🧠 Викторина · Вопрос {round_index + 1}/{len(question_order)}\n\n"
        f"{question['question']}"
    )
    markup = quiz_answer_keyboard(round_index, shuffled_options)
    if edit:
        await show_text(message, text, reply_markup=markup)
    else:
        await message.answer(text, reply_markup=markup)


@router.callback_query(F.data.startswith("quiz:answer:"))
async def answer_quiz(callback: CallbackQuery, state: FSMContext):
    try:
        _, _, round_index_text, selected_text = callback.data.split(":")
        round_index, selected_display_index = int(round_index_text), int(selected_text)
    except (ValueError, TypeError):
        await callback.answer("Неверный ответ.", show_alert=True)
        return

    data = await state.get_data()
    question_order = data.get("quiz_order", [])
    option_orders = data.get("quiz_option_orders", [])
    current_index = data.get("quiz_index")

    if current_index is None or round_index != current_index or round_index >= len(question_order):
        await callback.answer("На этот вопрос уже ответили. Можно начать новую викторину.", show_alert=True)
        return

    question = QUIZ[question_order[round_index]]
    displayed_option_order = option_orders[round_index]
    if not 0 <= selected_display_index < len(displayed_option_order):
        await callback.answer("Неверный ответ.", show_alert=True)
        return

    original_option_index = displayed_option_order[selected_display_index]
    correct = original_option_index == question["answer"]
    user_id = callback.from_user.id
    await db_call(record_answer, user_id, correct)
    score = data.get("quiz_score", 0) + int(correct)
    next_index = round_index + 1
    await state.update_data(quiz_score=score, quiz_index=next_index)

    result_line = (
        "✅ Верно!" if correct else
        f"❌ Не совсем. Правильный ответ: {question['options'][question['answer']]}"
    )
    feedback_text = f"{result_line}\n\n💡 {question['fact']}"
    total_questions = len(question_order)

    if next_index >= total_questions:
        await state.clear()
        await db_call(record_quiz_completed, user_id)
        feedback_text += f"\n\n🏁 Викторина окончена!\nВаш результат: {score}/{total_questions}"
        if score == total_questions:
            feedback_text += "\nВсе ответы верные, отлично! 🌟"
        elif score >= total_questions * 0.6:
            feedback_text += "\nХороший результат! Вы знаете изобретения. 👏"
        else:
            feedback_text += "\nНеплохо! Загляните в залы музея и попробуйте ещё раз. 📚"
        await show_text(callback.message, feedback_text, reply_markup=quiz_result_keyboard())
    else:
        await show_text(callback.message,
            feedback_text + f"\n\nСчёт: {score}/{next_index}",
            reply_markup=quiz_result_keyboard_continue(next_index),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("quiz:next:"))
async def next_quiz_question(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    try:
        requested_index = int(callback.data.rsplit(":", 1)[1])
    except ValueError:
        await callback.answer("Неверный вопрос.", show_alert=True)
        return

    question_order = data.get("quiz_order", [])
    if data.get("quiz_index") != requested_index or requested_index >= len(question_order):
        await callback.answer("Эта викторина уже закончилась.", show_alert=True)
        return
    await send_quiz_question(callback.message, state, edit=True)
    await callback.answer()


@router.message(StateFilter(None), F.text)
async def unknown_message(message: Message):
    await message.answer("Пользуйтесь кнопками меню, чтобы ходить по музею.", reply_markup=main_keyboard())
