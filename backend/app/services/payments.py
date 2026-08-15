"""Платежи, подписка и лимиты freemium.

Платёжный провайдер — ЗАГЛУШКА (`payment_provider="stub"`): реальных вызовов
ЮKassa нет. Поток: checkout → (заглушка) подтверждение → активация подписки →
«чек» 54-ФЗ (тоже заглушка). Реальная ЮKassa подключается позже за настройками
без изменения контракта эндпоинтов.
"""
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..config import settings
from ..data.tariffs import TARIFF_BY_ID, Tariff
from ..models import Payment, Reading, Subscription, User


class QuotaExceeded(Exception):
    """Исчерпан дневной лимит бесплатного тарифа."""


class PremiumRequired(Exception):
    """Функция доступна только по подписке."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# --- Подписка / доступ ---


def is_premium(user: User | None) -> bool:
    if user is None:
        return False
    sub = user.subscription
    if sub is None or sub.plan != "premium":
        return False
    if sub.current_period_end and sub.current_period_end < _utcnow():
        return False
    return True


def readings_today(db: Session, user_id: int) -> int:
    start = _utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        db.query(Reading)
        .filter(Reading.user_id == user_id, Reading.created_at >= start)
        .count()
    )


def ensure_can_read(db: Session, user: User | None) -> None:
    """Бросает QuotaExceeded, если авторизованный бесплатный исчерпал лимит."""
    if not settings.freemium_enabled:
        return
    if user is None or is_premium(user):
        return
    if readings_today(db, user.id) >= settings.free_daily_readings:
        raise QuotaExceeded(
            f"Достигнут дневной лимит бесплатного тарифа "
            f"({settings.free_daily_readings}). Оформите подписку для безлимита."
        )


def ensure_premium(user: User | None) -> None:
    """Бросает PremiumRequired для премиум-функций (напр. анализ дневника)."""
    if not settings.freemium_enabled:
        return
    if not is_premium(user):
        raise PremiumRequired("Функция доступна по подписке.")


# --- Оплата (заглушка провайдера) ---


def _get_subscription(db: Session, user: User) -> Subscription:
    sub = user.subscription
    if sub is None:
        sub = Subscription(user_id=user.id, plan="free", status="active")
        db.add(sub)
        db.flush()
    return sub


def create_checkout(db: Session, user: User, tariff_id: str) -> dict:
    tariff = TARIFF_BY_ID.get(tariff_id)
    if tariff is None:
        raise ValueError("Неизвестный тариф.")
    payment = Payment(
        user_id=user.id,
        tariff_id=tariff["id"],
        plan=tariff["plan"],
        amount=tariff["price"],
        currency="RUB",
        status="pending",
        provider=settings.payment_provider,
        provider_payment_id="stub_" + secrets.token_hex(8),
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    # В реальном режиме здесь был бы confirmation_url от ЮKassa.
    return {
        "payment_id": payment.id,
        "amount": payment.amount,
        "currency": payment.currency,
        "confirmation_url": None,
        "stub": settings.payment_provider == "stub",
    }


def _activate_subscription(db: Session, user: User, tariff: Tariff) -> Subscription:
    sub = _get_subscription(db, user)
    base = _utcnow()
    if sub.current_period_end and sub.current_period_end > base:
        base = sub.current_period_end  # продление — прибавляем к остатку
    sub.plan = tariff["plan"]
    sub.status = "active"
    sub.current_period_end = base + timedelta(days=tariff["period_days"])
    sub.auto_renew = True
    db.flush()
    return sub


def _issue_receipt(payment: Payment, email: str | None) -> None:
    """Фискализация 54-ФЗ — ЗАГЛУШКА. Реальный чек формирует провайдер."""
    where = email or "email не указан"
    payment.receipt_stub = f"Чек (заглушка) на {payment.amount} ₽ отправлен: {where}"


def confirm_payment(db: Session, payment: Payment) -> Subscription:
    """Отметить оплату успешной, активировать подписку, «выдать» чек."""
    tariff = TARIFF_BY_ID.get(payment.tariff_id)
    if tariff is None:
        raise ValueError("Неизвестный тариф платежа.")
    user = db.get(User, payment.user_id)
    if user is None:
        raise ValueError("Пользователь платежа не найден.")
    payment.status = "succeeded"
    _issue_receipt(payment, user.email)
    sub = _activate_subscription(db, user, tariff)
    db.commit()
    db.refresh(sub)
    return sub


def cancel_autorenew(db: Session, user: User) -> Subscription:
    sub = _get_subscription(db, user)
    sub.auto_renew = False
    db.commit()
    db.refresh(sub)
    return sub


def admin_grant(db: Session, user: User, tariff_id: str) -> Subscription:
    """Выдать/продлить премиум вручную (админ)."""
    tariff = TARIFF_BY_ID.get(tariff_id)
    if tariff is None:
        raise ValueError("Неизвестный тариф.")
    sub = _activate_subscription(db, user, tariff)
    db.commit()
    db.refresh(sub)
    return sub


def admin_set_free(db: Session, user: User) -> Subscription:
    """Перевести на бесплатный тариф (админ)."""
    sub = _get_subscription(db, user)
    sub.plan = "free"
    sub.status = "active"
    sub.current_period_end = None
    sub.auto_renew = False
    db.commit()
    db.refresh(sub)
    return sub


def refund(db: Session, payment: Payment) -> None:
    """Отметить платёж возвращённым (реальный возврат делает провайдер)."""
    payment.status = "refunded"
    db.commit()


def payment_public(p: Payment) -> dict:
    return {
        "id": p.id,
        "tariff_id": p.tariff_id,
        "amount": p.amount,
        "currency": p.currency,
        "status": p.status,
        "receipt": p.receipt_stub,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }
