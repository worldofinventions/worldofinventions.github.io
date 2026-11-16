// The Telegram Mini App: the site's invention map on its own page, opened from the bot.
// Tapping an exhibit sends the user back to the chat with /start item_<id>,
// so the bot shows the exhibit's usual card (see DEEP_LINKS in ../../handlers.py).
import '@fontsource-variable/fraunces/full.css';
import '@fontsource-variable/hanken-grotesk/wght.css';
import '@fontsource/ibm-plex-mono/latin-400.css';
import '@fontsource/ibm-plex-mono/latin-500.css';
import '../styles/base.css';
import '../styles/sections.css';
import './miniapp.css';

import { botStartUrl } from '../config';
import { COUNTRIES, COUNTRY_INFO, PERIODS, countryItems } from '../data';
import { initMap } from '../sections/map';
import { h } from '../ui';

interface TelegramWebApp {
  initData: string;
  colorScheme: 'light' | 'dark';
  ready(): void;
  expand(): void;
  close(): void;
  openTelegramLink(url: string): void;
  onEvent(event: string, cb: () => void): void;
  setHeaderColor?(color: string): void;
  setBackgroundColor?(color: string): void;
  HapticFeedback?: { selectionChanged(): void; impactOccurred(style: string): void };
}
const tg: TelegramWebApp | undefined = (window as any).Telegram?.WebApp;
/** True only when the page was really opened by Telegram (outside it initData is empty). */
const inTelegram = Boolean(tg?.initData);

function applyTheme(): void {
  if (!tg || !inTelegram) return;
  document.documentElement.dataset.theme = tg.colorScheme === 'dark' ? 'dark' : 'light';
  // Paint Telegram's own header and background in the museum's paper colour.
  const paper = getComputedStyle(document.documentElement).getPropertyValue('--paper').trim();
  if (paper) {
    try { tg.setHeaderColor?.(paper); tg.setBackgroundColor?.(paper); } catch { /* older clients */ }
  }
}

const label = (c: string) => `${COUNTRY_INFO[c][0]} ${c === 'International' ? 'International' : c}`;
const byPeriod = (c: string) => {
  const counts = new Map(PERIODS.map((p) => [p, 0]));
  for (const item of countryItems(c)) counts.set(item.period, (counts.get(item.period) ?? 0) + 1);
  return counts;
};

// ---- comparison of two countries, century by century
let rival: string | null = null;

function comparison(country: string): Node[] {
  const box = h('section.tgc', { 'aria-label': 'Compare with another country' });
  const render = () => {
    const others = COUNTRIES.filter((c) => c !== country);
    if (rival === country || (rival && !others.includes(rival))) rival = null;
    const chips = h('div.tgc__chips', { role: 'group', 'aria-label': 'Compare with' },
      ...others.map((c) => h('button.tgc__chip', {
        type: 'button', 'aria-pressed': String(c === rival),
        onclick: () => { rival = c === rival ? null : c; tg?.HapticFeedback?.selectionChanged(); render(); },
      }, label(c))));
    const parts: Node[] = [h('h4.tgc__title', {}, '⚖️ Compare with'), chips];
    if (rival) {
      const a = byPeriod(country);
      const b = byPeriod(rival);
      const max = Math.max(1, ...a.values(), ...b.values());
      const bar = (n: number, cls: string) => h(`span.tgc__bar.${cls}`, { style: `--w:${((n / max) * 100).toFixed(1)}%` }, h('b', {}, String(n)));
      const total = (c: string) => countryItems(c).length;
      parts.push(
        h('p.tgc__legend', {}, h('span.tgc__key.tgc__key--a', {}, label(country), ` · ${total(country)}`), h('span.tgc__key.tgc__key--b', {}, label(rival), ` · ${total(rival)}`)),
        h('div.tgc__rows', {}, ...PERIODS.map((p) =>
          h('div.tgc__row', {}, h('span.tgc__period', {}, p), h('div.tgc__bars', {}, bar(a.get(p) ?? 0, 'a'), bar(b.get(p) ?? 0, 'b'))))));
    }
    box.replaceChildren(...parts);
  };
  render();
  return [box];
}

// ---- start
tg?.ready();
tg?.expand();
applyTheme();
tg?.onEvent('themeChanged', applyTheme);

let first = true;
initMap({
  panelExtra: comparison,
  onSelect: () => {
    if (!first) tg?.HapticFeedback?.selectionChanged();
    first = false;
  },
});

// An exhibit opens its card in the bot; the Mini App closes so the chat is visible.
document.addEventListener('click', (e) => {
  const trigger = (e.target as HTMLElement).closest<HTMLElement>('[data-exhibit]');
  if (!trigger) return;
  const url = botStartUrl(`item_${trigger.dataset.exhibit}`);
  if (inTelegram && tg) {
    tg.HapticFeedback?.impactOccurred('light');
    tg.openTelegramLink(url);
    tg.close();
  } else {
    window.open(url, '_blank', 'noopener');
  }
});
