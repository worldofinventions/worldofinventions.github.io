// ──────────────────────────────────────────────────────────────────────────
//  Mini app config. The bot's address is only used for "write to the bot"
//  hints; everything else lives inside the app itself.
// ──────────────────────────────────────────────────────────────────────────

export const BOT_URL = 'https://t.me/lshpdigitalmuseumbot';
/** Соседний музей экосистемы: World of Inventions, на английском. */
export const WORLD_BOT_URL = 'https://t.me/jdjsbehenbot';
export const SITE_URL = 'https://worldofinventions.github.io/ru/';

export const botStartUrl = (payload?: string): string => (payload ? `${BOT_URL}?start=${encodeURIComponent(payload)}` : BOT_URL);

export interface TeamMember {
  name: string;
  role: string;
  photo?: string;
  link?: string;
}

// The curators, as listed in the bot's "Project Team" screen (handlers.py).
export const TEAM: TeamMember[] = [
  { name: 'Григорий Костенко', role: 'Команда проекта' },
  { name: 'Анфиса Мазанова', role: 'Команда проекта' },
  { name: 'Екатерина Диденко', role: 'Команда проекта' },
  { name: 'Александр Конопелько', role: 'Команда проекта' },
];
