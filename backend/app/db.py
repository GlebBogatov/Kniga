"""Подключение к БД: engine, сессия, Base, инициализация."""
from collections.abc import Iterator

from sqlalchemy import create_engine
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


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
