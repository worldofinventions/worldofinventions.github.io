// Personal statistics: the same numbers the bot's /stats screen shows,
// fetched live from the server when the view opens.
import { INVENTIONS, HALL_IDS } from '../data';
import { h } from '../ui';
import { api, type VisitorStats } from '../api';
import { state } from '../state';

function row(icon: string, label: string, value: string, bar?: number): HTMLElement {
  return h('div.stat', {},
    h('span.stat__icon', { 'aria-hidden': 'true' }, icon),
    h('div.stat__text', {},
      h('span.stat__label', {}, label),
      h('span.stat__value', {}, value),
      bar !== undefined ? h('span.stat__bar', { 'aria-hidden': 'true' }, h('i', { style: `width:${Math.round(bar * 100)}%` })) : null));
}

export async function mountStats(root: HTMLElement): Promise<void> {
  const section = h('section', {}, h('div.wrap', {}, h('p.eyebrow', {}, 'Your record'), h('h2', {}, '📊 Personal Statistics'), h('p.loading', {}, 'Opening the register…')));
  root.append(section);

  let stats: VisitorStats;
  try {
    stats = await api.stats();
    state.stats = stats;
  } catch (err) {
    section.querySelector('.loading')!.textContent = err instanceof Error ? err.message : 'Statistics are not available right now.';
    return;
  }

  const studied = Math.min(stats.studied_exhibits, INVENTIONS.length);
  const halls = Math.min(stats.opened_halls, HALL_IDS.length);
  const answers = stats.total_answers
    ? `${stats.correct_answers} of ${stats.total_answers} (${stats.accuracy ?? Math.round(100 * stats.correct_answers / stats.total_answers)}%)`
    : 'no quiz answers yet';

  section.querySelector('.wrap')!.replaceChildren(
    h('p.eyebrow', {}, 'Your record'),
    h('h2', {}, '📊 Personal Statistics'),
    h('div.stats', {},
      row('📚', 'Exhibits studied', `${studied} of ${INVENTIONS.length}`, studied / INVENTIONS.length),
      row('🏛', 'Halls opened', `${halls} of ${HALL_IDS.length}`, halls / HALL_IDS.length),
      row('⭐', 'Favorites saved', String(stats.favorites)),
      row('🧠', 'Correct quiz answers', answers),
      row('🏁', 'Quizzes completed', String(stats.quizzes_completed))),
    h('p.stats__note', {}, 'An exhibit counts as studied when you open it. The same numbers are shown in the bot.'));
}
