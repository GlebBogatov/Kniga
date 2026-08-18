"""Подключение к БД: engine, сессия, Base, инициализация."""
from collections.abc import Iterator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

_connect_args = (
    {"check_same_thread": False} if settings.db_url.startswith("sqlite") else {}
)
engine = create_engine(settings.db_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Создать таблицы. Импорт models — чтобы они зарегистрировались на Base."""
    from . import models  # noqa: F401  (регистрация моделей)

    Base.metadata.create_all(bind=engine)
    _ensure_columns()


# Лёгкие идемпотентные миграции: create_all не добавляет колонки в уже
# существующие таблицы. Здесь дописываем новые поля в старую БД без Alembic.
# Формат: таблица -> {колонка: DDL-определение}.
_ADDED_COLUMNS: dict[str, dict[str, str]] = {
    "users": {"ui_mode": "VARCHAR(16) DEFAULT 'simple'"},
}


def _ensure_columns() -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table, columns in _ADDED_COLUMNS.items():
            if table not in existing_tables:
                continue
            present = {c["name"] for c in inspector.get_columns(table)}
            for name, ddl in columns.items():
                if name not in present:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
