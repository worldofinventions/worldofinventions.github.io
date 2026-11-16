// The Halls: the site's room with plinths, ported as an app view.
// On phone-sized screens the rooms stack vertically (the site's own narrow layout).
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { HALLS, HALL_IDS, hallItemsByYear, pad3 } from '../data';
import { $, h, exhibitImage } from '../ui';
import { api } from '../api';

gsap.registerPlugin(ScrollTrigger);

const MORSE: Record<string, string> = {
  a: '.-', b: '-...', c: '-.-.', d: '-..', e: '.', f: '..-.', g: '--.', h: '....', i: '..', j: '.---', k: '-.-', l: '.-..', m: '--',
  n: '-.', o: '---', p: '.--.', q: '--.-', r: '.-.', s: '...', t: '-', u: '..-', v: '...-', w: '.--', x: '-..-', y: '-.--', z: '--..',
};
const toMorse = (text: string) => text.toLowerCase().split('').map((c) => (c === ' ' ? '/' : MORSE[c] ?? '')).filter(Boolean).join(' ').replace(/\./g, '•').replace(/-/g, '▬');

const ASIDES = [
  'Mind the candle wax on the floor.',
  'Please do not feed the engines.',
  'The warm glow is the valves waking up.',
  'No flash photography. The exhibits flash back.',
];

