# Книга перемен — ИИ-толкования И-Цзин

Веб-сервис: пользователь вводит **вопрос** и **результат гадания** (триграмму,
гексаграмму или бросок монет), а Claude API возвращает толкование,
персонализированное под вопрос.

## Структура

```
backend/    FastAPI + SQLite + прокси к Anthropic (Python 3.12+)
frontend/   React 18 + Vite + TypeScript (SPA)
```

## Запуск (разработка)

Backend:
```
cd backend
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt
copy .env.example .env                               # затем вписать ANTHROPIC_API_KEY
uvicorn app.main:app --reload
```
API-доки: http://localhost:8000/docs

Frontend:
```
cd frontend
npm install
npm run dev
```
Vite проксирует `/api` → `http://localhost:8000`.

## Тесты

```
cd backend && pytest
cd frontend && npm test
```

## Статус

Этап 1 — каркас. Дальнейшие этапы см. в плане реализации.
Данные триграмм/гексаграмм — канонические; интерпретирующая проза и тексты
интерфейса — заглушки `[TODO ...]`, наполняются контент-редактором позже.
