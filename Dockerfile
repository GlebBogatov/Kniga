# Единый образ: сборка фронтенда (Node) + бэкенд FastAPI, который раздаёт и
# API (/api/*), и собранный фронтенд (/). Один сервис — один адрес, без CORS.

# --- Сборка фронтенда ---
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# Прод-сборка: без VITE_DEMO (реальный API), base = / (раздаётся из корня).
RUN npm run build

# --- Рантайм бэкенда ---
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
COPY backend/requirements.txt ./
RUN pip install -r requirements.txt
COPY backend/ ./
# Собранный фронтенд кладём в ./static — main.py отдаёт его на "/".
COPY --from=frontend /app/frontend/dist ./static
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
