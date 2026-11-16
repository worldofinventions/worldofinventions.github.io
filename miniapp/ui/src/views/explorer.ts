// The card catalogue: the site's explorer, with the bot's own search and filter rules.
import { INVENTIONS, HALLS, HALL_IDS, COUNTRIES, PERIODS, countryLabel } from '../data';
import { searchMatches, type Filters } from '../bot';
import { h } from '../ui';
import { exhibitCard } from './card';

export function mountExplorer(root: HTMLElement): void {
  const holder = h('div');
  const state: Filters & { q: string } = { q: '', hall: null, country: null, period: null };

  const select = (label: string, key: 'hall' | 'country' | 'period', options: [string, string][]) => {
    const el = h('select', { id: `f-${key}` }, h('option', { value: '' }, `All ${label.toLowerCase()}s`.replace('countrys', 'countries')),
      ...options.map(([value, text]) => h('option', { value }, text)));
    el.addEventListener('change', () => { state[key] = el.value || null; update(); });
    return { el, wrap: h('label.field', { for: `f-${key}` }, h('span', {}, label), el) };
  };
  const hall = select('Hall', 'hall', HALL_IDS.map((id) => [id, `Hall ${id} · ${HALLS[id].title}`]));
  const country = select('Country', 'country', COUNTRIES.map((c) => [c, countryLabel(c)]));
  const period = select('Period', 'period', PERIODS.map((p) => [p, p]));
  const search = h('input', { id: 'f-q', type: 'search', placeholder: 'telescope, Faraday, 1876…', autocomplete: 'off', spellcheck: 'false', maxlength: 60 });
  search.addEventListener('input', () => { state.q = search.value; update(); });

  const count = h('p.explorer__count', { role: 'status', 'aria-live': 'polite' });
  const reset = h('button.btn.btn--ghost', { type: 'button' }, 'Reset filters');
  const list = h('ul.cards');
  const empty = h('div.explorer__empty', { hidden: true },
    h('p.explorer__empty-title', {}, 'Nothing in the drawers under that name.'),
    h('p', {}, 'The archivist suggests fewer letters, another century, or checking whether it has been invented yet.'),
    h('button.btn', { type: 'button', onclick: () => clear() }, 'Empty the search and start over'));

  const cards = new Map(INVENTIONS.map((item) => [item.id, exhibitCard(item)]));
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
      ? `All ${INVENTIONS.length} exhibits`
      : `${matches.size} of ${INVENTIONS.length} exhibits`;
    reset.hidden = !active;
    empty.hidden = matches.size > 0;
    list.hidden = matches.size === 0;
  }

  holder.append(
    h('form.explorer__bar', { role: 'search', onsubmit: (e: Event) => e.preventDefault() },
      h('label.field.field--search', { for: 'f-q' }, h('span', {}, 'Keyword'), search),
      hall.wrap, country.wrap, period.wrap),
    h('div.explorer__status', {}, count, reset),
    list, empty);

  root.append(h('section', {},
    h('div.wrap', {},
      h('p.eyebrow', {}, 'Card catalogue'),
      h('h2', {}, `All ${INVENTIONS.length} exhibits, one drawer`),
      h('p.lead', {}, 'Type a word, or narrow the drawer by hall, country and period, in any combination. Same fields searched, same spelling rules as in the bot.'),
      holder)));
  update();
}
