// The curators' plaque and the "More" hall of services.
import { h } from '../ui';
import { TEAM } from '../config';
import { state } from '../state';

export function mountTeam(root: HTMLElement): void {
  const plaque = h('div');
  if (!TEAM.length) {
    plaque.append(h('p.plaque__empty', {}, 'The names are being engraved.'), h('p.plaque__sub', {}, 'This plaque is waiting for its curators.'));
  } else {
    plaque.append(h('ul.plaque__list', { 'data-count': Math.min(TEAM.length, 8) }, ...TEAM.map((m) => {
      const initials = m.name.split(/\s+/).map((w) => w[0]).slice(0, 2).join('').toUpperCase();
      const portrait = m.photo
        ? h('img.plaque__photo', { src: m.photo, alt: `Portrait of ${m.name}`, width: 96, height: 96, loading: 'lazy' })
        : h('span.plaque__photo.plaque__photo--blank', { 'aria-hidden': 'true' }, initials);
      const name = m.link ? h('a', { href: m.link, target: '_blank', rel: 'noopener' }, m.name) : m.name;
      return h('li.plaque__person', {}, portrait, h('span.plaque__name', {}, name), h('span.plaque__role', {}, m.role));
    })));
  }

  root.append(h('section', {},
    h('div.wrap', {},
      h('div.plaque.plaque--page', {},
        h('span.plaque__screw', { 'aria-hidden': 'true' }),
        h('span.plaque__screw', { 'aria-hidden': 'true' }),
        h('span.plaque__screw', { 'aria-hidden': 'true' }),
        h('span.plaque__screw', { 'aria-hidden': 'true' }),
        h('h2', {}, 'This exhibition was curated by'),
        plaque,
        h('p.plaque__sub', {}, 'Thank you for visiting our project!')))));
}

const tile = (href: string, icon: string, name: string, sub: string): HTMLElement =>
  h('a.tile', { href },
    h('span.tile__ico', { 'aria-hidden': 'true' }, icon),
    h('span.tile__text', {}, h('b', {}, name), h('small', {}, sub)));

export function mountMore(root: HTMLElement): void {
  root.append(h('section', {},
    h('div.wrap', {},
      h('p.eyebrow', {}, 'Everything else'),
      h('h2', {}, '☰ More'),
      h('p.lead', {}, 'The rest of the museum: your collection, your record, the calendar, the quiz and ways to reach the team.'),
      h('div.tiles', {},
        tile('#/today', '📅', 'This Day in History', 'dated inventions & discoveries'),
        tile('#/quiz', '🧠', 'Invention Quiz', '10 questions per round'),
        tile('#/favorites', '⭐', 'My Favorites', `${state.favorites.size} saved`),
        tile('#/stats', '📊', 'Statistics', 'your personal progress'),
        tile('#/feedback', '💬', 'Feedback', 'suggest & improve'),
        tile('#/team', '👥', 'Project Team', 'the curators'),
        sisterTile()))));
}

/** The sister museum of the ecosystem: Russian inventions, in Russian (@lshpdigitalmuseumbot). */
function sisterTile(): HTMLElement {
  const url = 'https://t.me/lshpdigitalmuseumbot';
  const tg = (window as any).Telegram?.WebApp ?? null;
  return h('a.tile', {
    href: url, target: '_blank', rel: 'noopener', lang: 'ru',
    onclick: (e: Event) => { if (tg?.openTelegramLink) { e.preventDefault(); tg.openTelegramLink(url); } },
  },
    h('span.tile__ico', { 'aria-hidden': 'true' }, '🇷🇺'),
    h('span.tile__text', {}, h('b', {}, 'Музей изобретений русских людей'), h('small', { lang: 'en' }, 'the sister museum, in Russian')));
}
