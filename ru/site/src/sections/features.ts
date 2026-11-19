// The visitor's guide: every feature of the bot, each with the real screen it produces.
// The display case on the right behaves like the bot: one message, edited in place.
import { BY_ID, HALL_IDS, INVENTIONS, QUIZ, QUIZ_ROUND_SIZE, STATS, hallItems, COUNTRIES } from '../data';
import {
  hallsScreen, cardScreen, favoritesScreen, statsScreen, historyScreen, howScreen, mapScreen, filtersScreen, quizScreen, newQuizRound,
  feedbackScreen, FEEDBACK_THANKS, TEAM_SCREEN_HEAD, ITEMS_PER_PAGE, pageCount, exhibitsWord,
} from '../bot';
import { $, h, messageEl, userBubble, botLink } from '../ui';

interface Feature { id: string; title: string; text: string; note?: string; screen: () => HTMLElement[] }

/** Which bot screen each entry opens (the /start payloads handled in ../handlers.py). */
const START: Record<string, (starId: string) => string> = {
  halls: () => 'halls', card: (id) => `item_${id}`, favorites: () => 'favorites', stats: () => 'stats',
  today: () => 'today', how: (id) => `item_${id}`, map: () => 'map', search: () => 'search',
  quiz: () => 'quiz', feedback: () => 'feedback', team: () => 'team',
};

