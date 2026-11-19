// The entrance hall of the app: everything is one tap away.
import { INVENTIONS, HALLS } from '../data';
import { h } from '../ui';
import { state } from '../state';
import { exhibitsWord } from '../bot';

const tile = (href: string, icon: string, name: string, sub: string): HTMLElement =>
  h('a.tile', { href },
    h('span.tile__ico', { 'aria-hidden': 'true' }, icon),
    h('span.tile__text', {}, h('b', {}, name), h('small', {}, sub)));

export function mountHome(root: HTMLElement): void {
  const stats = state.stats;
  const studied = stats ? Math.min(stats.studied_exhibits, INVENTIONS.length) : null;
  const halls = Object.keys(HALLS).length;
  const name = state.user?.name ?? 'гость';

  root.append(h('section.view-home', {},
    h('div.wrap', {},
      h('p.eyebrow', {}, 'Музей изобретений русских людей'),
      h('h2', {}, `Здравствуйте, ${name.split(' ')[0]}`),
      h('p.lead', {},
        `${INVENTIONS.length} ${exhibitsWord(INVENTIONS.length)} в ${halls} залах, от глаголицы до графена. `
        + 'Избранное, прогресс и результаты викторины сохраняются в вашем аккаунте Telegram '
        + 'и совпадают с тем, что показывает бот.'),
      h('p.home__chips', {},
        studied !== null ? h('span.home__chip', {}, `📚 изучено ${studied} из ${INVENTIONS.length}`) : null,
        h('span.home__chip', {}, `⭐ в избранном: ${state.favorites.size}`)),
      h('div.tiles', {},
        tile('#/halls', '🏺', 'Залы музея', `${halls} зала на одной линии времени`),
        tile('#/catalog', '📚', 'Каталог', 'поиск и фильтры'),
        tile('#/map', '🗺', 'Карта изобретений', 'по странам'),
        tile('#/today', '📅', 'Этот день в истории', 'изобретения и открытия по датам'),
        tile('#/quiz', '🧠', 'Викторина', '10 вопросов в раунде'),
        tile('#/favorites', '⭐', 'Избранное', `сохранено: ${state.favorites.size}`),
        tile('#/stats', '📊', 'Статистика', 'ваши успехи'),
        tile('#/feedback', '💬', 'Отзыв', 'идеи и исправления'),
        tile('#/team', '👥', 'Команда', 'кураторы проекта')))));
}
