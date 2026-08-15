# Журнал прогресса

Фиксируется после каждого этапа: что сделано, статус тестов, коммит.
План этапов — в утверждённом плане реализации.

---

## Этап 1 — Каркас · 2026-08-13 · коммит `4f8085e`

- Склонирован репозиторий, проект собран в корне (`backend/`, `frontend/`).
- **Backend:** FastAPI-приложение (`app/main.py`), настройки (`config.py`,
  pydantic-settings), БД (`db.py`, SQLAlchemy), health-роутер, `.env.example`,
  `requirements.txt`.
- **Frontend:** заготовка Vite + React + TypeScript, прокси `/api` → `:8000`,
  палитра (`styles/palette.css`).
- `.gitignore`, README.
- **Тесты:** `test_health` — зелёный (1 passed).
- Окружение: Python 3.13, Node 24, venv установлен.

## Этап 2 — Данные · 2026-08-13 · коммит `7839e14`

- `data/trigrams.py`: 8 триграмм из канона (`восемь_триграмм_...md`) +
  обратный индекс `TRIGRAM_BY_LINES`. Поле `classic` — заглушка `[TODO Таня]`.
- `data/hexagrams.py`: 64 гексаграммы + `KING_WEN[lower][upper] → 1..64`.
  `essence` — заглушка `[TODO Таня]`.
- **Тесты:** `test_trigram_lines`, `test_king_wen` — контрольные точки таблицы
  Вэнь-вана, полнота 1..64, биекция 64 комбинаций. Итого 8 passed.

## Этап 3 — Расчёт символов · 2026-08-13 · коммит `fec6590`

- `services/divination.py`: расчёт символа для режимов 8 / 64 / coins;
  изменяющиеся линии, вторичная гексаграмма, виртуальный бросок (`secrets`,
  классическое распределение 3/8 и 1/8).
- **Тесты:** `test_coins` — 6×7→№1 без изменений; 6×6→№2 + вторичная №1;
  распределение броска; валидация ввода. Итого 16 passed.

## Этап 4 — LLM-сервис, промпты, схемы · 2026-08-13 · коммит `a6c09c2`

- `services/llm.py`: провайдер-абстракция (`AnthropicProvider`,
  `OpenRouterProvider`), base_url/proxy, ретраи на сетевые ошибки, circuit
  breaker (порог/таймаут, инъекция часов), structured output через
  `output_config.format`, потоковый `stream_text`.
- `services/prompts.py`: промпты триграммы/гексаграммы/монет, чат, проверка
  вопроса (+crisis), анализ дневника; блок безопасности `SAFETY` в каждом.
- `schemas.py`: `ReadingRequest`/`ChatRequest`/`QuestionCheckRequest` +
  JSON-схемы структурированного вывода.
- `/api/health/llm` (кэш 5 мин).
- **Тесты:** `test_llm` (breaker, ретраи→503/502, переключение провайдера,
  proxy/base_url), `test_prompts` (вопрос/безопасность/стиль/монеты).
  Итого 26 passed.

## Этап 5 — POST /api/reading + БД · 2026-08-13 · коммит `f69be5e`

- `models.py`: `Reading` и `ChatMessage` (SQLAlchemy 2.0, cascade delete,
  задел под user_id).
- `services/readings.py`: сборка символа → промпт → structured LLM → сохранение
  записи; symbol_key/label/element.
- `routers/divination.py`: `POST /api/reading` (422 при неверных полях,
  502/503 при сбое LLM), подключён в `main.py`.
- **Тесты:** `test_api` — happy-path режимов 8/64/coins (+виртуальный бросок),
  сохранение записи, 422 на неверных полях/коротком вопросе. Итого 33 passed.

## Этап 6 — Rate limiting + кризис-фильтр · 2026-08-13

- `services/ratelimit.py`: in-memory лимитер по IP (скользящее окно),
  зависимость `rate_limit`; лимиты reading 10/час·30/сутки, question 30/час,
  analyze 5/сутки.
- `/api/reading` под лимитом; middleware ограничения тела (>8 КБ → 413).
- `routers/question.py`: `POST /api/question/check` (MODEL_LIGHT) →
  quality/hint/crisis; блок безопасности `SAFETY` уже во всех промптах.
- Тесты вынесены в общий `conftest.py` (in-memory БД + FakeLLM по схеме).
- **Тесты:** `test_question`, `test_ratelimit` (429 после лимита, 413 на
  большом теле) + рефактор `test_api`. Итого 37 passed.

*(точные хеши коммитов — в `git log`.)*

## Этап 7 — Frontend «Гадание» · 2026-08-13

- Генератор `backend/scripts/export_frontend_data.py`: единый источник данных
  (бэкенд) → `frontend/src/data/reference.generated.ts` (триграммы, гексаграммы,
  KING_WEN) — без ручного дублирования.
- `api/client.ts` (fetch, таймаут 60 с, обработка ошибок), `copy.ts` (все строки
  UI — точка Тани), `types.ts`, утилиты `lib/lines`, `lib/validation`.
