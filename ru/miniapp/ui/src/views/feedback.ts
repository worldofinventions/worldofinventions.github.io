// Suggestions & feedback: typed here, delivered to the admin like the bot does.
import { h, toast, haptic } from '../ui';
import { api } from '../api';

const LIMIT = 4000;

export function mountFeedback(root: HTMLElement): void {
  const counter = h('span', {}, '0');
  const box = h('textarea.field__area', {
    maxlength: LIMIT,
    placeholder: 'Есть идея, нашли ошибку или хотите предложить изобретение? Напишите здесь, и сообщение получит команда проекта.',
    rows: 6,
  }) as HTMLTextAreaElement;
  box.addEventListener('input', () => { counter.textContent = String(box.value.length); });
  const send = h('button.btn.btn--primary', { type: 'button' }, 'Отправить команде');

  send.addEventListener('click', async () => {
    const text = box.value.trim();
    if (!text) { toast('Сначала напишите сообщение'); return; }
    haptic('impact', 'light');
    send.disabled = true;
    try {
      await api.sendFeedback(text);
      haptic('notify', 'success');
      root.replaceChildren(h('section', {}, h('div.wrap.center', {},
        h('p.eyebrow', {}, 'Сообщение доставлено'),
        h('h2', {}, 'Спасибо! 💙'),
        h('p.lead', {}, 'Ваше сообщение отправлено команде проекта.'),
        h('a.btn', { href: '#/' }, 'Вернуться в музей'))));
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Не удалось отправить сообщение');
      send.disabled = false;
    }
  });

  root.append(h('section', {},
    h('div.wrap', {},
      h('p.eyebrow', {}, 'Предложения и отзывы'),
      h('h2', {}, '💬 Напишите кураторам'),
      h('p.lead', {}, 'Сообщение попадёт команде проекта, туда же, куда приходят отзывы из бота.'),
      h('div.form', {},
        h('label.field', { for: 'feedback-box' }, h('span', {}, 'Ваше сообщение'), box),
        h('p.form__counter', {}, counter, ` / ${LIMIT}`),
        send))));
}
