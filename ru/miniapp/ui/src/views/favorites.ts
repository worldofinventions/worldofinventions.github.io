// My Favorites: the visitor's saved exhibits, straight from the server.
import { BY_ID } from '../data';
import { h } from '../ui';
import { state } from '../state';
import { exhibitCard } from './card';
import { exhibitsWord } from '../bot';

export function mountFavorites(root: HTMLElement): void {
  const section = h('section', {});
  root.append(section);

  const render = (): void => {
    const items = [...state.favorites].map((id) => BY_ID.get(id)).filter(Boolean);
    section.replaceChildren(h('div.wrap', {},
      h('p.eyebrow', {}, 'Ваша коллекция'),
      h('h2', {}, '⭐ Избранное'),
      h('p.lead', {}, items.length
        ? `Сохранено: ${items.length} ${exhibitsWord(items.length)}. Нажмите, чтобы открыть витрину.`
        : 'Вы пока ничего не сохранили. Откройте экспонат и нажмите «В избранное».'),
      items.length
        ? h('ul.cards', {}, ...items.map((item) => exhibitCard(item!)))
        : h('a.btn', { href: '#/catalog' }, 'Открыть каталог')));
  };

  render();
  document.addEventListener('visitor:changed', render, { once: true });
}
