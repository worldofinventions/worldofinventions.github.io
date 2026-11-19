// The accession register: the collection in numbers, each one counted from the data.
import gsap from 'gsap';
import { STATS } from '../data';
import { $, h, reducedMotion, whenVisible } from '../ui';

/** Слово после числа: 1 год, 2 года, 5 лет. */
const word = (n: number, one: string, few: string, many: string): string =>
  n % 10 === 1 && n % 100 !== 11 ? one : n % 10 >= 2 && n % 10 <= 4 && !(n % 100 >= 12 && n % 100 <= 14) ? few : many;

export function initLedger(): void {
  const rows: [number, string, string][] = [
    [STATS.exhibits, `${word(STATS.exhibits, 'экспонат', 'экспоната', 'экспонатов')} в залах`, 'inventions.json'],
    [STATS.halls, `${word(STATS.halls, 'зал', 'зала', 'залов')}, по одному на эпоху`, 'HALLS в handlers.py'],
    [STATS.span, `${word(STATS.span, 'год', 'года', 'лет')} истории, от ${STATS.yearMin} до ${STATS.yearMax} года`, 'первый и последний экспонат'],
    [STATS.events, `${word(STATS.events, 'дата', 'даты', 'дат')} в календаре`, 'history.json'],
    [STATS.questions, `${word(STATS.questions, 'вопрос', 'вопроса', 'вопросов')} в банке викторины`, 'QUIZ в handlers.py'],
  ];
  const list = $('#ledger-rows');
  const cells: { el: HTMLElement; value: number; width: number }[] = [];
  list.replaceChildren(...rows.map(([value, label, source], i) => {
    const digits = h('span.ledger__digits', { 'aria-hidden': 'true' });
    cells.push({ el: digits, value, width: String(value).length });
    return h('li.ledger__row', {},
      h('span.ledger__line', { 'aria-hidden': 'true' }, `С.${i + 1}`),
      h('span.ledger__value', {}, h('span.sr-only', {}, String(value)), digits),
      h('span.ledger__label', {}, label),
      h('span.ledger__src', {}, source));
  }));
  const paint = (cell: (typeof cells)[number], n: number) => {
    cell.el.replaceChildren(...String(Math.round(n)).padStart(cell.width, '0').split('').map((d) => h('span.flap', {}, d)));
  };
  cells.forEach((cell) => paint(cell, cell.value));
  if (reducedMotion()) return;
  cells.forEach((cell) => paint(cell, 0));
  whenVisible(list, () => {
    cells.forEach((cell, i) => {
      const state = { n: 0 };
      gsap.to(state, { n: cell.value, duration: 1.3, delay: i * 0.12, ease: 'power2.out', onUpdate: () => paint(cell, state.n), onComplete: () => paint(cell, cell.value) });
    });
  }, '-40px');
}
