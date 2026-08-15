"""Сервис авторизации и учётных записей.

Вход через VK/Яндекс ID пока реализован ЗАГЛУШКОЙ (`dev_login`): реальные
OAuth-вызовы не выполняются, пользователь создаётся по переданному профилю.
Реальный обмен кодом на токен у VK/Яндекс подключается позже за флагом
настроек — контракт эндпоинтов и модель данных при этом не меняются.

Сессия — непрозрачный токен (Bearer), хранится в таблице user_sessions.
"""
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..config import settings
from ..models import ChatMessage, Payment, Reading, Subscription, User, UserSession

PROVIDERS = ("vk", "yandex", "dev")


def _utcnow() -> datetime:
    """Наивный UTC — совпадает с тем, что SQLite отдаёт обратно (без tzinfo)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_or_create_user(
    db: Session,
    provider: str,
    provider_user_id: str,
    *,
    email: str | None = None,
    name: str | None = None,
    role: str | None = None,
) -> User:
    user = (
        db.query(User)
        .filter_by(provider=provider, provider_user_id=provider_user_id)
        .one_or_none()
    )
    if user is None:
        user = User(
            provider=provider,
            provider_user_id=provider_user_id,
            email=email,
            name=name,
            role=role or "user",
        )
        db.add(user)
        db.flush()  # получить user.id
        db.add(Subscription(user_id=user.id, plan="free", status="active"))
        db.commit()
        db.refresh(user)
    else:
        # обновляем контактные данные, если пришли новые
        changed = False
        if email and user.email != email:
            user.email, changed = email, True
        if name and user.name != name:
            user.name, changed = name, True
        if role and settings.allow_dev_login and user.role != role:
            user.role, changed = role, True  # роль меняется только в dev-режиме
        if changed:
            db.commit()
            db.refresh(user)
    return user


def start_session(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    expires = _utcnow() + timedelta(days=settings.session_ttl_days)
    db.add(UserSession(token=token, user_id=user.id, expires_at=expires))
    db.commit()
    return token


def resolve_token(db: Session, token: str) -> User | None:
    sess = db.query(UserSession).filter_by(token=token).one_or_none()
    if sess is None or sess.expires_at < _utcnow():
        return None
    user = db.get(User, sess.user_id)
    if user is None or user.is_blocked:
        return None
    return user


def end_session(db: Session, token: str) -> None:
    db.query(UserSession).filter_by(token=token).delete()
    db.commit()


def delete_account(db: Session, user: User) -> None:
    """Полное удаление аккаунта и связанных данных (право субъекта ПДн, 152-ФЗ)."""
    reading_ids = [r.id for r in db.query(Reading.id).filter_by(user_id=user.id).all()]
    if reading_ids:
        db.query(ChatMessage).filter(
            ChatMessage.reading_id.in_(reading_ids)
        ).delete(synchronize_session=False)
    db.query(Reading).filter_by(user_id=user.id).delete(synchronize_session=False)
    db.query(UserSession).filter_by(user_id=user.id).delete(synchronize_session=False)
    db.query(Payment).filter_by(user_id=user.id).delete(synchronize_session=False)
    db.query(Subscription).filter_by(user_id=user.id).delete(synchronize_session=False)
    db.delete(user)
    db.commit()


def token_from_header(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(None, 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


# --- представления для API ---


def subscription_public(sub: Subscription | None) -> dict:
    if sub is None:
        return {"plan": "free", "status": "active", "current_period_end": None,
                "auto_renew": False}
    return {
        "plan": sub.plan,
        "status": sub.status,
        "current_period_end": (
            sub.current_period_end.isoformat() if sub.current_period_end else None
        ),
        "auto_renew": sub.auto_renew,
    }


def user_public(user: User) -> dict:
    return {
        "id": user.id,
        "provider": user.provider,
        "email": user.email,
        "name": user.name,
        "birth_date": user.birth_date.isoformat() if user.birth_date else None,
        "role": user.role,
        "subscription": subscription_public(user.subscription),
    }
