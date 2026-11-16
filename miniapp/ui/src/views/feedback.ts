// Suggestions & feedback: typed here, delivered to the admin like the bot does.
import { h, toast, haptic } from '../ui';
import { api } from '../api';

const LIMIT = 4000;

export function mountFeedback(root: HTMLElement): void {
  const counter = h('span', {}, '0');
  const box = h('textarea.field__area', {
    maxlength: LIMIT,
    placeholder: 'Have an idea, spotted a mistake, or want to suggest an invention? Write here and the message goes to the project team.',
    rows: 6,
  }) as HTMLTextAreaElement;
  box.addEventListener('input', () => { counter.textContent = String(box.value.length); });
  const send = h('button.btn.btn--primary', { type: 'button' }, 'Send to the team');

  send.addEventListener('click', async () => {
    const text = box.value.trim();
    if (!text) { toast('Please write a message first'); return; }
    haptic('impact', 'light');
    send.disabled = true;
    try {
      await api.sendFeedback(text);
      haptic('notify', 'success');
      root.replaceChildren(h('section', {}, h('div.wrap.center', {},
        h('p.eyebrow', {}, 'Message delivered'),
        h('h2', {}, 'Thank you! 💙'),
        h('p.lead', {}, 'Your message has been sent to the project team.'),
        h('a.btn', { href: '#/' }, 'Back to the museum'))));
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Could not send your message');
      send.disabled = false;
    }
  });

  root.append(h('section', {},
    h('div.wrap', {},
      h('p.eyebrow', {}, 'Suggestions & feedback'),
      h('h2', {}, '💬 Tell the curators'),
      h('p.lead', {}, 'Your message is forwarded to the project team, the same inbox the bot uses.'),
      h('div.form', {},
        h('label.field', { for: 'feedback-box' }, h('span', {}, 'Your message'), box),
        h('p.form__counter', {}, counter, ` / ${LIMIT}`),
        send))));
}
