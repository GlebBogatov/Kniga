"""Зависимости FastAPI для авторизации.

- get_current_user_optional — пользователь или None (гадать можно и анонимно).
- get_current_user — требует вход (401).
- require_roles(...) — фабрика зависимостей для админки/CMS (403 без роли).
"""
from collections.abc import Callable

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .db import get_db
from .models import User
from .services import auth


def get_current_user_optional(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User | None:
    token = auth.token_from_header(authorization)
    if not token:
        return None
    return auth.resolve_token(db, token)


def get_current_user(
    user: User | None = Depends(get_current_user_optional),
) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Требуется вход.")
    return user


def require_roles(*roles: str) -> Callable[..., User]:
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Недостаточно прав.")
        return user

    return dependency