- Компоненты: `TrigramLines`, `TrigramGrid`, `HexagramPicker` (превью № и имени
  до API), `CoinsInput` (+виртуальный бросок), `QuestionInput` (проверка вопроса,
  плашка кризиса), `ReadingResult` (классика мгновенно, 4 блока, печать-ханьцзы,
  дисклеймер, деградация при 502/503).
- `App.tsx`: табы, переключатель режимов, поток гадания.
- **Тесты (vitest):** вычисление гексаграммы из пары id, сегменты ян/инь,
  блокировка кнопки, превью-символы — 13 passed. Typecheck + vite build — ок.

*(точные хеши коммитов — в `git log`.)*

## Этап 8 — Дневник · 2026-08-13

- Backend: `services/readings.py` — `list_journal`, `delete_reading`,
  `analyze_journal` (≥2 записей, компактная выжимка → structured LLM).
- `routers/journal.py`: `GET /api/journal`, `DELETE /api/journal/{id}`,
  `POST /api/journal/analyze` (400 при <2, лимит 5/сутки).
- Frontend: обобщён `api/client` (GET/DELETE), компонент `Journal`
  (список с датой `ru-RU`, вопрос киноварью, удаление с confirm, анализ),
  подключён в таб «Дневник».
- **Тесты:** backend `test_journal` (список/удаление/404/analyze) — 43 passed;
  frontend typecheck + 13 vitest — ок.

*(точные хеши коммитов — в `git log`.)*

## Этап 9 — Уточняющий чат · 2026-08-13

- Backend: `readings.chat` — контекст гадания + история `ChatMessage`,
  лимит 5 уточнений, `call_text`; `POST /api/reading/{id}/chat`
  (404/400/502/503), поле `remaining`.
- Frontend: компонент `FollowUpChat` (история, счётчик «осталось N из 5»),
  подключён под результатом; метод `api.chat`.
- **Тесты:** backend `test_chat` (ответ+remaining, лимит на 6-м, 404) —
  46 passed; frontend typecheck + 13 vitest — ок.

*(точные хеши коммитов — в `git log`.)*

## Этап 10 — Стриминг толкования · 2026-08-13

- Backend: `POST /api/reading/stream` (SSE) — стрим прозы толкования
  (`stream_text`), затем компактный structured-добор advice/caution/next_step
  (+lines_commentary); события `delta`/`done`/`error`, сохранение записи.
  Схемы `TRAILER_SCHEMA`/`COINS_TRAILER_SCHEMA`, промпты stream/trailer.
- Frontend: `api.streamReading` (парсер SSE через ReadableStream), App стримит
  толкование по умолчанию с fallback на `POST /api/reading`; `ReadingResult`
  показывает текст по мере генерации (курсор).
- **Тесты:** backend `test_stream` (события + сохранение, 422) — 48 passed;
  frontend typecheck + 13 vitest + build — ок.

*(точные хеши коммитов — в `git log`.)*

## Этапы 11–13 — Пресеты, справочник, финал · 2026-08-13

- **11 (пресеты):** `data/question_presets.py` (5 стартовых, заглушки для Тани),
  `preset_slug` → `prompt_focus` в толковании (обычном и стриме); фронтенд —
  компонент `Presets` (чипы, подставляют текст вопроса + slug).
- **12 (справочник):** `routers/reference.py` — `GET /api/trigrams[/{id}]`,
  `/api/hexagrams[/{n}]`, `/api/presets[/{slug}]`.
- **13 (финал):** README (эндпоинты, шаг генерации данных, заметка о контенте,
  доступ из РФ). Полный прогон: **backend 55 passed, frontend 13 passed**.

*(точные хеши коммитов — в `git log`.)*

---

## Доп. — Демо-деплой на GitHub Pages · 2026-08-13

- `.github/workflows/pages.yml`: Actions собирает фронт (`VITE_DEMO=1`,
  `VITE_BASE=/Kniga/`) и публикует на GitHub Pages.
- Демо-режим (`frontend/src/api/demo.ts`, флаг `VITE_DEMO`): интерфейс
  кликается полностью без бэкенда, толкования — заглушки; баннер-предупреждение.
- `vite.config.ts`: `base` из `VITE_BASE` (Pages), локально `/`.
- Проверено локально (демо-сборка рендерится, пресеты/баннер видны),
  typecheck + 13 vitest — ок.

## Демо опубликовано · 2026-08-14

- Репозиторий сделан публичным, Pages включён (источник — GitHub Actions).
- **Сайт живой: https://glebbogatov.github.io/Kniga/** (деплой success, 200,
  база `/Kniga/` корректна). Пересобирается автоматически при пуше в `main`.
- ИИ-ответы в демо переведены в явные заглушки «✧ Здесь будет ИИ-мудрость ✧»
  (толкование, совет, предостережение, шаг, ответ чата, анализ дневника) —
  чтобы контент-редактору было видно, где встаёт сгенерированный текст.

## Монетизация · Этап 2 — Учётные записи (backend) · 2026-08-15

