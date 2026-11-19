import { readFileSync } from 'node:fs';
import { defineConfig, type Plugin } from 'vite';
import { BOT_URL, WORLD_SITE_URL, SITE_URL as CONFIG_SITE_URL } from './src/config';

// Адрес русского сайта: RU_SITE_URL при сборке, иначе значение из config.ts.
const SITE_URL = (process.env.RU_SITE_URL || CONFIG_SITE_URL).replace(/\/$/, '');

/** Fills the __TOKENS__ in index.html from the data, so even the static HTML never hardcodes a number. */
function museumHtml(): Plugin {
  return {
    name: 'museum-html',
    transformIndexHtml: {
      order: 'pre',
      handler(html) {
        const read = (f: string) => JSON.parse(readFileSync(new URL(`./src/data/generated/${f}`, import.meta.url), 'utf8'));
        const inventions: { name: string; year: string }[] = read('inventions.json');
        const bot = read('bot-data.json');
        // Первое трёх- или четырёхзначное число: «863», «1056–1057», «ок. 950».
        const year = (y: string) => parseInt(/\d{3,4}/.exec(y)?.[0] ?? '0', 10);
        const sorted = inventions.filter((i) => year(i.year) > 0).sort((a, b) => year(a.year) - year(b.year));
        const first = sorted[0];
        const last = sorted[sorted.length - 1];
        const tokens: Record<string, string> = {
          MUSEUM: bot.museumName,
          N_EXHIBITS: String(inventions.length),
          N_HALLS: String(Object.keys(bot.halls).length),
          N_EVENTS: String(read('history.json').length),
          N_QUESTIONS: String(bot.quiz.length),
          YEAR_MIN: String(year(first.year)),
          YEAR_MAX: String(year(last.year)),
          FIRST_NAME: first.name,
          LAST_NAME: last.name,
          BOT_URL,
          WORLD_SITE_URL,
          OG_IMAGE: `${SITE_URL}/og.png`,
          SITE_URL: SITE_URL || '.',
        };
        return html.replace(/__([A-Z_]+)__/g, (all, key) => tokens[key] ?? all);
      },
    },
    generateBundle() {
      const read = (f: string) => JSON.parse(readFileSync(new URL(`./src/data/generated/${f}`, import.meta.url), 'utf8'));
      const bot = read('bot-data.json');
      const halls = Object.entries(bot.halls as Record<string, { name: string; title: string; description: string }>);
      this.emitFile({ type: 'asset', fileName: 'robots.txt', source: 'User-agent: *\nAllow: /\n' });
      this.emitFile({
        type: 'asset', fileName: 'llms.txt',
        source: `# ${bot.museumName}\n\n> Образовательный Telegram-бот Ломоносовской школы-пансиона: виртуальный музей изобретений, связанных с историей России. ` +
          `${read('inventions.json').length} экспонатов, ${read('history.json').length} дат в календаре, ${bot.quiz.length} вопросов викторины.\n\n## Залы\n\n` +
          halls.map(([id, hall]) => `- Зал ${id}, ${hall.name} (${hall.title}): ${hall.description}`).join('\n') +
          `\n\n## Ссылки\n\n- [Сайт](${SITE_URL || '.'}/index.html): залы, каталог, карта, «Этот день в истории», викторина\n- [Бот в Telegram](${BOT_URL})\n` +
          `- [World of Inventions](${WORLD_SITE_URL}): соседний музей изобретений мира, на английском\n`,
      });
    },
    buildStart() {
      if (BOT_URL.includes('<USERNAME>')) {
        this.warn('BOT_URL in src/config.ts still contains <USERNAME>. The Telegram buttons will not open the bot until it is set.');
      }
    },
  };
}

/** The two fonts used above the fold start loading together with the stylesheet. */
function preloadFonts(): Plugin {
  const wanted = [/literata-cyrillic-opsz-normal-.*.woff2$/, /onest-cyrillic-wght-normal-.*.woff2$/];
  return {
    name: 'preload-fonts',
    transformIndexHtml: {
      order: 'post',
      handler(html, ctx) {
        const files = Object.keys(ctx.bundle ?? {}).filter((f) => wanted.some((re) => re.test(f)));
        return {
          html,
          tags: files.map((f) => ({ tag: 'link', attrs: { rel: 'preload', as: 'font', type: 'font/woff2', href: `./${f}`, crossorigin: '' }, injectTo: 'head' as const })),
        };
      },
    },
  };
}

export default defineConfig({
  base: './',
  appType: 'mpa',
  plugins: [museumHtml(), preloadFonts()],
  build: {
    target: 'es2020',
    cssMinify: true,
    // index.html is the site; miniapp.html is the map the bot opens as a Telegram Mini App.
    rollupOptions: { input: { main: 'index.html', miniapp: 'miniapp.html' } },
  },
});
