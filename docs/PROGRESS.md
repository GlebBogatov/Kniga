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

---

## Что дальше

Этап 10 — стриминг толкования (SSE). Далее: пресеты и справочник (11–12),
README и финальный прогон (13).
