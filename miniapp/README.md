# World of Inventions — Mini App (версия 2)

Telegram Mini App — **весь функционал бота внутри приложения**, собранный на дизайн-системе
и секциях существующего сайта (Fraunces/Hanken Grotesk, рамки-«витрины», залы с постаментами,
гравированный атлас мира, листки календаря, «экзаменационный лист» викторины).

То, что на сайте было презентацией бота, здесь работает по-настоящему:

| Экран | Что делает |
|---|---|
| 🏛 **Home** | Плитки всех разделов, прогресс и избранное |
| 🏺 **Halls** | 4 зала с постаментами (порт секции сайта); открытие залов пишется в статистику |
| 📚 **Catalogue** | Каталог-«картотека» с поиском и фильтрами — те же правила, что у бота (порт `bot.ts`) |
| 🗺 **Map** | Гравированный атлас мира + список стран по континентам (порт `map.ts`) |
| 📅 **This Day** | Календарь с выбором даты, «ближайшие даты» по правилам бота |
| 🧠 **Quiz** | **Полный раунд на 10 вопросов**: сессия на сервере, ответы идут в статистику |
| ⭐ **Favorites** | Сохранённые экспонаты (на сервере, общие с ботом) |
| 📊 **Statistics** | Изучено/залы/точность/раунды — живьём из БД |
| 💬 **Feedback** | Сообщение админу (тот же «почтовый ящик», что у бота) |
| 👥 **Team** | Табличка кураторов |
| 🖼 **Витрина** | Полноэкранная карточка экспоната: фото, факты, «How it works»-чертёж, источники, свайп/стрелки, кнопка избранного |

## Структура

```
miniapp/
├── server.py        # aiohttp: мини-апп + JSON API + бот (webhook/polling) в одном процессе
├── README.md
├── web/             # СБОРКА фронтенда — то, что отдаёт сервер (не редактировать руками)
└── ui/              # исходники фронтенда (Vite + TypeScript)
    ├── package.json, vite.config.ts, tsconfig.json, index.html
    └── src/
        ├── app.ts       # Telegram bootstrap, роутер, таб-бар, BackButton, тема
        ├── api.ts       # клиент JSON API (избранное, статистика, викторина, feedback)
        ├── state.ts     # состояние посетителя
        ├── ui.ts        # DOM-хелперы сайта (адаптированы: фото с сервера мини-аппа)
        ├── data.ts      # копия data.ts сайта (сгенерированные JSON в src/data/generated/)
        ├── bot.ts       # точный порт логики бота с сайта: search, history, quiz-раунды
        ├── modal.ts     # витрина + избранное + отметка «изучено»
        ├── styles/      # base/halls/sections.css сайта + app.css (оболочка приложения)
        └── views/       # home, halls, explorer, map, today, quiz, favorites, stats, feedback, team
```

Данные (`inventions.json`, `history.json`, карта, банк вопросов) берутся из тех же
сгенерированных файлов, что и сайт (`npm run data` в `site/`); копия лежит в
`miniapp/ui/src/data/generated/`. Избранное/статистика/викторина/feedback — через
API `server.py`, в общей с ботом SQLite.

## Сборка фронтенда

```powershell
cd miniapp\ui
npm install          # один раз
npm run build        # tsc + vite build → ../web/
npm run dev          # режим разработки на :5174 (API и фото проксируются на :10000)
```

## Запуск сервера (из корня проекта)

```powershell
# интерфейс в браузере без Telegram (демо-пользователь, ?uid=<число> для разных id)
$env:MINIAPP_DISABLE_TELEGRAM='1'
.\.venv\Scripts\python.exe miniapp\server.py

# сервер + бот (polling) — НЕ запускать, пока бот на Render активен (polling снимет webhook)
.\.venv\Scripts\python.exe miniapp\server.py
```

Новые Python-зависимости не нужны (`aiogram` + `aiohttp` уже в `requirements.txt`).

## Деплой на Render

Start Command сервиса бота: `python miniapp/server.py` (уже прописан в `render.yaml`).
Сервер сам поставит webhook, назначит мини-апп **меню-кнопкой бота** («🏛 Museum»)
и включит keep-awake. Пересборка фронтенда при деплое: если фронтенд меняется,
закоммитьте обновлённую `miniapp/web/` (сборка локальная), либо добавьте
build-команду на стороне Render.

### Сосуществование с картографическим мини-аппом

В проекте есть ещё один мини-апп — карта (`site/miniapp.html`, публикуется на
GitHub Pages, `WEBAPP_URL`). Они не конфликтуют:

- **Кнопка меню бота** — полное приложение («🏛 Museum», этот мини-апп). В
  `miniapp/server.py` функция `set_museum_menu_button` регистрируется/вызывается
  *после* хука из `bot.py`, поэтому приоритет у полного приложения;
  при локальном http-запуске кнопка не трогается.
- **Картографический мини-апп** остаётся доступным через инлайн-кнопку
  «🗺 Open Interactive Map» на экране карты бота (см. `keyboards.py`,
  параметр `WEBAPP_URL`). Глубокие ссылки `?startapp=item_<id>` у каждого
  приложения свои: карта отправляет экспонат в чат бота, этот мини-апп
  открывает свой каталог.

## API (кратко)

`GET /api/bootstrap` · `POST /api/progress/studied|hall` · `POST /api/favorites/{id}/toggle` ·
`GET /api/stats` · `GET /api/history/today` (не используется фронтендом, но доступен) ·
`POST /api/quiz/start|answer|next` · `POST /api/feedback` · `GET /healthz` ·
статика: `/` (мини-апп), `/exhibits/<id>.jpg` (+`thumb/`).

Авторизация: заголовок `X-Telegram-Init-Data` (HMAC-проверка); в локальном режиме
без Telegram — демо-пользователь.

## Deep links

`https://t.me/<bot>?startapp=<payload>` — payloads как у бота: `halls`, `catalog`,
`favorites`, `stats`, `today`, `map`, `quiz`, `feedback`, `team`, `hall1..4`, `item_<id>`.