export function initFeatures(): void {
  const root = $('#guide');
  const withPhoto = INVENTIONS.filter((item) => item.image);
  const star = withPhoto[Math.min(4, withPhoto.length - 1)] ?? INVENTIONS[0];
  const today = new Date();
  const sample = { studied: Math.round(STATS.exhibits * 0.3), halls: Math.max(1, STATS.halls - 1), favorites: 3, correct: 16, total: 20, quizzes: 2 };

  const features: Feature[] = [
    {
      id: 'halls', title: 'Четыре зала и полный каталог',
      text: `Смотрите коллекцию по эпохам или листайте каталог: все ${STATS.exhibits} ${exhibitsWord(STATS.exhibits)}, по ${ITEMS_PER_PAGE} на странице (страниц: ${pageCount(STATS.exhibits)}).`,
      screen: () => [messageEl(hallsScreen())],
    },
    {
      id: 'card', title: 'Карточка экспоната',
      text: 'Фото и весь текст этикетки в одном сообщении. Когда вы идёте дальше, бот редактирует это же сообщение, и чат не превращается в ленту старых меню.',
      screen: () => [messageEl(cardScreen(star), { clampText: 230 })],
    },
    {
      id: 'favorites', title: 'Избранное',
      text: 'Нажмите звезду на любой карточке. Сохранённые экспонаты ждут в разделе «Избранное», последние сверху.',
      screen: () => [messageEl(favoritesScreen([star, hallItems(HALL_IDS[HALL_IDS.length - 1])[0]].filter(Boolean)))],
    },
    {
      id: 'stats', title: 'Личная статистика',
      text: 'Бот считает открытые экспонаты, посещённые залы, избранное и ответы в викторине. Экспонат считается изученным, как только вы его открыли.',
      note: 'Цифры посетителя придуманы для примера, общие количества настоящие.',
      screen: () => [messageEl(statsScreen(sample))],
    },
    {
      id: 'today', title: 'Этот день в истории',
      text: 'Откройте в любой день. Если на сегодня записей нет, бот покажет ближайшие события до и после и скажет, сколько до них дней.',
      note: 'Собрано для вашей даты по тому же правилу, что и в боте.',
      screen: () => [messageEl(historyScreen({ year: today.getFullYear(), month: today.getMonth() + 1, day: today.getDate() }, BY_ID), { clampText: 420 })],
    },
    {
      id: 'how', title: 'Как это работает',
      text: 'У каждого экспоната есть короткое простое объяснение принципа работы. Оно появляется под тем же фото, а одно нажатие возвращает этикетку.',
      screen: () => [messageEl(howScreen(star))],
    },
    {
      id: 'map', title: 'Карта изобретений',
      text: `Стран на карте: ${COUNTRIES.length}, у каждой число экспонатов. Многие русские изобретатели работали за границей, поэтому на карте есть Франция, Германия, Великобритания и США.`,
      screen: () => [messageEl(mapScreen())],
    },
    {
      id: 'search', title: 'Поиск и фильтры',
      text: 'Сузьте поиск по стране, залу и периоду, а потом напишите слово, чтобы искать внутри оставшегося. Буквы «е» и «ё» не различаются: «Королев» найдёт «Королёва».',
      screen: () => [messageEl(filtersScreen({ country: COUNTRIES[1] ?? null, hall: null, period: null }))],
    },
    {
      id: 'quiz', title: 'Викторина',
      text: `В каждом раунде ${QUIZ_ROUND_SIZE} случайных вопросов из ${QUIZ.length}, варианты перемешаны. После каждого ответа, верного или нет, бот рассказывает факт.`,
      screen: () => [messageEl(quizScreen(QUIZ, newQuizRound(QUIZ, QUIZ_ROUND_SIZE), 0))],
    },
    {
      id: 'feedback', title: 'Предложения и отзывы',
      text: 'Нашли ошибку или не хватает изобретения? Отправьте одно сообщение, и бот перешлёт его команде проекта.',
      note: 'Сообщение посетителя здесь для примера.',
      screen: () => [messageEl(feedbackScreen()), userBubble('Добавьте, пожалуйста, самовар!'), messageEl({ text: FEEDBACK_THANKS, keyboard: [] })],
    },
    {
      id: 'team', title: 'Команда проекта',
      text: 'Экран с авторами музея и ссылкой на соседний музей World of Inventions, в одно нажатие из главного меню.',
      screen: () => [messageEl({ text: `${TEAM_SCREEN_HEAD}\n\n• …`, keyboard: [[{ text: '🌍 World of Inventions (English)', cb: 'noop' }], [{ text: '🏠 Главное меню', cb: 'home' }]] })],
    },
  ];

  const screen = h('div.case__screen', { 'aria-hidden': 'true' });
  const note = h('p.case__note');
  const label = h('p.case__label');
  const display = h('div.case', {}, label, screen, note);
  const aside = h('div.guide__aside', {}, display);
  const wide = matchMedia('(min-width: 900px)');
  const entries = new Map<string, HTMLElement>();
  let active = '';

  const place = () => {
    if (wide.matches) aside.append(display);
    else entries.get(active)?.append(display);
  };
  const select = (f: Feature) => {
    if (active === f.id) return;
    active = f.id;
    for (const [id, li] of entries) {
      li.classList.toggle('is-active', id === f.id);
      li.querySelector('button')!.setAttribute('aria-expanded', String(id === f.id));
    }
    screen.replaceChildren(...f.screen());
    screen.scrollTop = 0;
    label.textContent = `Экран: ${f.title}`;
    note.textContent = f.note ?? 'Текст и кнопки ровно такие, как присылает бот.';
    place();
  };

  const list = h('ol.guide__list', {}, ...features.map((f) => {
    const button = h('button.guide__btn', { type: 'button', 'aria-expanded': 'false' }, f.title);
    button.addEventListener('click', () => select(f));
    const start = START[f.id]?.(star.id);
    const li = h('li.guide__item', {}, h('h3', {}, button), h('p', {}, f.text),
      start ? botLink(`Открыть «${f.title}» в боте`, 'guide__bot', start) : null);
    entries.set(f.id, li);
    return li;
  }));
  wide.addEventListener('change', place);
  root.append(list, aside);
  select(features[1]);
  // Reading down the list on a wide screen: the entry crossing the middle of the window takes the case.
  const io = new IntersectionObserver((hits) => {
    if (!wide.matches) return;
    const hit = hits.find((x) => x.isIntersecting);
    const f = hit && features.find((x) => entries.get(x.id) === hit.target);
    if (f) select(f);
  }, { rootMargin: '-46% 0px -46% 0px' });
  entries.forEach((li) => io.observe(li));
}
