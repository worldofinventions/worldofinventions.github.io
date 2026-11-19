// This Day in History: the site's calendar, run through the bot's rules (bot.ts buildHistory).
import { MONTH_NAMES, eraOf } from '../data';
import { buildHistory, type DayRef } from '../bot';
import { h } from '../ui';

const WEEKDAYS = ['воскресенье', 'понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота'];
const KINDS: Record<string, string> = { invention: 'изобретение', discovery: 'открытие', milestone: 'событие' };
const MONTHS_NOMINATIVE = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь'];
const pad = (n: number) => String(n).padStart(2, '0');
const toRef = (d: Date): DayRef => ({ year: d.getFullYear(), month: d.getMonth() + 1, day: d.getDate() });
const iso = (r: DayRef) => `${r.year}-${pad(r.month)}-${pad(r.day)}`;

export function mountToday(root: HTMLElement): void {
  const now = new Date();
  let date = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const isToday = () => iso(toRef(date)) === iso(toRef(new Date()));

  const leaf = h('div.leaf', { 'aria-hidden': 'true' });
  const picker = h('input', { id: 'today-date', type: 'date', 'aria-label': 'Выберите дату' });
  const back = h('button.btn.btn--ghost', { type: 'button', hidden: true }, 'Вернуться к сегодня');
  const heading = h('h3.today__heading', { tabindex: -1 });
  const lead = h('p.today__lead');
  const list = h('ol.clippings');
  const shift = (days: number) => { date = new Date(date.getFullYear(), date.getMonth(), date.getDate() + days); render(true); };

  picker.addEventListener('change', () => {
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(picker.value);
    if (m) { date = new Date(+m[1], +m[2] - 1, +m[3]); render(true); }
  });
  back.addEventListener('click', () => { const t = new Date(); date = new Date(t.getFullYear(), t.getMonth(), t.getDate()); render(true); });

  function render(animate = false): void {
    const ref = toRef(date);
    const result = buildHistory(ref);
    const month = MONTH_NAMES[ref.month - 1];
    picker.value = iso(ref);
    back.hidden = isToday();
    leaf.replaceChildren(
      h('span.leaf__month', {}, MONTHS_NOMINATIVE[ref.month - 1]), h('span.leaf__day', {}, String(ref.day)), h('span.leaf__week', {}, `${WEEKDAYS[date.getDay()]}, ${ref.year}`));
    if (animate) { leaf.classList.remove('is-torn'); void leaf.offsetWidth; leaf.classList.add('is-torn'); }
    heading.textContent = `${isToday() ? 'Сегодня, ' : ''}${ref.day} ${month}`;
    lead.textContent = result.exact
      ? `Записей в календаре музея на эту дату: ${result.entries.length}.`
      : 'В нашем календаре нет события ровно на эту дату. Ближайшие:';
    list.replaceChildren(...result.entries.map(({ event, dayLabel, when }) => {
      const exhibitId = event.related_id ?? undefined;
      return h('li.clipping', { 'data-era': eraOf(event.year) },
        h('p.clipping__meta', {}, h('span.clipping__kind', {}, KINDS[event.kind] ?? event.kind), h('span', {}, `${dayLabel} ${event.year}`), when ? h('span.clipping__when', {}, when) : null),
        h('h4.clipping__title', {}, event.title),
        h('p.clipping__text', {}, event.text),
        exhibitId ? h('button.clipping__link', { type: 'button', 'data-exhibit': exhibitId }, 'Открыть экспонат') : null);
    }));
  }

  root.append(h('section', {},
    h('div.wrap', {},
      h('p.eyebrow', {}, 'Этот день в истории'),
      h('h2', {}, 'Что случилось в этот день'),
      h('p.lead', {}, 'В календаре изобретения, открытия и события с точными датами. Если на сегодня записей нет, он, как и бот, показывает ближайшие даты до и после.'),
      h('div.today__grid', {},
        h('div.today__cal', {},
          h('div.leaf-stack', {}, leaf),
          h('div.today__nav', {},
            h('button.btn.btn--ghost', { type: 'button', onclick: () => shift(-1) }, 'Предыдущий день'),
            h('button.btn.btn--ghost', { type: 'button', onclick: () => shift(1) }, 'Следующий день')),
          h('label.field', { for: 'today-date' }, h('span', {}, 'Перейти к дате'), picker),
          back),
        h('div.today__events', { 'aria-live': 'polite' }, heading, lead, list)))));
  render();
}
