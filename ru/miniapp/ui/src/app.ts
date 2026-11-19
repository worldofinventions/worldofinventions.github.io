// The mini app entry point: Telegram bootstrap, visitor state, routing,
// the tab bar and the back button. The views themselves are ports of the
// site's sections; the display case (modal.ts) works across all of them.
// Шрифты с кириллицей: Literata (заголовки), Onest (текст), IBM Plex Mono (подписи).
import '@fontsource-variable/literata/opsz.css';
import '@fontsource-variable/literata/opsz-italic.css';
import '@fontsource-variable/onest/index.css';
import '@fontsource/ibm-plex-mono/cyrillic-400.css';
import '@fontsource/ibm-plex-mono/cyrillic-500.css';
import '@fontsource/ibm-plex-mono/latin-400.css';
import '@fontsource/ibm-plex-mono/latin-500.css';
import './styles/base.css';
import './styles/halls.css';
import './styles/sections.css';
import './styles/app.css';

import { $, tokenIcon, h, haptic, toast } from './ui';
import { api } from './api';
import { state, setFavorites } from './state';
import { initModal, vitrineOpen } from './modal';
import { mountHome } from './views/home';
import { mountHalls } from './views/halls';
import { mountExplorer } from './views/explorer';
import { mountMap } from './views/map';
import { mountToday } from './views/today';
import { mountQuiz } from './views/quiz';
import { mountFavorites } from './views/favorites';
import { mountStats } from './views/stats';
import { mountFeedback } from './views/feedback';
import { mountTeam, mountMore } from './views/team';

const tg = (window as any).Telegram?.WebApp ?? null;
if (tg) { try { tg.ready(); tg.expand(); } catch { /* not in Telegram */ } }

type Mount = (root: HTMLElement) => void | Promise<void>;

const ROUTES: Record<string, Mount> = {
  '': mountHome,
  halls: mountHalls,
  catalog: mountExplorer,
  map: mountMap,
  today: mountToday,
  quiz: mountQuiz,
  favorites: mountFavorites,
  stats: mountStats,
  feedback: mountFeedback,
  team: mountTeam,
  more: mountMore,
};

const TAB_OF: Record<string, string> = {
  '': 'home', halls: 'halls', catalog: 'catalog', map: 'map',
  today: 'more', quiz: 'more', favorites: 'more', stats: 'more',
  feedback: 'more', team: 'more', more: 'more',
};

const view = $('#view') as HTMLElement;
let currentRoute = '\0'; // forces the very first render
let renderToken = 0;

function routeFromHash(): string {
  return (location.hash || '#/').replace(/^#\/?/, '').split('/')[0] ?? '';
}

async function render(): Promise<void> {
  const route = routeFromHash();
  // The display case manages its own hash (#/exhibit/<id>): a change that
  // maps to the same view must not re-render and lose scroll or filters.
  if (route === currentRoute) { updateChrome(); return; }
  const mount = ROUTES[route];
  currentRoute = route;
  updateChrome();
  if (!mount) {
    view.replaceChildren();
    view.append(h('section', {}, h('div.wrap', {},
      h('p.eyebrow', {}, 'Вы заблудились'),
      h('h2', {}, 'Такого зала нет'),
      h('p.lead', {}, 'Кнопки внизу помогут вернуться.'),
      h('a.btn', { href: '#/' }, 'На главную'))));
    return;
  }
  const token = ++renderToken;
  try {
    const section = document.createElement('div');
    view.replaceChildren(section);
    await mount(section);
    if (token === renderToken) window.scrollTo(0, 0);
  } catch (err) {
    if (token !== renderToken) return;
    console.error(`View "${route}" failed`, err);
    view.replaceChildren();
    view.append(h('section', {}, h('div.wrap', {},
      h('p.eyebrow', {}, 'Погас свет'),
      h('h2', {}, 'Этот зал не открылся'),
      h('p.lead', {}, String(err instanceof Error ? err.message : err)),
      h('a.btn', { href: '#/' }, 'На главную'))));
  }
}

function updateChrome(): void {
  const route = routeFromHash();
  const tab = TAB_OF[route] ?? 'home';
  document.querySelectorAll('.tab').forEach((t) => t.classList.toggle('is-active', (t as HTMLElement).dataset.tab === tab));
  const atHome = route === '' && !vitrineOpen();
  try { if (tg?.BackButton) (atHome ? tg.BackButton.hide() : tg.BackButton.show()); } catch { /* ignore */ }
}

// Telegram's hardware-style back button: close the display case first, then leave the view.
tg?.BackButton?.onClick?.(() => {
  const openDialog = document.querySelector('dialog[open]') as HTMLDialogElement | null;
  if (openDialog) { openDialog.close(); return; }
  haptic('impact', 'light');
  if (routeFromHash() !== '') history.back();
});

document.addEventListener('vitrine:closed', updateChrome);

// Lights follow Telegram's color scheme, and can still be overridden via the stored choice.
function applyScheme(): void {
  const scheme: string | undefined = tg?.colorScheme;
  if (scheme === 'light' || scheme === 'dark') document.documentElement.dataset.theme = scheme;
}
tg?.onEvent?.('themeChanged', applyScheme);
applyScheme();

/** start_param: t.me/<bot>?startapp=<payload> opens the app on that screen. */
function applyStartParam(): void {
  const sp: string | undefined = tg?.initDataUnsafe?.start_param;
  if (!sp) return;
  const map: Record<string, string> = {
    museum: '', halls: 'halls', catalog: 'catalog', catalogue: 'catalog', favorites: 'favorites',
    stats: 'stats', today: 'today', map: 'map', search: 'catalog', quiz: 'quiz',
    feedback: 'feedback', team: 'team',
  };
  let target = map[sp];
  if (target === undefined && /^hall[1-4]$/.test(sp)) target = 'halls';
  if (target === undefined && sp.startsWith('item_')) target = 'catalog';
  if (target !== undefined) {
    const hash = target ? `#/${target}` : '#/';
    if (location.hash !== hash) location.hash = hash;
    currentRoute = '\0'; // force a render of the target view
  }
}

window.addEventListener('hashchange', () => { render(); });

(async function init(): Promise<void> {
  $('#nav-token').append(tokenIcon(28));
  try {
    const boot = await api.bootstrap();
    state.user = boot.user;
    setFavorites(boot.favorites);
    state.stats = boot.stats;
    const user = $('#nav-user') as HTMLElement;
    user.textContent = boot.user.name;
    user.removeAttribute('aria-hidden');
  } catch (err) {
    console.error('Bootstrap failed', err);
    toast(err instanceof Error ? err.message : 'Музей не загрузился');
  }
  initModal();
  applyStartParam();
  render();
})();
