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
  const section = h('section', {}, h('div.wrap', {}, h('p.eyebrow', {}, 'Ваши успехи'), h('h2', {}, '📊 Личная статистика'), h('p.loading', {}, 'Открываю журнал…')));
  root.append(section);

  let stats: VisitorStats;
  try {
    stats = await api.stats();
    state.stats = stats;
  } catch (err) {
    section.querySelector('.loading')!.textContent = err instanceof Error ? err.message : 'Статистика сейчас недоступна.';
    return;
  }

  const studied = Math.min(stats.studied_exhibits, INVENTIONS.length);
  const halls = Math.min(stats.opened_halls, HALL_IDS.length);
  const answers = stats.total_answers
    ? `${stats.correct_answers} из ${stats.total_answers} (${stats.accuracy ?? Math.round(100 * stats.correct_answers / stats.total_answers)}%)`
    : 'пока нет ответов';

  section.querySelector('.wrap')!.replaceChildren(
    h('p.eyebrow', {}, 'Ваши успехи'),
    h('h2', {}, '📊 Личная статистика'),
    h('div.stats', {},
      row('📚', 'Изучено экспонатов', `${studied} из ${INVENTIONS.length}`, studied / INVENTIONS.length),
      row('🏛', 'Открыто залов', `${halls} из ${HALL_IDS.length}`, halls / HALL_IDS.length),
      row('⭐', 'В избранном', String(stats.favorites)),
      row('🧠', 'Верных ответов в викторине', answers),
      row('🏁', 'Пройдено викторин', String(stats.quizzes_completed))),
    h('p.stats__note', {}, 'Экспонат считается изученным, когда вы его открываете. Те же цифры показывает бот.'));
}