- Модели `User` / `Subscription` / `UserSession`; `Reading.user_id` (nullable):
  до входа гадания анонимны, после — привязаны к пользователю.
- `services/auth.py`: get-or-create пользователя, сессии (Bearer-токен),
  удаление аккаунта с данными (152-ФЗ). Вход VK/Яндекс — **заглушка**
  `dev-login` (реальный OAuth за флагом позже).
- `deps.py`: `get_current_user_optional` / `get_current_user` /
  `require_roles(...)` (роли user/admin/editor — задел под админку/CMS).
- Роутер `/api/auth/*`: login/{provider} (заглушка), dev-login, me (GET/PATCH),
  logout, delete account. Дневник и создание гаданий привязаны к пользователю
  (аноним видит свои анонимные записи; чужие удалить нельзя).
- Настройки `ALLOW_DEV_LOGIN`, `SESSION_TTL_DAYS` (+ `.env.example`).
- **Тесты: backend 62 passed** (+7 auth), frontend 13 passed.

## Монетизация · Этап 1 — Навигация + юр-документы · 2026-08-15

- Лёгкая hash-навигация в `main.tsx` (без роутер-зависимости, работает на
  Pages при любом base): `#/` — приложение, `#/legal/<slug>` — документ.
- Черновики юр-документов `content/legal.ts`: оферта, политика
  конфиденциальности, согласие на обработку ПДн, реквизиты — с плашкой
  «Черновик» и метками `[TODO юрист]` / `[TODO реквизиты ИП]`.
- Компоненты `LegalPage`, `Footer` (ссылки на документы, дисклеймер 18+,
  строка реквизитов); тексты в `copy.ts`.
- Проверено: эмуляция 390px — переполнения нет (`scrollWidth == vw`);
  build + 13 vitest — ок. Реальные документы/реквизиты — за юристом и ИП.

## Критерии проверки вопроса вынесены для Тани · 2026-08-14

- `data/question_check.py` (новый): критерии оценки вопроса — что считать
  хорошим/расплывчатым/кризисным, примеры, тон подсказки — как data с
  пометкой `[TODO Таня]`. `prompts.py::question_check_prompt` собирается
  из них; контракт (эндпоинт, схема `quality/hint/crisis`) не тронут.
- Фронт: кнопка «Проверить вопрос» теперь всегда показывает результат;
  в демо — явная заглушка-текст (проверка вопроса — функция ИИ, модель
  `model_light` = `claude-haiku-4-5`).
- Тесты: backend 55 passed, frontend 13 passed.

## Хиро-CTA + адаптивность · 2026-08-14

- Добавлена магнитная стартовая кнопка «✦ Задать свой вопрос» (по центру,
  сразу под заголовком): пульс-свечение, вращающаяся + мерцающая искра,
  пробегающий блик-глинт и мигание яркостью всей кнопки (`cta-flash`) —
  заметно и на телефоне. По клику — скролл к полю вопроса, фокус, подсветка.
- Адаптивность десктоп/планшет/телефон: брейкпоинты `<=820px` (планшет),
  `<=560px` и `<=380px` (телефон) — размеры кнопки/полей/отступов, кнопки
  на всю ширину, перенос режимов и монет. Проверено эмуляцией устройств
  390/834px через Chrome DevTools Protocol: `scrollWidth == vw`, переполнения
  нет. Все эффекты уважают `prefers-reduced-motion`.
- Логику/разметку не трогали (правки только в `styles/app.css`, `App.tsx`,
  `copy.ts`). Build + 13 vitest — ок.

## Редизайн — тёмная тема «Таро» · 2026-08-14

- По референсу tarotoo.com/free-tarot: тёмный фиолетовый фон со спот-светом,
  кремовый засечный шрифт (Cormorant Garamond / Marcellus), золотые небесные
  акценты и звёздная пыль, карты-триграммы оформлены как рубашки Таро (тёмный
  фиолет с золотым узором, золотой иероглиф), контурная золотая кнопка,
  скруглённое тёмное поле вопроса.
- Полностью переписаны `palette.css` и `styles/app.css`; в `index.html`
  подключены шрифты Google Fonts; хиро-орнамент в `App.tsx`.
- Логика/разметку компонентов не трогали. Typecheck + 13 vitest — ок.

---

## Итог

Каркас MVP завершён (этапы 1–13). Рабочий цикл во всех трёх режимах:
вопрос → символ → толкование (обычное и стрим) → уточнение → дневник → анализ;
проверка вопроса с кризис-фильтром; rate limiting; устойчивость доступа к LLM
(провайдеры/прокси/breaker). Контент — заглушки `[TODO Таня]`, наполняются
позже без изменения логики.

**Дальше (по плану — отдельные потоки):** контент Тани (эталонные толкования,
финальные тексты UI, тон промптов, 40–60 пресетов, дисклеймеры, 72 SEO-страницы);
задел P1 (символ дня, режим «да/нет», сверка исходов, профиль/стиль); деплой.
