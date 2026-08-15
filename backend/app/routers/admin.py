"""Админка владельца: /api/admin/* (роль admin)."""
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_roles
from ..models import Payment, User
from ..services import admin, payments

router = APIRouter(prefix="/admin", tags=["admin"])
admin_only = require_roles("admin")


@router.get("/metrics")
def metrics(_: User = Depends(admin_only), db: Session = Depends(get_db)) -> dict:
    return admin.metrics(db)


@router.get("/users")
def users(
    query: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> list[dict]:
    return admin.list_users(db, query, limit, offset)


def _target(db: Session, user_id: int) -> User:
    user = admin.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")
    return user


@router.get("/users/{user_id}")
def user_detail(
    user_id: int, _: User = Depends(admin_only), db: Session = Depends(get_db)
) -> dict:
    detail = admin.user_admin(db, _target(db, user_id))
    detail["payments"] = admin.user_payments(db, user_id)
    return detail


@router.post("/users/{user_id}/block")
def block(user_id: int, _: User = Depends(admin_only), db: Session = Depends(get_db)) -> dict:
    return admin.set_blocked(db, _target(db, user_id), True)


@router.post("/users/{user_id}/unblock")
def unblock(user_id: int, _: User = Depends(admin_only), db: Session = Depends(get_db)) -> dict:
    return admin.set_blocked(db, _target(db, user_id), False)


@router.post("/users/{user_id}/grant")
def grant(
    user_id: int,
    tariff_id: str = Body(..., embed=True),
    _: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> dict:
    user = _target(db, user_id)
    try:
        payments.admin_grant(db, user, tariff_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return admin.user_admin(db, user)


@router.post("/users/{user_id}/set-free")
def set_free(
    user_id: int, _: User = Depends(admin_only), db: Session = Depends(get_db)
) -> dict:
    user = _target(db, user_id)
    payments.admin_set_free(db, user)
    return admin.user_admin(db, user)


@router.post("/users/{user_id}/refund/{payment_id}")
def refund(
    user_id: int,
    payment_id: int,
    _: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> dict:
    payment = db.get(Payment, payment_id)
    if payment is None or payment.user_id != user_id:
        raise HTTPException(status_code=404, detail="Платёж не найден.")
    payments.refund(db, payment)
    return payments.payment_public(payment)
