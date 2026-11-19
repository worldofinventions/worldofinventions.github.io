// The real quiz, not a taster: a full 10-question round from the server.
// The round state (order, shuffled options, score) lives in the mini app
// server's memory, and every answer is recorded in the visitor's statistics —
// exactly the same numbers the bot keeps.
import { h, haptic, toast } from '../ui';
import { api, type QuizQuestion, type QuizVerdict } from '../api';
import { notify } from '../state';

export function mountQuiz(root: HTMLElement): void {
  const paper = h('div.paper');
  root.append(h('section', {},
    h('div.wrap', {},
      h('p.eyebrow', {}, 'Викторина'),
      h('h2', {}, 'Десять вопросов на прощание'),
      h('p.lead', {}, 'Полный раунд из банка вопросов музея, варианты перемешаны. Каждый верный ответ идёт в вашу статистику, как в боте.'),
      paper)));

  let question: QuizQuestion | null = null;
  let verdict: QuizVerdict | null = null;
  let score = 0;

  const header = () => {
    const total = question?.total ?? 0;
    return h('header.paper__head', {},
      h('span', {}, 'Экзаменационный лист'),
      h('span', {}, 'Полный раунд'),
      h('span', {}, `Счёт ${score}/${total}`));
  };

  async function start(focus = false): Promise<void> {
    try {
      question = await api.quizStart();
      verdict = null;
      score = 0;
      ask(focus);
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Не удалось начать викторину');
    }
  }

  function ask(focus = true): void {
    const q = question!;
    const feedback = h('div.paper__feedback', { role: 'status', 'aria-live': 'polite' });
    const title = h('h3.paper__q', { tabindex: -1 }, q.question);
    const buttons = q.options.map((text, i) => {
      const b = h('button.option', { type: 'button' }, h('span.option__letter', {}, 'АБВГ'[i] ?? String(i + 1)), h('span', {}, text));
      b.addEventListener('click', () => answer(i));
      return b;
    });
    paper.replaceChildren(header(),
      h('p.paper__count', {}, `Вопрос ${q.index + 1} из ${q.total}`),
      title, h('div.options', {}, ...buttons), feedback);
    if (focus) title.focus({ preventScroll: true });
  }

  async function answer(choice: number): Promise<void> {
    if (!question) return;
    haptic('select');
    const buttons = [...paper.querySelectorAll<HTMLButtonElement>('.option')];
    buttons.forEach((b) => { b.disabled = true; });
    try {
      const res = await api.quizAnswer(choice);
      verdict = res;
      score = res.score;
      haptic('notify', res.correct ? 'success' : 'error');
      buttons.forEach((b, i) => {
        if (question!.options[i] === res.correct_option) b.classList.add('is-right');
        else if (i === choice) b.classList.add('is-wrong');
      });
      const last = res.finished;
      const next = h('button.btn.btn--primary', { type: 'button' }, last ? 'Показать результат' : 'Следующий вопрос');
      next.addEventListener('click', () => { last ? result() : advance(); });
      paper.querySelector('.paper__feedback')!.replaceChildren(
        h('p.paper__verdict', { class: res.correct ? 'is-right' : 'is-wrong' }, res.correct ? 'Верно.' : `Не совсем. Правильный ответ: ${res.correct_option}`),
        h('p.paper__fact', {}, res.fact),
        next);
      paper.querySelector('.paper__head')!.replaceWith(header());
      next.focus();
      if (last) notify(); // quizzes_completed has changed server-side
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Не удалось записать ответ');
      buttons.forEach((b) => { b.disabled = false; });
    }
  }

  async function advance(): Promise<void> {
    try {
      const res = await api.quizNext();
      question = res;
      verdict = null;
      ask();
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Не удалось загрузить следующий вопрос');
    }
  }

  function result(): void {
    const res = verdict!;
    const total = res.total;
    const comment = res.score === total
      ? 'Ни одной ошибки. Кураторы хотели бы взять вас на работу.'
      : res.score >= total * 0.6
        ? 'Хороший результат. Вы явно читали таблички.'
        : 'Неплохая попытка. Повторить можно в залах музея.';
    const title = h('h3.paper__q', { tabindex: -1 }, `Ваш результат: ${res.score} из ${total}.`);
    const again = h('button.btn', { type: 'button' }, 'Сыграть ещё');
    again.addEventListener('click', () => start(true));
    paper.replaceChildren(header(),
      h('p.paper__count', {}, 'Результат'),
      title,
      h('p.paper__stamp', { 'aria-hidden': 'true', class: res.score === total ? 'is-top' : '' }, `${res.score}/${total}`),
      h('p.paper__fact', {}, comment),
      h('p.paper__fact', {}, 'Раунд добавлен в вашу статистику. В следующем раунде будут десять новых случайных вопросов.'),
      h('div.paper__actions', {}, again));
    title.focus({ preventScroll: true });
  }

  start(false);
}
