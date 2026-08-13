# Книга перемен — ИИ-толкования И-Цзин

Веб-сервис: пользователь вводит **вопрос** и **результат гадания** (триграмму,
гексаграмму или бросок монет), а Claude API возвращает толкование,
персонализированное под вопрос. Ключевое отличие от конкурентов — вопрос
влияет на ответ.

## Структура

```
backend/    FastAPI + SQLite + прокси к Anthropic (Python 3.12+)
frontend/   React 18 + Vite + TypeScript (SPA)
docs/       PROGRESS.md — журнал прогресса по этапам
```

## Запуск (разработка)

**Backend:**
```
cd backend
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt
copy .env.example .env                               # затем вписать ANTHROPIC_API_KEY
uvicorn app.main:app --reload
```
API-доки (Swagger): http://localhost:8000/docs

**Frontend:**
```
cd frontend
npm install
npm run dev
```
Vite проксирует `/api` → `http://localhost:8000`.

## API

| Метод | Путь | Назначение |
|---|---|---|
| POST | `/api/reading` | Толкование (режимы `8` / `64` / `coins`) |
| POST | `/api/reading/stream` | То же, потоковой передачей (SSE) |
| POST | `/api/reading/{id}/chat` | Уточняющий вопрос (лимит 5) |
| POST | `/api/question/check` | Проверка качества вопроса + кризис-фильтр |
| GET/DELETE | `/api/journal`, `/api/journal/{id}` | Дневник |
| POST | `/api/journal/analyze` | Анализ дневника (≥2 записей) |
| GET | `/api/trigrams`, `/api/hexagrams`, `/api/presets` | Справочник и пресеты |
| GET | `/api/health`, `/api/health/llm` | Health-check |

## Данные и генерация

Данные триграмм/гексаграмм и таблица Вэнь-вана — канонические, живут в
`backend/app/data/`. Фронтенд использует сгенерированный из них файл
`frontend/src/data/reference.generated.ts`. После изменения данных
перегенерировать:
```
cd backend && python scripts/export_frontend_data.py
```

## Контент (наполняется позже)

Интерпретирующая проза и тексты интерфейса — заглушки, помеченные `[TODO Таня]`
(в `backend/app/data/*` — поля `classic`/`essence`; в промптах — тон;
`frontend/src/copy.ts` — все строки UI; `backend/app/data/question_presets.py`
— 5 стартовых пресетов). Логику это не затрагивает.

## Доступ к Claude из РФ

Прямой `api.anthropic.com` из РФ считается нестабильным. Код поддерживает три
канала без изменения логики (переключаются через `.env`): свой relay-прокси
(`ANTHROPIC_BASE_URL`), исходящий socks5/http-прокси (`OUTBOUND_PROXY_URL`),
OpenRouter (`LLM_PROVIDER=openrouter`). Заложены ретраи и circuit breaker.

## Тесты

```
cd backend && pytest
cd frontend && npm test
```
