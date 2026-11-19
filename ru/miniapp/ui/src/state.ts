// Shared visitor state: loaded from /api/bootstrap, kept in sync on every change.
import type { Visitor, VisitorStats } from './api';

export const state = {
  user: null as Visitor | null,
  favorites: new Set<string>(),
  stats: null as VisitorStats | null,
};

export function setFavorites(ids: string[]): void {
  state.favorites = new Set(ids);
}

export function isFavorite(id: string): boolean {
  return state.favorites.has(id);
}

export function applyFavorite(id: string, saved: boolean): void {
  if (saved) state.favorites.add(id);
  else state.favorites.delete(id);
  if (state.stats) {
    state.stats.favorites = Math.max(0, state.stats.favorites + (saved ? 1 : -1));
  }
}

/** Anything subscribed to visitor changes (favorites view, statistics, home) re-renders. */
export function notify(): void {
  document.dispatchEvent(new CustomEvent('visitor:changed'));
}
