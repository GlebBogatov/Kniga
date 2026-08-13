"""Роутер гадания: POST /api/reading."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import ReadingRequest
from ..services import readings
from ..services.llm import LLMCallError, LLMService, LLMUnavailable, get_llm_service

router = APIRouter(tags=["divination"])


@router.post("/reading")
def create_reading(
    req: ReadingRequest,
    db: Session = Depends(get_db),
    llm: LLMService = Depends(get_llm_service),
) -> dict:
    try:
        return readings.create_reading(db, req, llm)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except LLMUnavailable:
        raise HTTPException(
            status_code=503,
            detail="Толкование временно недоступно, показано классическое значение.",
        )
    except LLMCallError:
        raise HTTPException(
            status_code=502, detail="Не удалось получить толкование. Попробуйте ещё раз."
        )
