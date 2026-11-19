# Сайт «Музея изобретений русских людей»

Витрина русскоязычного бота экосистемы World of Inventions. Публикуется на GitHub Pages
по адресу https://worldofinventions.github.io/ru/ вместе с английским сайтом (`.github/workflows/pages.yml`).

```powershell
npm install
npm run data    # данные из ../handlers.py и ../data/*.json, фото и их авторы
npm run data:map  # карта (только если появилась новая страна)
npm run og      # картинка для ссылок public/og.png
npm run build   # -> dist/
```

Общее описание русского музея: [../README.md](../README.md).