export function mountHalls(root: HTMLElement): void {
  root.append(h('section.halls', {},
    h('div.wrap.section-head', {},
      h('p.eyebrow', {}, 'Permanent exhibition'),
      h('h2', {}, 'Every invention has a room. Every room has a century.'),
      h('p.lead', {}, `${HALL_IDS.length} halls stand on one timeline, from candlelight to screen glow. Stop at any plinth to open its display case.`)),
    h('div.halls__stage', { id: 'halls-stage' },
      h('div.halls__hud', {},
        h('p.halls__now', { id: 'halls-hud-name' }),
        h('div.halls__jumps', { id: 'halls-jumps', role: 'group', 'aria-label': 'Jump to a hall' })),
      h('div.halls__track', { id: 'halls-track' }),
      h('div.halls__progress', { id: 'halls-progress', 'aria-hidden': 'true' }))));

  const stage = $('#halls-stage');
  const track = $('#halls-track');
  const hudName = $('#halls-hud-name');
  const jumps = $('#halls-jumps');
  const progress = $('#halls-progress');

  // Opening the halls screen means the visitor sees the rooms: count them as opened.
  for (const id of HALL_IDS) api.markHall(id).catch(() => { });

  const rooms = HALL_IDS.map((id, n) => {
    const hall = HALLS[id];
    const items = hallItemsByYear(id);
    const wall = h('ol.room__wall', { style: `--n:${items.length}` },
      ...items.map((item, i) =>
        h('li.plinth', { class: i % 2 ? 'plinth--low' : 'plinth--high', style: `--i:${i}` },
          h('button.plinth__btn', { type: 'button', 'data-exhibit': item.id },
            exhibitImage(item, 'thumb'),
            h('span.plinth__cap', {}, h('span.plinth__no', {}, `No. ${pad3(item.no)}`), h('span.plinth__name', {}, item.name), h('span.sr-only', {}, `, ${item.year}`))),
          h('span.plinth__year', { 'aria-hidden': 'true' }, item.year))));
    if (id === HALL_IDS[1]) wall.dataset.tape = `${toMorse(hall.name)}   `.repeat(10);
    const room = h('section.room', { 'data-hall': id, 'aria-labelledby': `room-${id}` },
      h('div.room__intro', {},
        h('p.room__no', {}, `Hall ${id}`),
        h('h3.room__name', { id: `room-${id}` }, hall.name),
        h('p.room__period', {}, hall.title),
        h('p.room__desc', {}, hall.description),
        h('p.room__meta', {}, `${items.length} exhibits · ${items[0]?.year ?? ''} to ${items[items.length - 1]?.year ?? ''}`),
        h('p.room__aside', {}, ASIDES[n % ASIDES.length])),
      h('div.room__gallery', {}, wall));
    track.append(room);
    return room;
  });

  const segs = HALL_IDS.map((id) => h('span.halls__seg', { 'data-hall': id }, h('i', {}, HALLS[id].title)));
  const marker = h('span.halls__marker');
  progress.append(...segs, marker);

  let st: ScrollTrigger | null = null;
  const maxShift = () => Math.max(0, track.scrollWidth - stage.clientWidth);
  const scrollToX = (x: number) => {
    if (!st) return;
    const max = maxShift();
    const p = max ? Math.min(1, Math.max(0, x / max)) : 0;
    window.scrollTo({ top: st.start + p * (st.end - st.start), behavior: 'smooth' });
  };

  jumps.append(...HALL_IDS.map((id, i) =>
    h('button', {
      type: 'button', 'data-hall': id, 'aria-label': `Go to Hall ${id}: ${HALLS[id].name}`,
      onclick: () => (st ? scrollToX(rooms[i].offsetLeft) : rooms[i].scrollIntoView({ behavior: 'smooth' })),
    }, id)));

  const setActive = (id: string) => {
    if (stage.dataset.hall === id) return;
    stage.dataset.hall = id;
    hudName.textContent = `Hall ${id} · ${HALLS[id].name} · ${HALLS[id].title}`;
    jumps.querySelectorAll('button').forEach((b) => b.toggleAttribute('aria-current', b.dataset.hall === id));
  };
  setActive(HALL_IDS[0]);

  const layoutProgress = () => {
    const total = track.scrollWidth || 1;
    rooms.forEach((room, i) => { segs[i].style.flexGrow = String(room.offsetWidth / total); });
  };

  const mm = gsap.matchMedia();
  mm.add('(min-width: 960px) and (min-height: 600px) and (prefers-reduced-motion: no-preference)', () => {
    stage.classList.add('is-horizontal');
    layoutProgress();
    const tween = gsap.to(track, {
      x: () => -maxShift(),
      ease: 'none',
      scrollTrigger: {
        trigger: stage,
        pin: true,
        scrub: 0.5,
        start: () => 'top 0px',
        end: () => `+=${maxShift()}`,
        invalidateOnRefresh: true,
        onRefresh: layoutProgress,
        onUpdate: (self) => {
          const centre = self.progress * maxShift() + stage.clientWidth / 2;
          const room = [...rooms].reverse().find((r) => r.offsetLeft <= centre) ?? rooms[0];
          setActive(room.dataset.hall!);
          marker.style.transform = `translateX(${(self.progress * progress.clientWidth).toFixed(1)}px)`;
        },
      },
    });
    st = tween.scrollTrigger!;
    const onFocus = (e: FocusEvent) => {
      const target = (e.target as HTMLElement).closest<HTMLElement>('.plinth, .room__intro');
      if (!target || !st) return;
      stage.scrollLeft = 0;
      const box = target.getBoundingClientRect();
      if (box.left >= 40 && box.right <= innerWidth - 40) return;
      const x = box.left - track.getBoundingClientRect().left;
      scrollToX(x - stage.clientWidth / 2 + box.width / 2);
    };
    track.addEventListener('focusin', onFocus);
    return () => {
      track.removeEventListener('focusin', onFocus);
      stage.classList.remove('is-horizontal');
      st = null;
    };
  });

  const io = new IntersectionObserver((entries) => {
    if (st) return;
    for (const e of entries) if (e.isIntersecting) setActive((e.target as HTMLElement).dataset.hall!);
  }, { rootMargin: '-45% 0px -45% 0px' });
  rooms.forEach((room) => io.observe(room));

  stage.addEventListener('pointermove', (e) => {
    const box = stage.getBoundingClientRect();
    stage.style.setProperty('--mx', `${e.clientX - box.left}px`);
    stage.style.setProperty('--my', `${e.clientY - box.top}px`);
  });

  document.fonts?.ready.then(() => ScrollTrigger.refresh());
  window.addEventListener('load', () => ScrollTrigger.refresh());
}
