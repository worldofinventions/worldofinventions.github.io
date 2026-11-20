// The curators' plaque and the "More" hall of services.
import { h } from '../ui';
import { TEAM, WORLD_BOT_URL, SITE_URL } from '../config';
import { state } from '../state';

export function mountTeam(root: HTMLElement): void {
  const plaque = h('div');
  if (!TEAM.length) {
    plaque.append(h('p.plaque__empty', {}, 'Имена ещё гравируются.'), h('p.plaque__sub', {}, 'Табличка ждёт своих кураторов.'));
  } else {
    plaque.append(h('ul.plaque__list', { 'data-count': Math.min(TEAM.length, 8) }, ...TEAM.map((m) => {
      const initials = m.name.split(/\s+/).map((w) => w[0]).slice(0, 2).join('').toUpperCase();
      const portrait = m.photo
        ? h('img.plaque__photo', { src: m.photo, alt: `Портрет: ${m.name}`, width: 96, height: 96, loading: 'lazy' })
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
        h('h2', {}, 'Кураторы выставки'),
        plaque,
        h('p.plaque__sub', {}, 'Образовательный проект Ломоносовской школы-пансиона'),
        h('p.plaque__sub', {}, h('a', { href: SITE_URL, target: '_blank', rel: 'noopener' }, 'Сайт музея'), ' · ', h('a', { href: WORLD_BOT_URL, target: '_blank', rel: 'noopener' }, 'World of Inventions, музей изобретений мира (на английском)'))))));
}

const tile = (href: string, icon: string, name: string, sub: string): HTMLElement =>
  h('a.tile', { href },
    h('span.tile__ico', { 'aria-hidden': 'true' }, icon),
    h('span.tile__text', {}, h('b', {}, name), h('small', {}, sub)));

export function mountMore(root: HTMLElement): void {
  root.append(h('section', {},
    h('div.wrap', {},
      h('p.eyebrow', {}, 'Остальное'),
      h('h2', {}, '☰ Ещё'),
      h('p.lead', {}, 'Ваша коллекция, успехи, календарь и связь с командой.'),
      h('div.tiles', {},
        tile('#/today', '📅', 'Этот день в истории', 'изобретения и открытия по датам'),
        tile('#/favorites', '⭐', 'Избранное', `сохранено: ${state.favorites.size}`),
        tile('#/stats', '📊', 'Статистика', 'ваши успехи'),
        tile('#/feedback', '💬', 'Отзыв', 'идеи и исправления'),
        tile('#/team', '👥', 'Команда', 'кураторы проекта'),
        worldTile()))));
}

/** Плитка соседнего музея: открывает бота World of Inventions в Telegram. */
function worldTile(): HTMLElement {
  const tg = (window as any).Telegram?.WebApp ?? null;
  return h('a.tile', {
    href: WORLD_BOT_URL, target: '_blank', rel: 'noopener',
    onclick: (e: Event) => { if (tg?.openTelegramLink) { e.preventDefault(); tg.openTelegramLink(WORLD_BOT_URL); } },
  },
    h('span.tile__ico', { 'aria-hidden': 'true' }, '🌍'),
    h('span.tile__text', {}, h('b', { lang: 'en' }, 'World of Inventions · Global'), h('small', {}, 'соседний музей: изобретения мира, на английском')));
}
