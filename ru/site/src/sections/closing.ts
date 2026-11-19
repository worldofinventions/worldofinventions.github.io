// The curators' plaque and the footer credits.
import { TEAM, REPO_URL, WORLD_SITE_URL } from '../config';
import { INVENTIONS, MUSEUM_NAME, STATS } from '../data';
import { $, h } from '../ui';

export function initTeam(): void {
  const root = $('#team-plaque');
  if (!TEAM.length) {
    root.append(h('p.plaque__empty', {}, 'Имена ещё гравируются.'), h('p.plaque__sub', {}, 'Табличка ждёт своих кураторов.'));
    return;
  }
  root.append(h('ul.plaque__list', { 'data-count': Math.min(TEAM.length, 8) }, ...TEAM.map((m) => {
    const initials = m.name.split(/\s+/).map((w) => w[0]).slice(0, 2).join('').toUpperCase();
    const portrait = m.photo
      ? h('img.plaque__photo', { src: m.photo, alt: `Портрет: ${m.name}`, width: 96, height: 96, loading: 'lazy' })
      : h('span.plaque__photo.plaque__photo--blank', { 'aria-hidden': 'true' }, initials);
    const name = m.link ? h('a', { href: m.link, target: '_blank', rel: 'noopener' }, m.name) : m.name;
    return h('li.plaque__person', {}, portrait, h('span.plaque__name', {}, name), h('span.plaque__role', {}, m.role));
  })));
}

export function initFooter(): void {
  const withImage = INVENTIONS.filter((item) => item.image);
  const credits = h('ul.credits', {}, ...withImage.map((item) => {
    const img = item.image!;
    return h('li', {},
      img.page ? h('a', { href: img.page, target: '_blank', rel: 'noopener' }, item.name) : item.name,
      [img.artist, img.license, item.image_credit].filter(Boolean).map((x) => `, ${x}`).join(''));
  }));
  const seen = new Map<string, string>();
  for (const item of INVENTIONS) for (const src of item.sources) if (!seen.has(src.url)) seen.set(src.url, src.title);
  const sources = h('ul.credits', {}, ...[...seen].sort((a, b) => a[1].localeCompare(b[1])).map(([url, title]) =>
    h('li', {}, h('a', { href: url, target: '_blank', rel: 'noopener' }, title))));

  $('#footer-credits').append(
    h('details', {}, h('summary', {}, `Авторы фотографий (${withImage.length})`),
      h('p', {}, `Фотографии есть у ${withImage.length} из ${STATS.exhibits} экспонатов, у остальных пока гравированная табличка. Ссылки, авторы и лицензии взяты с Wikimedia Commons.`),
      credits),
    h('details', {}, h('summary', {}, `Источники текстов (${seen.size})`), sources),
    h('details', {}, h('summary', {}, 'О сайте'),
      h('p', {}, 'Шрифты Literata, Onest и IBM Plex Mono (SIL Open Font License). Флаги: Twemoji, CC BY 4.0.')));

  const meta = $('#footer-meta');
  meta.append(h('span', {}, `© ${new Date().getFullYear()} ${MUSEUM_NAME}. Образовательный проект Ломоносовской школы-пансиона.`));
  meta.append(h('a', { href: WORLD_SITE_URL, target: '_blank', rel: 'noopener' }, 'World of Inventions: музей изобретений мира (на английском)'));
  if (REPO_URL) meta.append(h('a', { href: REPO_URL, target: '_blank', rel: 'noopener' }, 'Исходный код'));
}
