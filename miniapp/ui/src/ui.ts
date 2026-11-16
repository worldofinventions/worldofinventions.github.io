// Small DOM helpers shared by every view — the site's ui.ts adapted for the
// mini app: exhibit photos come from the mini app server, and the "open in the
// bot" links are replaced by in-app navigation.
import { pad3, altText } from './data';

type Child = Node | string | null | undefined | false;
type Attrs = Record<string, string | number | boolean | null | undefined | ((e: any) => void)>;

/** Hyperscript: h('button.plinth', { type: 'button', onclick }, child, ...) */
export function h<K extends keyof HTMLElementTagNameMap>(spec: K | `${K}.${string}`, attrs: Attrs = {}, ...children: Child[]): HTMLElementTagNameMap[K] {
  const [tag, ...classes] = spec.split('.');
  const el = document.createElement(tag) as HTMLElementTagNameMap[K];
  if (classes.length) el.className = classes.join(' ');
  for (const [key, value] of Object.entries(attrs)) {
    if (value == null || value === false) continue;
    if (typeof value === 'function') el.addEventListener(key.replace(/^on/, ''), value as EventListener);
    else if (key === 'class') el.className += ` ${value}`;
    else el.setAttribute(key, value === true ? '' : String(value));
  }
  el.append(...(children.filter((c) => c != null && c !== false) as (Node | string)[]));
  return el;
}

const SVG_NS = 'http://www.w3.org/2000/svg';
export function s(tag: string, attrs: Record<string, string | number | null | undefined> = {}, ...children: (Node | string)[]): SVGElement {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attrs)) if (value != null) el.setAttribute(key, String(value));
  el.append(...children);
  return el;
}

export const $ = <T extends Element = HTMLElement>(sel: string, root: ParentNode = document): T => {
  const el = root.querySelector<T>(sel);
  if (!el) throw new Error(`Missing element: ${sel}`);
  return el;
};
export const reducedMotion = (): boolean => matchMedia('(prefers-reduced-motion: reduce)').matches;

/** Run `fn` once, the first time `el` comes near the viewport. */
export function whenVisible(el: Element, fn: () => void, rootMargin = '200px'): void {
  if (!('IntersectionObserver' in window)) { fn(); return; }
  const io = new IntersectionObserver((entries) => {
    if (entries.some((e) => e.isIntersecting)) { io.disconnect(); fn(); }
  }, { rootMargin });
  io.observe(el);
}

export function arrowIcon(): SVGElement {
  return s('svg', { viewBox: '0 0 16 16', width: 14, height: 14, 'aria-hidden': 'true', class: 'icon-arrow' },
    s('path', { d: 'M3 13 13 3M6 3h7v7', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.5 }));
}

// ------------------------------------------------------------------ exhibit images
const widthUrl = (url: string, width: number) => url.replace(/width=\d+/, `width=${width}`);

/** The engraved plate that stands in for a missing or broken photograph. */
export function plate(item: import('./data').Exhibit, variant: 'thumb' | 'full'): HTMLElement {
  const a11y = variant === 'full' ? { role: 'img', 'aria-label': `${item.name}: no photograph, the exhibit is being restored` } : { 'aria-hidden': 'true' };
  return h('div.plate', a11y,
    h('span.plate__no', { 'aria-hidden': 'true' }, pad3(item.no)),
    variant === 'full'
      ? h('span.plate__note', { 'aria-hidden': 'true' }, 'This exhibit is being restored')
      : h('span.plate__note', { 'aria-hidden': 'true' }, 'plate in restoration'));
}

/** A framed exhibit picture with lazy loading, reserved space and a graceful fallback.
 *  The mini app server serves the site's own copies of the photographs
 *  (`/exhibits/<id>.jpg` and the 330px thumbs), the remote URL is the fallback. */
export function exhibitImage(item: import('./data').Exhibit, variant: 'thumb' | 'full'): HTMLElement {
  const frame = h('div.frame', { class: `frame--${variant}` });
  if (!item.image_url) {
    frame.classList.add('frame--plate');
    frame.append(plate(item, variant));
    return frame;
  }
  const width = item.image?.width ?? 900;
  const height = item.image?.height ?? Math.round(width * 0.75);
  const img = h('img', {
    alt: variant === 'full' ? altText(item) : '',
    loading: 'lazy',
    decoding: 'async',
    width: variant === 'thumb' ? 330 : width,
    height: variant === 'thumb' ? Math.round((330 * height) / width) : height,
    src: variant === 'thumb' ? `exhibits/thumb/${item.id}.jpg` : `exhibits/${item.id}.jpg`,
  });
  if (item.image && /\.svg$/i.test(item.image.file)) frame.classList.add('frame--logo');
  frame.classList.add('is-loading');
  img.addEventListener('load', () => frame.classList.remove('is-loading'));
  img.addEventListener('error', () => {
    if (!img.dataset.fallback) {
      img.dataset.fallback = '1';
      img.src = variant === 'thumb' ? widthUrl(item.image_url!, 330) : item.image_url!;
      return;
    }
    frame.classList.remove('is-loading');
    frame.classList.add('frame--plate');
    frame.replaceChildren(plate(item, variant));
  });
  frame.append(img);
  return frame;
}

// ------------------------------------------------------------------ Telegram helpers
const tg = (window as any).Telegram?.WebApp ?? null;

export function haptic(type: 'impact' | 'notify' | 'select', value = 'light'): void {
  try {
    if (!tg?.HapticFeedback) return;
    if (type === 'impact') tg.HapticFeedback.impactOccurred(value);
    else if (type === 'notify') tg.HapticFeedback.notificationOccurred(value);
    else tg.HapticFeedback.selectionChanged();
  } catch { /* not inside Telegram */ }
}

let toastTimer = 0;
export function toast(text: string): void {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = text;
  el.classList.add('is-shown');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('is-shown'), 2200) as unknown as number;
}

/** The round museum token used as the logo and the favicon. */
export function tokenIcon(size = 28): SVGElement {
  return s('svg', { viewBox: '0 0 64 64', width: size, height: size, 'aria-hidden': 'true', class: 'token' },
    s('circle', { cx: 32, cy: 32, r: 30, fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }),
    s('circle', { cx: 32, cy: 32, r: 24.5, fill: 'none', stroke: 'currentColor', 'stroke-width': 1, 'stroke-dasharray': '1.5 3' }),
    s('circle', { cx: 32, cy: 9.5, r: 2.4, fill: 'currentColor' }),
    s('path', { d: 'M17 26l5.2 17 5-12.5L32 43l4.8-12.5 5 12.5L47 26', fill: 'none', stroke: 'currentColor', 'stroke-width': 3, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }));
}

export const MUSEUM = 'World of Inventions';
