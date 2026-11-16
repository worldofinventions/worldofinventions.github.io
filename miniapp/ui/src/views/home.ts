// The entrance hall of the app: everything is one tap away.
import { INVENTIONS, HALLS } from '../data';
import { h } from '../ui';
import { state } from '../state';

const tile = (href: string, icon: string, name: string, sub: string): HTMLElement =>
  h('a.tile', { href },
    h('span.tile__ico', { 'aria-hidden': 'true' }, icon),
    h('span.tile__text', {}, h('b', {}, name), h('small', {}, sub)));

export function mountHome(root: HTMLElement): void {
  const stats = state.stats;
  const studied = stats ? Math.min(stats.studied_exhibits, INVENTIONS.length) : null;
  const halls = Object.keys(HALLS).length;
  const name = state.user?.name ?? 'explorer';

  root.append(h('section.view-home', {},
    h('div.wrap', {},
      h('p.eyebrow', {}, 'Mini App · the museum in your pocket'),
      h('h2', {}, `Welcome, ${name.split(' ')[0]}`),
      h('p.lead', {},
        `${INVENTIONS.length} inventions in ${halls} halls, from the first telescopes to the web. `
        + 'Walk the halls, search the catalogue, test yourself — and your favorites, '
        + 'progress and quiz results are kept for your Telegram account.'),
      h('p.home__chips', {},
        studied !== null ? h('span.home__chip', {}, `📚 ${studied} / ${INVENTIONS.length} studied`) : null,
        h('span.home__chip', {}, `⭐ ${state.favorites.size} favorites`),
        h('span.home__chip', {}, `🗺 ${INVENTIONS.length} exhibits on the map`)),
      h('div.tiles', {},
        tile('#/halls', '🏺', 'Museum Halls', `${halls} halls on one timeline`),
        tile('#/catalog', '📚', 'Full Catalogue', 'search & filters, all exhibits'),
        tile('#/map', '🗺', 'Invention Map', 'by country of origin'),
        tile('#/today', '📅', 'This Day in History', 'dated inventions & discoveries'),
        tile('#/quiz', '🧠', 'Invention Quiz', '10 questions per round'),
        tile('#/favorites', '⭐', 'My Favorites', `${state.favorites.size} saved`),
        tile('#/stats', '📊', 'Statistics', 'your personal progress'),
        tile('#/feedback', '💬', 'Feedback', 'suggest & improve'),
        tile('#/team', '👥', 'Project Team', 'the curators')))));
}
