from math import ceil

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from .config import WORLD_BOT_URL

ITEMS_PER_PAGE = 8
FAVORITE_ADD_TEXT = "⭐ В избранное"
FAVORITE_REMOVE_TEXT = "💔 Убрать из избранного"


def btn(text: str, callback: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=text,
        callback_data=callback
    )


def chunk(buttons: list, size: int = 2) -> list[list]:
    """Разбивает кнопки на ряды по `size` штук (сетка вместо длинного столбца)."""
    return [buttons[i:i + size] for i in range(0, len(buttons), size)]


def nav_row() -> list:
    """Обычная пара кнопок внизу экрана."""
    return [btn("⬅️ Меню музея", "museum"), btn("🏠 Главное меню", "home")]


def ecosystem_row() -> list:
    """Переход в соседний музей экосистемы: World of Inventions (на английском)."""
    return [InlineKeyboardButton(text="🌍 World of Inventions (English)", url=WORLD_BOT_URL)]


# ---------------------------------------------------------------- menus
def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn("🏛 Войти в музей", "museum")],
        [btn("⭐ Избранное", "favorites"), btn("📊 Статистика", "stats")],
        [btn("📅 Этот день", "history:today"), btn("🗺 Карта", "map")],
        [btn("🔎 Поиск", "search"), btn("🧠 Викторина", "quiz:start")],
        [btn("💬 Отзыв", "feedback"), btn("👥 Команда", "team")],
        ecosystem_row(),
    ])


def museum_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn("🏛 Залы музея", "halls")],
        [btn("📚 Каталог", "catalog"), btn("🔎 Поиск", "search")],
        [btn("⭐ Избранное", "favorites"), btn("🗺 Карта", "map")],
        [btn("📊 Статистика", "stats"), btn("⬅️ Главное меню", "home")],
    ])


def halls_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn("Зал 1 · V–X века", "hall:1")],
        [btn("Зал 2 · XI–XV века", "hall:2")],
        [btn("Зал 3 · XVI–XIX века", "hall:3")],
        [btn("Зал 4 · XX–XXI века", "hall:4")],
        nav_row(),
    ])


# ---------------------------------------------------------------- lists of exhibits (paged)
def page_count(total: int, per_page: int = ITEMS_PER_PAGE) -> int:
    return max(1, ceil(total / per_page))


def paged_items_keyboard(
    items,
    key: str,
    page: int = 0,
    footer: list | None = None,
    per_page: int = ITEMS_PER_PAGE,
    prefix: str = "",
) -> InlineKeyboardMarkup:
    """Страница экспонатов (по одному в ряд, чтобы названия читались целиком),
    ряд ◀️ 2/5 ▶️, если страниц больше одной, и нижние ряды."""
    pages = page_count(len(items), per_page)
    page = page % pages
    rows = [
        [btn(f"{prefix}{item['name']}", f"item:{item['id']}")]
        for item in items[page * per_page:(page + 1) * per_page]
    ]
    if pages > 1:
        rows.append([
            btn("◀️", f"pg:{(page - 1) % pages}:{key}"),
            btn(f"{page + 1}/{pages}", "noop"),
            btn("▶️", f"pg:{(page + 1) % pages}:{key}"),
        ])
    rows.extend(footer if footer is not None else [nav_row()])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def items_keyboard(items, prefix="item:", key=None, page=0, footer=None) -> InlineKeyboardMarkup:
    """Список экспонатов. С `key` он листается по страницам, без него — простой список."""
    if key is not None:
        return paged_items_keyboard(items, key, page, footer)
    rows = [[btn(item["name"], f"{prefix}{item['id']}")] for item in items]
    rows.extend(footer if footer is not None else [nav_row()])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def hall_items_keyboard(items, hall_id: str, page: int = 0) -> InlineKeyboardMarkup:
    return paged_items_keyboard(
        items, f"hall:{hall_id}", page,
        footer=[[btn("⬅️ Все залы", "halls"), btn("🏠 Главное меню", "home")]],
    )


