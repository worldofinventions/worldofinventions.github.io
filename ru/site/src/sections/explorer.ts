// The card catalogue: every exhibit, with the bot's own search and filter rules.
import { INVENTIONS, HALLS, HALL_IDS, COUNTRIES, COUNTRY_INFO, PERIODS, countryLabel, pad3 } from '../data';
import { searchMatches, exhibitsWord, type Filters } from '../bot';
import { $, h, exhibitImage } from '../ui';

export function initExplorer(): void {
  const root = $('#explorer');
  const state: Filters & { q: string } = { q: '', hall: null, country: null, period: null };

  const select = (label: string, allLabel: string, key: 'hall' | 'country' | 'period', options: [string, string][]) => {
    const el = h('select', { id: `f-${key}` }, h('option', { value: '' }, allLabel),
      ...options.map(([value, text]) => h('option', { value }, text)));
    el.addEventListener('change', () => { state[key] = el.value || null; update(); });
    return { el, wrap: h('label.field', { for: `f-${key}` }, h('span', {}, label), el) };
  };
  const hall = select('Зал', 'Все залы', 'hall', HALL_IDS.map((id) => [id, `Зал ${id} · ${HALLS[id].title}`]));
  const country = select('Страна', 'Все страны', 'country', COUNTRIES.map((c) => [c, countryLabel(c)]));
  const period = select('Период', 'Все периоды', 'period', PERIODS.map((p) => [p, p]));
  const search = h('input', { id: 'f-q', type: 'search', placeholder: 'паровоз, Попов, 1957…', autocomplete: 'off', spellcheck: 'false', maxlength: 60 });
  search.addEventListener('input', () => { state.q = search.value; update(); });

  const count = h('p.explorer__count', { role: 'status', 'aria-live': 'polite' });
  const reset = h('button.btn.btn--ghost', { type: 'button' }, 'Сбросить фильтры');
  const list = h('ul.cards');
  const empty = h('div.explorer__empty', { hidden: true },
    h('p.explorer__empty-title', {}, 'В картотеке нет карточек с таким словом.'),
    h('p', {}, 'Попробуйте слово короче, другой век или другую страну.'),
    h('button.btn', { type: 'button', onclick: () => clear() }, 'Очистить поиск'));

  const cards = new Map(INVENTIONS.map((item) => [item.id,
    h('li.card', {},
      h('button.card__btn', { type: 'button', 'data-exhibit': item.id },
        h('span.card__head', {}, h('span', {}, `№ ${pad3(item.no)}`), h('span', {}, `Зал ${item.hall}`)),
        exhibitImage(item, 'thumb'),
        h('span.card__name', {}, item.name),
        h('span.card__row', {}, h('span', {}, item.year), h('span.card__flags', { 'aria-hidden': 'true' }, item.map_countries.map((c) => COUNTRY_INFO[c][0]).join(' '))),
        h('span.card__country', {}, item.country)))]));
  list.append(...cards.values());

  function clear(): void {
    Object.assign(state, { q: '', hall: null, country: null, period: null });
    search.value = '';
    [hall, country, period].forEach((f) => { f.el.value = ''; });
    update();
    search.focus();
  }
  reset.addEventListener('click', clear);

  function update(): void {
    const matches = new Set(searchMatches(state, state.q).map((item) => item.id));
    for (const [id, card] of cards) card.hidden = !matches.has(id);
    const active = Boolean(state.q.trim() || state.hall || state.country || state.period);
    count.textContent = matches.size === INVENTIONS.length
      ? `Все ${INVENTIONS.length} ${exhibitsWord(INVENTIONS.length)}`
      : `${matches.size} из ${INVENTIONS.length}`;
    reset.hidden = !active;
    empty.hidden = matches.size > 0;
    list.hidden = matches.size === 0;
  }

  root.append(
    h('form.explorer__bar', { role: 'search', onsubmit: (e: Event) => e.preventDefault() },
      h('label.field.field--search', { for: 'f-q' }, h('span', {}, 'Слово'), search),
      hall.wrap, country.wrap, period.wrap),
    h('div.explorer__status', {}, count, reset),
    list, empty);
  update();
}
