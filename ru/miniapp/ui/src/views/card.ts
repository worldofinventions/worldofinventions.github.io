// The catalogue card, shared by the catalogue, favorites and the home screen.
import { COUNTRY_INFO, pad3, type Exhibit } from '../data';
import { h, exhibitImage } from '../ui';

export function exhibitCard(item: Exhibit): HTMLElement {
  return h('li.card', {},
    h('button.card__btn', { type: 'button', 'data-exhibit': item.id },
      h('span.card__head', {}, h('span', {}, `№ ${pad3(item.no)}`), h('span', {}, `Зал ${item.hall}`)),
      exhibitImage(item, 'thumb'),
      h('span.card__name', {}, item.name),
      h('span.card__row', {}, h('span', {}, item.year), h('span.card__flags', { 'aria-hidden': 'true' }, item.map_countries.map((c) => COUNTRY_INFO[c][0]).join(' '))),
      h('span.card__country', {}, item.country)));
}
