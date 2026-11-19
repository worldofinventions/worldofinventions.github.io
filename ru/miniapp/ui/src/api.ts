// Мост к ru/server.py (пути относительные: приложение живёт под /ru/): favorites, statistics and the quiz live on
// the server, in the same SQLite database the Telegram bot uses.

const tg = (window as any).Telegram?.WebApp ?? null;

function headers(): Record<string, string> {
  const base = { 'Content-Type': 'application/json' };
  const initData: string = tg?.initData ?? '';
  return initData ? { ...base, 'X-Telegram-Init-Data': initData } : base;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(path, { ...init, headers: headers() });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error((data as { error?: string }).error ?? `Ошибка запроса (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export interface VisitorStats {
  studied_exhibits: number;
  opened_halls: number;
  favorites: number;
  correct_answers: number;
  total_answers: number;
  quizzes_completed: number;
  accuracy: number | null;
}

export interface Visitor { id: number; name: string; username?: string }
export interface Bootstrap { user: Visitor; favorites: string[]; stats: VisitorStats }
export interface QuizQuestion { index: number; total: number; question: string; options: string[] }
export interface QuizVerdict {
  correct: boolean;
  correct_option: string;
  fact: string;
  score: number;
  answered: number;
  total: number;
  finished: boolean;
}

export const api = {
  bootstrap: (): Promise<Bootstrap> => request('api/bootstrap'),
  stats: (): Promise<VisitorStats> => request('api/stats'),
  toggleFavorite: (id: string): Promise<{ saved: boolean }> =>
    request(`api/favorites/${encodeURIComponent(id)}/toggle`, { method: 'POST' }),
  markStudied: (id: string): Promise<unknown> =>
    request('api/progress/studied', { method: 'POST', body: JSON.stringify({ id }) }),
  markHall: (hall: string): Promise<unknown> =>
    request('api/progress/hall', { method: 'POST', body: JSON.stringify({ hall }) }),
  quizStart: (): Promise<QuizQuestion> => request('api/quiz/start', { method: 'POST' }),
  quizAnswer: (choice: number): Promise<QuizVerdict> =>
    request('api/quiz/answer', { method: 'POST', body: JSON.stringify({ choice }) }),
  quizNext: (): Promise<QuizQuestion> => request('api/quiz/next', { method: 'POST' }),
  sendFeedback: (message: string): Promise<{ ok: boolean }> =>
    request('api/feedback', { method: 'POST', body: JSON.stringify({ message }) }),
};
