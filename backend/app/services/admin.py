"""Админ-логика: пользователи, платежи, метрики (для владельца)."""
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..models import Payment, Reading, Subscription, User
from . import auth, payments


def user_admin(db: Session, u: User) -> dict:
    readings = db.query(Reading).filter_by(user_id=u.id).count()
    return {
        "id": u.id,
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "provider": u.provider,
        "email": u.email,
        "name": u.name,
        "role": u.role,
        "is_blocked": u.is_blocked,
        "subscription": auth.subscription_public(u.subscription),
        "readings": readings,
    }


def list_users(
    db: Session, query: str | None = None, limit: int = 50, offset: int = 0
) -> list[dict]:
    q = db.query(User)
    if query:
        like = f"%{query}%"
        q = q.filter(
            or_(
                User.email.ilike(like),
                User.name.ilike(like),
                User.provider_user_id.ilike(like),
            )
        )
    rows = (
        q.order_by(User.created_at.desc(), User.id.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return [user_admin(db, u) for u in rows]


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def set_blocked(db: Session, user: User, blocked: bool) -> dict:
    user.is_blocked = blocked
    db.commit()
    db.refresh(user)
    return user_admin(db, user)


def user_payments(db: Session, user_id: int) -> list[dict]:
    rows = (
        db.query(Payment)
        .filter_by(user_id=user_id)
        .order_by(Payment.created_at.desc(), Payment.id.desc())
        .all()
    )
    return [payments.payment_public(p) for p in rows]


def metrics(db: Session) -> dict:
    users_total = db.query(User).count()
    premium = (
        db.query(Subscription)
        .filter(Subscription.plan == "premium", Subscription.status == "active")
        .count()
    )
    readings_total = db.query(Reading).count()
    paid = db.query(Payment).filter(Payment.status == "succeeded")
    revenue = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        Payment.status == "succeeded"
    ).scalar()
    return {
        "users_total": users_total,
        "users_premium": premium,
        "readings_total": readings_total,
        "payments_succeeded": paid.count(),
        "revenue_total": int(revenue or 0),
    }