def favorites_keyboard(items, page: int = 0) -> InlineKeyboardMarkup:
    return paged_items_keyboard(items, "fav", page, prefix="⭐ ")


def results_keyboard(items, page: int = 0) -> InlineKeyboardMarkup:
    return paged_items_keyboard(
        items, "res", page,
        footer=[[btn("🔎 Изменить фильтры", "search")], nav_row()],
    )


def map_items_keyboard(items, country: str, page: int = 0) -> InlineKeyboardMarkup:
    """Экспонаты одной страны на карте изобретений."""
    return paged_items_keyboard(
        items, f"country:{country}", page,
        footer=[[btn("🗺 К карте", "map"), btn("🏠 Главное меню", "home")]],
    )


# ---------------------------------------------------------------- exhibit card
def navigation_keyboard(
    item,
    is_favorite=False,
    prev_id: str | None = None,
    next_id: str | None = None,
    position: tuple | None = None,
    back: tuple | None = None,
) -> InlineKeyboardMarkup:
    """Кнопки карточки экспоната.
    prev_id / next_id / position добавляют листалку ◀️ 3/25 ▶️; `back` — (подпись, callback)."""
    favorite_text = FAVORITE_REMOVE_TEXT if is_favorite else FAVORITE_ADD_TEXT
    back_label, back_callback = back or ("⬅️ Зал", f"hall:{item['hall']}")

    rows = []
    if prev_id and next_id and position:
        rows.append([
            btn("◀️ Назад", f"item:{prev_id}"),
            btn(f"{position[0]}/{position[1]}", "noop"),
            btn("Дальше ▶️", f"item:{next_id}"),
        ])
    rows.append([
        btn(favorite_text, f"favorite:toggle:{item['id']}"),
        btn("⚙️ Как это работает", f"how:{item['id']}"),
    ])
    rows.append([btn(back_label, back_callback), btn("🏠 Главное меню", "home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def how_keyboard(item, is_favorite: bool = False, back: tuple | None = None) -> InlineKeyboardMarkup:
    favorite_text = FAVORITE_REMOVE_TEXT if is_favorite else FAVORITE_ADD_TEXT
    back_label, back_callback = back or ("⬅️ Зал", f"hall:{item['hall']}")
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            btn(favorite_text, f"favorite:toggle:{item['id']}"),
            btn("⬅️ К экспонату", f"item:{item['id']}"),
        ],
        [btn(back_label, back_callback), btn("🏠 Главное меню", "home")],
    ])


def relabel_favorite(markup, item_id: str, saved: bool):
    """Копия `markup`, в которой меняется только подпись кнопки избранного.
    Подходит и для карточки, и для экрана «Как это работает», листалка сохраняется."""
    if markup is None:
        return None
    target = f"favorite:toggle:{item_id}"
    text = FAVORITE_REMOVE_TEXT if saved else FAVORITE_ADD_TEXT
    rows = [
        [btn(text if b.callback_data == target else b.text, b.callback_data) for b in row]
        for row in markup.inline_keyboard
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_keyboard(destination="home") -> InlineKeyboardMarkup:
    label = (
        "⬅️ Назад"
        if destination != "home"
        else "🏠 Главное меню"
    )
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn(label, destination)]
    ])


