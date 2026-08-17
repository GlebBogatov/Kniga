"""Точка входа FastAPI: CORS, роутеры, инициализация БД, раздача фронтенда."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .db import init_db
from .routers import (
    admin,
    auth,
    cms,
    divination,
    health,
    journal,
    payments,
    question,
    reference,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="И-Цзин API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.max_body_bytes:
        return JSONResponse(status_code=413, content={"detail": "Запрос слишком большой."})
    return await call_next(request)


app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(cms.router, prefix="/api")
app.include_router(divination.router, prefix="/api")
app.include_router(question.router, prefix="/api")
app.include_router(journal.router, prefix="/api")
app.include_router(reference.router, prefix="/api")


@app.get("/api")
def api_root() -> dict:
    return {"service": "iching", "docs": "/docs"}


# Раздача собранного фронтенда, если рядом есть папка static (прод/Docker).
# В деве фронт обслуживает Vite, папки нет — тогда отдаём JSON на "/".
_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if _STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="spa")
else:

    @app.get("/")
    def root() -> dict:
        return {"service": "iching", "docs": "/docs"}
