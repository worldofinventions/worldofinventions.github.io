// ──────────────────────────────────────────────────────────────────────────
//  Everything a maintainer is expected to edit lives in this one file.
// ──────────────────────────────────────────────────────────────────────────

// The bot's Telegram address. Every "Open in Telegram" button on the site reads it.
export const BOT_URL = 'https://t.me/lshpdigitalmuseumbot';

/** Соседний музей экосистемы: World of Inventions (на английском) — бот и сайт. */
export const WORLD_BOT_URL = 'https://t.me/worldofinventions_app';
export const WORLD_SITE_URL = 'https://worldofinventions.github.io/';

/**
 * A link that opens the bot and sends "/start <payload>", so the bot goes straight
 * to one screen. The payloads are listed in DEEP_LINKS in ../handlers.py:
 * museum, halls, hall1..hall4, catalog, favorites, stats, today, map, search,
 * quiz, feedback, team, and item_<exhibit id>.
 */
export const botStartUrl = (payload?: string): string => (payload ? `${BOT_URL}?start=${encodeURIComponent(payload)}` : BOT_URL);

// TODO: paste the public repository URL. While it is empty, the footer simply
// leaves the repository link out.
export const REPO_URL = '';

// TODO: the address the site is deployed to (no trailing slash). It is only
// used for the absolute Open Graph / Twitter image URL.
export const SITE_URL = 'https://worldofinventions.github.io/ru';

export interface TeamMember {
  name: string;
  role: string;
  /** Path or URL of a square portrait, e.g. "/team/ada.jpg" (put the file in public/team/). */
  photo?: string;
  /** Personal link: Telegram, GitHub, a portfolio. */
  link?: string;
}

// TODO: add team members. The plaque lays itself out for 1 to 8 people.
// While the list is empty, the section shows a "names are being engraved" plaque.
//
//   { name: 'Ada Lovelace', role: 'Content & research', link: 'https://github.com/ada' },
//   { name: 'Charles Babbage', role: 'Bot development', photo: '/team/charles.jpg' },
export const TEAM: TeamMember[] = [
  { name: 'Григорий Костенко', role: 'Команда проекта' },
  { name: 'Анфиса Мазанова', role: 'Команда проекта' },
  { name: 'Екатерина Диденко', role: 'Команда проекта' },
  { name: 'Александр Конопелько', role: 'Команда проекта' },
];

/** How many questions the on-site taster quiz asks (the bot's own round size comes from handlers.py). */
export const SITE_QUIZ_SIZE = 5;