def team_keyboard(site_url: str | None = None) -> InlineKeyboardMarkup:
    """Экран команды: сайт музея, соседний музей и возврат в меню."""
    rows = []
    if site_url:
        rows.append([InlineKeyboardButton(text="🌐 Сайт музея", url=site_url)])
    rows.append(ecosystem_row())
    rows.append([btn("🏠 Главное меню", "home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def info_keyboard() -> InlineKeyboardMarkup:
    """Простая клавиатура для экранов вроде статистики или пустого избранного."""
    return InlineKeyboardMarkup(inline_keyboard=[nav_row()])


def history_keyboard(items) -> InlineKeyboardMarkup:
    """Ссылки на экспонаты, связанные с событиями дня."""
    rows = [
        [btn(f"🏺 Экспонат: {item['name']}", f"item:{item['id']}")]
        for item in items
    ]
    rows.append([btn("🏠 Главное меню", "home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ---------------------------------------------------------------- quiz
def quiz_answer_keyboard(
    question_index: int,
    options: list[str]
) -> InlineKeyboardMarkup:
    rows = [
        [
            btn(
                f"{'АБВГ'[i]}. {option}",
                f"quiz:answer:{question_index}:{i}"
            )
        ]
        for i, option in enumerate(options)
    ]
    rows.append([btn("🏠 Выйти из викторины", "home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def quiz_result_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn("🔁 Сыграть ещё", "quiz:start"), btn("🏠 Главное меню", "home")],
    ])


def quiz_result_keyboard_continue(next_index: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn("➡️ Следующий вопрос", f"quiz:next:{next_index}"), btn("🏠 Выйти", "home")],
    ])


# ---------------------------------------------------------------- map and filters
def countries_keyboard(
    countries: list[str],
    labels: dict | None = None,
    webapp_url: str | None = None,
) -> InlineKeyboardMarkup:
    """Кнопки стран текстовой карты. С `webapp_url` первый ряд открывает
    интерактивную карту как Telegram Mini App."""
    labels = labels or {}
    buttons = [
        btn(labels.get(country, country), f"map:country:{country}")
        for country in countries
    ]
    rows = []
    if webapp_url:
        rows.append([InlineKeyboardButton(text="🗺 Интерактивная карта", web_app=WebAppInfo(url=webapp_url))])
    rows.extend(chunk(buttons, 2))
    rows.append(nav_row())
    return InlineKeyboardMarkup(inline_keyboard=rows)


def filters_keyboard(
    countries: list[str],
    halls: dict,
    result_count: int | None = None,
    labels: dict | None = None,
    active: dict | None = None,
) -> InlineKeyboardMarkup:
    """Экран фильтров: кнопка результатов, страны в две колонки, меню залов и периодов.
    `active` ({'country','hall','period'}) отмечает выбранные фильтры значком ✅."""
    labels = labels or {}
    active = active or {}
    rows = []

    if result_count is not None:
        rows.append([btn(f"📋 Показать ({result_count})", "filter:results")])

    all_label = "🌍 Все страны" if active.get("country") else "✅ 🌍 Все страны"
    rows.append([btn(all_label, "filter:country:all")])

    country_buttons = []
    for country in countries:
        label = labels.get(country, f"🌍 {country}")
        if active.get("country") == country:
            label = f"✅ {label}"
        country_buttons.append(btn(label, f"filter:country:{country}"))
    rows.extend(chunk(country_buttons, 2))

    hall_label = "✅ 🏛 Зал" if active.get("hall") else "🏛 Зал"
    period_label = "✅ 📅 Период" if active.get("period") else "📅 Период"
    rows.append([btn(hall_label, "filter:hall:menu"), btn(period_label, "filter:period:menu")])
    rows.append([btn("🔄 Сбросить", "filter:reset"), btn("⬅️ Меню музея", "museum")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def hall_filter_keyboard(halls: dict, active: str | None = None) -> InlineKeyboardMarkup:
    rows = [[btn("✅ 🏛 Все залы" if not active else "🏛 Все залы", "filter:hall:all")]]
    for hall_id, hall in halls.items():
        label = f"Зал {hall_id} · {hall['title']}"
        if active == hall_id:
            label = f"✅ {label}"
        rows.append([btn(label, f"filter:hall:{hall_id}")])
    rows.append([btn("⬅️ К фильтрам", "search")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def period_filter_keyboard(periods: list[str], active: str | None = None) -> InlineKeyboardMarkup:
    rows = [[btn("✅ 📅 Все периоды" if not active else "📅 Все периоды", "filter:period:all")]]
    period_buttons = [
        btn(f"✅ {period}" if active == period else period, f"filter:period:{period}")
        for period in periods
    ]
    rows.extend(chunk(period_buttons, 2))
    rows.append([btn("⬅️ К фильтрам", "search")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
