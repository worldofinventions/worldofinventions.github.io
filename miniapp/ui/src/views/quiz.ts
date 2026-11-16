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
      h('p.eyebrow', {}, 'Invention quiz'),
      h('h2', {}, 'Ten questions before you go'),
      h('p.lead', {}, 'A full round from the museum bank of questions, the answers shuffled. Every correct answer counts towards your statistics, like in the bot.'),
      paper)));

  let question: QuizQuestion | null = null;
  let verdict: QuizVerdict | null = null;
  let score = 0;

  const header = () => {
    const total = question?.total ?? 0;
    return h('header.paper__head', {},
      h('span', {}, 'Examination paper'),
      h('span', {}, 'Full round'),
      h('span', {}, `Score ${score}/${total}`));
  };

  async function start(focus = false): Promise<void> {
    try {
      question = await api.quizStart();
      verdict = null;
      score = 0;
      ask(focus);
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Could not start the quiz');
    }
  }

  function ask(focus = true): void {
    const q = question!;
    const feedback = h('div.paper__feedback', { role: 'status', 'aria-live': 'polite' });
    const title = h('h3.paper__q', { tabindex: -1 }, q.question);
    const buttons = q.options.map((text, i) => {
      const b = h('button.option', { type: 'button' }, h('span.option__letter', {}, String.fromCharCode(65 + i)), h('span', {}, text));
      b.addEventListener('click', () => answer(i));
      return b;
    });
    paper.replaceChildren(header(),
      h('p.paper__count', {}, `Question ${q.index + 1} of ${q.total}`),
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
      const next = h('button.btn.btn--primary', { type: 'button' }, last ? 'See the result' : 'Next question');
      next.addEventListener('click', () => { last ? result() : advance(); });
      paper.querySelector('.paper__feedback')!.replaceChildren(
        h('p.paper__verdict', { class: res.correct ? 'is-right' : 'is-wrong' }, res.correct ? 'Correct.' : `Not quite. The correct answer is: ${res.correct_option}`),
        h('p.paper__fact', {}, res.fact),
        next);
      paper.querySelector('.paper__head')!.replaceWith(header());
      next.focus();
      if (last) notify(); // quizzes_completed has changed server-side
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Could not record the answer');
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
      toast(err instanceof Error ? err.message : 'Could not load the next question');
    }
  }

  function result(): void {
    const res = verdict!;
    const total = res.total;
    const comment = res.score === total
      ? 'A perfect paper. The curators would like a word about a job.'
      : res.score >= total * 0.6
        ? 'Well done. You clearly read the labels.'
        : 'A fair try. The halls are a good place to revise.';
    const title = h('h3.paper__q', { tabindex: -1 }, `You scored ${res.score} out of ${total}.`);
    const again = h('button.btn', { type: 'button' }, 'Play again');
    again.addEventListener('click', () => start(true));
    paper.replaceChildren(header(),
      h('p.paper__count', {}, 'Result'),
      title,
      h('p.paper__stamp', { 'aria-hidden': 'true', class: res.score === total ? 'is-top' : '' }, `${res.score}/${total}`),
      h('p.paper__fact', {}, comment),
      h('p.paper__fact', {}, 'Your round has been added to your statistics. Another round draws ten new random questions with shuffled answers.'),
      h('div.paper__actions', {}, again));
    title.focus({ preventScroll: true });
  }

  start(false);
}
