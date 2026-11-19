# Музей изобретений русских людей

Русскоязычный бот экосистемы World of Inventions: **@lshpdigitalmuseumbot** («Цифровой музей🏛»),
образовательный проект Ломоносовской школы-пансиона. Устроен так же, как английский бот
@jdjsbehenbot из корня репозитория, и работает **в том же процессе на Render**.

| Часть | Где лежит | Адрес |
|---|---|---|
| Бот (aiogram 3) | `ru/handlers.py`, `ru/keyboards.py`, `ru/database.py`, `ru/config.py` | https://t.me/lshpdigitalmuseumbot |
| Сервер: webhook, API, Mini App | `ru/server.py`, подключается в `miniapp/server.py` под `/ru/` | https://world-of-inventions-bot.onrender.com/ru/ |
| Mini App (весь музей) | исходники `ru/miniapp/ui`, сборка `ru/miniapp/web` | кнопка «🏛 Музей» у бота |
| Сайт-витрина + карта | `ru/site` | https://worldofinventions.github.io/ru/ |
| Данные | `ru/data/inventions.json` (42 экспоната), `ru/data/history.json` (27 дат) | |
| Фото | `ru/site/public/exhibits/<id>.jpg`, авторы и лицензии в `ru/site/scripts/image-credits.json` | Wikimedia Commons |

## Экосистема

* В главном меню каждого бота есть кнопка соседнего музея (`ecosystem_row()` в обоих `keyboards.py`).
* Английский сайт ссылается на `/ru/`, русский сайт ссылается на английский.
* В Mini App обоих музеев на экране «Ещё / More» есть плитка соседнего бота.
* Отзывы из обоих ботов приходят одному администратору (`ADMIN_ID`).

## Залы

1. V–X века: истоки письменности и культуры
2. XI–XV века: средневековые технологии
3. XVI–XIX века: научный и промышленный прорыв
4. XX–XXI века: изобретения, изменившие мир

## Настройка на Render

В сервисе `world-of-inventions-bot` добавить переменную окружения **`RU_BOT_TOKEN`** (токен
@lshpdigitalmuseumbot) и сделать redeploy. При запуске сервер сам:

* ставит webhook `…/ru/telegram-webhook` (это отключает прежний ManyBot);
* назначает Mini App кнопкой меню бота;
* записывает описание и команды бота (`/start`, `/help`).

Без `RU_BOT_TOKEN` русский музей не подключается, а World of Inventions работает как раньше.
Необязательные переменные: `RU_ADMIN_ID` (если отзывы должен получать другой человек),
`RU_WEBAPP_URL` (`off` убирает кнопку интерактивной карты).

## Локальная разработка

```powershell
# интерфейс в браузере без Telegram: http://localhost:10000/ru/
$env:MINIAPP_DISABLE_TELEGRAM='1'
.\.venv\Scripts\python.exe miniapp\server.py
```

Не запускайте сервер локально с `RU_BOT_TOKEN`, пока бот работает на Render: локальный
polling снимет webhook, и бот перестанет отвечать на Render.

Сборка:

```powershell
cd ru\site;        npm install; npm run data; npm run build   # data: извлечение из ru/handlers.py, фото, карта
cd ru\miniapp\ui;  npm install; npm run build                 # → ru\miniapp\web (коммитится)
```

После правки `ru/data/*.json` или текстов в `ru/handlers.py` выполните `npm run data` в `ru/site`
и скопируйте `ru/site/src/data/generated/*.json` в `ru/miniapp/ui/src/data/generated/`.
