// ──────────────────────────────────────────────────────────────────────────
//  Mini app config. The bot's address is only used for "write to the bot"
//  hints; everything else lives inside the app itself.
// ──────────────────────────────────────────────────────────────────────────

export const BOT_URL = 'https://t.me/jdjsbehenbot';

export const botStartUrl = (payload?: string): string => (payload ? `${BOT_URL}?start=${encodeURIComponent(payload)}` : BOT_URL);

export interface TeamMember {
  name: string;
  role: string;
  photo?: string;
  link?: string;
}

// The curators, as listed in the bot's "Project Team" screen (handlers.py).
export const TEAM: TeamMember[] = [
  { name: 'Grigoriy Kostenko', role: 'Project team' },
  { name: 'Matvey Mosienko', role: 'Project team' },
  { name: 'Sergey Isakov', role: 'Project team' },
  { name: 'Alexander Konopelko', role: 'Project team' },
];
