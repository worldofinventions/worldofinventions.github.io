// My Favorites: the visitor's saved exhibits, straight from the server.
import { BY_ID } from '../data';
import { h } from '../ui';
import { state } from '../state';
import { exhibitCard } from './card';

export function mountFavorites(root: HTMLElement): void {
  const section = h('section', {});
  root.append(section);

  const render = (): void => {
    const items = [...state.favorites].map((id) => BY_ID.get(id)).filter(Boolean);
    section.replaceChildren(h('div.wrap', {},
      h('p.eyebrow', {}, 'Your collection'),
      h('h2', {}, '⭐ My Favorites'),
      h('p.lead', {}, items.length
        ? `You have saved ${items.length} exhibit(s). Tap one to open its display case.`
        : 'You have not saved any exhibits yet. Open an exhibit and tap "Add Favorite" to keep it here.'),
      items.length
        ? h('ul.cards', {}, ...items.map((item) => exhibitCard(item!)))
        : h('a.btn', { href: '#/catalog' }, 'Open the catalogue')));
  };

  render();
  document.addEventListener('visitor:changed', render, { once: true });
}
