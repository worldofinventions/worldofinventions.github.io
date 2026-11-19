// A five-question taster of the bot's quiz, drawn from the same bank with the same shuffling.
import { SITE_QUIZ_SIZE } from '../config';
import { QUIZ, QUIZ_ROUND_SIZE } from '../data';
import { newQuizRound, type QuizRound } from '../bot';
import { $, h, botLink } from '../ui';

export function initQuiz(): void {
  const root = $('#quiz');
  const paper = h('div.paper');
  root.append(paper);
  let round: QuizRound;
  let index = 0;
  let score = 0;

  const header = () => h('header.paper__head', {},
    h('span', {}, 'Экзаменационный лист'),
    h('span', {}, `Вопросов в банке: ${QUIZ.length}`),
    h('span', {}, `Score ${score}/${round.order.length}`));

  function start(focus = false): void {
    round = newQuizRound(QUIZ, SITE_QUIZ_SIZE);
    index = 0;
    score = 0;
    question(focus);
  }

  function question(focus = true): void {
    const q = QUIZ[round.order[index]];
    const order = round.optionOrders[index];
    const feedback = h('div.paper__feedback', { role: 'status', 'aria-live': 'polite' });
    const title = h('h3.paper__q', { tabindex: -1 }, q.question);
    const buttons = order.map((original, i) => {
      const b = h('button.option', { type: 'button' }, h('span.option__letter', {}, 'АБВГ'[i] ?? String(i + 1)), h('span', {}, q.options[original]));
      b.addEventListener('click', () => answer(original));
      return b;
    });
    function answer(original: number): void {
      const correct = original === q.answer;
      if (correct) score++;
      buttons.forEach((b, i) => {
        b.disabled = true;
        if (order[i] === q.answer) b.classList.add('is-right');
        else if (order[i] === original) b.classList.add('is-wrong');
      });
      const last = index + 1 >= round.order.length;
      const next = h('button.btn.btn--primary', { type: 'button' }, last ? 'Показать результат' : 'Следующий вопрос');
      next.addEventListener('click', () => { index++; last ? result() : question(); });
      feedback.replaceChildren(
        h('p.paper__verdict', { class: correct ? 'is-right' : 'is-wrong' }, correct ? 'Верно.' : `Не совсем. Правильный ответ: ${q.options[q.answer]}`),
        h('p.paper__fact', {}, q.fact),
        next);
      paper.querySelector('.paper__head')!.replaceWith(header());
      next.focus();
    }
    paper.replaceChildren(header(),
      h('p.paper__count', {}, `Вопрос ${index + 1} из ${round.order.length}`),
      title, h('div.options', {}, ...buttons), feedback);
    if (focus) title.focus({ preventScroll: true });
  }

  function result(): void {
    const total = round.order.length;
    // same three bands as the bot: perfect, at least 60%, below
    const comment = score === total
      ? 'Ни одной ошибки. Кураторы хотели бы взять вас на работу.'
      : score >= total * 0.6
        ? 'Хороший результат. Вы явно читали таблички.'
        : 'Неплохая попытка. Повторить можно в залах музея.';
    const title = h('h3.paper__q', { tabindex: -1 }, `Ваш результат: ${score} из ${total}.`);
    const again = h('button.btn', { type: 'button' }, 'Сыграть ещё');
    again.addEventListener('click', () => start(true));
    paper.replaceChildren(header(),
      h('p.paper__count', {}, 'Результат'),
      title,
      h('p.paper__stamp', { 'aria-hidden': 'true', class: score === total ? 'is-top' : '' }, `${score}/${total}`),
      h('p.paper__fact', {}, comment),
      h('p.paper__fact', {}, `Это была проба. В Telegram в каждом раунде ${QUIZ_ROUND_SIZE} случайных вопросов из банка, а варианты каждый раз перемешиваются.`),
      h('div.paper__actions', {}, botLink('Полный раунд в Telegram', 'btn btn--primary', 'quiz'), again));
    title.focus({ preventScroll: true });
  }

  start();
}
