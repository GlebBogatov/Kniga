"""Тарифы, оплата и подписка: /api/tariffs, /api/payments/*, /api/subscription/*.

Провайдер оплаты — заглушка (см. services/payments.py). Для проверки потока без
реального ЮKassa есть dev-confirm; вебхук присутствует для будущего реального
подключения.
"""
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..data.tariffs import TARIFFS
from ..db import get_db
from ..deps import get_current_user
from ..models import Payment, User
from ..services import auth, payments

router = APIRouter(tags=["payments"])


@router.get("/tariffs")
def list_tariffs() -> list[dict]:
    return TARIFFS


@router.post("/payments/checkout")
def checkout(
    tariff_id: str = Body(..., embed=True),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return payments.create_checkout(db, user, tariff_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/payments/dev-confirm/{payment_id}")
def dev_confirm(
    payment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Заглушка успешной оплаты (вместо реального возврата с ЮKassa)."""
    if not settings.allow_dev_login:
        raise HTTPException(status_code=403, detail="Заглушка оплаты отключена.")
    payment = db.get(Payment, payment_id)
    if payment is None or payment.user_id != user.id:
        raise HTTPException(status_code=404, detail="Платёж не найден.")
    if payment.status != "pending":
        raise HTTPException(status_code=400, detail="Платёж уже обработан.")
    payments.confirm_payment(db, payment)
    db.refresh(user)
    return {"payment": payments.payment_public(payment), "user": auth.user_public(user)}


@router.post("/payments/webhook")
def webhook(event: dict = Body(default={}), db: Session = Depends(get_db)) -> dict:
    """Вебхук провайдера — заглушка под будущий реальный ЮKassa.

    Ожидается уведомление об оплате; находим платёж и подтверждаем.
    """
    obj = event.get("object", {})
    provider_payment_id = obj.get("id")
    if event.get("event") == "payment.succeeded" and provider_payment_id:
        payment = (
            db.query(Payment)
            .filter_by(provider_payment_id=provider_payment_id, status="pending")
            .one_or_none()
        )
        if payment:
            payments.confirm_payment(db, payment)
    return {"ok": True}


@router.get("/payments")
def my_payments(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    rows = (
        db.query(Payment)
        .filter_by(user_id=user.id)
        .order_by(Payment.created_at.desc(), Payment.id.desc())
        .all()
    )
    return [payments.payment_public(p) for p in rows]


@router.post("/subscription/cancel")
def cancel_subscription(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    payments.cancel_autorenew(db, user)
    db.refresh(user)
    return auth.user_public(user)
