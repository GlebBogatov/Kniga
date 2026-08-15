"""Дневник: GET/DELETE /api/journal, POST /api/journal/analyze.

Дневник привязан к пользователю: авторизованный видит свои записи,
аноним — свои анонимные (user_id NULL).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user_optional
from ..models import User
from ..services import payments, readings
from ..services.llm import LLMCallError, LLMService, LLMUnavailable, get_llm_service
from ..services.ratelimit import ANALYZE_LIMITS, rate_limit

router = APIRouter(tags=["journal"])


def _uid(user: User | None) -> int | None:
    return user.id if user else None


@router.get("/journal")
def get_journal(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
) -> list[dict]:
    return readings.list_journal(db, limit, offset, user_id=_uid(user))


@router.delete("/journal/{reading_id}")
def delete_entry(
    reading_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
) -> dict:
    if not readings.delete_reading(db, reading_id, user_id=_uid(user)):
        raise HTTPException(status_code=404, detail="Запись не найдена.")
    return {"deleted": reading_id}


@router.post("/journal/analyze")
def analyze(
    db: Session = Depends(get_db),
    llm: LLMService = Depends(get_llm_service),
    user: User | None = Depends(get_current_user_optional),
    _rl: None = Depends(rate_limit("analyze", ANALYZE_LIMITS)),
) -> dict:
    try:
        payments.ensure_premium(user)
        return readings.analyze_journal(db, llm, user_id=_uid(user))
    except payments.PremiumRequired as exc:
        raise HTTPException(status_code=402, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except LLMUnavailable:
        raise HTTPException(status_code=503, detail="Анализ временно недоступен.")
    except LLMCallError:
        raise HTTPException(status_code=502, detail="Не удалось проанализировать дневник.")
