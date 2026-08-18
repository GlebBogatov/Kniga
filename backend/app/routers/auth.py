"""Авторизация и профиль: /api/auth/*.

Вход через VK/Яндекс ID пока ЗАГЛУШКА (dev-login) — см. services/auth.py.
"""
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import DevLoginRequest, ProfileUpdateRequest
from ..services import auth

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login/{provider}")
def login_url(provider: str) -> dict:
    """Заглушка старта OAuth: реальный VK/Яндекс подключается позже.

    Пока фронт использует dev-login. Здесь возвращаем сведения о заглушке,
    чтобы UI мог показать корректное состояние.
    """
    if provider not in ("vk", "yandex"):
        raise HTTPException(status_code=404, detail="Неизвестный провайдер.")
    return {
        "provider": provider,
        "stub": True,
        "detail": "Вход через соцсети пока заглушка. Используется dev-login.",
    }


@router.post("/dev-login")
def dev_login(req: DevLoginRequest, db: Session = Depends(get_db)) -> dict:
    """Заглушка входа: создаёт/находит пользователя и открывает сессию."""
    if not settings.allow_dev_login:
        raise HTTPException(status_code=403, detail="Dev-вход отключён.")
    user = auth.get_or_create_user(
        db, req.provider, req.provider_user_id,
        email=req.email, name=req.name, role=req.role,
    )
    if user.is_blocked:
        raise HTTPException(status_code=403, detail="Аккаунт заблокирован.")
    token = auth.start_session(db, user)
    return {"token": token, "user": auth.user_public(user)}


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    return auth.user_public(user)


@router.patch("/me")
def update_me(
    req: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if req.name is not None:
        user.name = req.name
    if req.email is not None:
        user.email = req.email
    if req.ui_mode is not None:
        user.ui_mode = req.ui_mode
    db.commit()
    db.refresh(user)
    return auth.user_public(user)


@router.post("/logout")
def logout(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    token = auth.token_from_header(authorization)
    if token:
        auth.end_session(db, token)
    return {"ok": True}


@router.delete("/account")
def delete_account(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    auth.delete_account(db, user)
    return {"deleted": True}
