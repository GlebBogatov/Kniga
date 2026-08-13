"""Роутер гадания: POST /api/reading."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import ChatRequest, ReadingRequest
from ..services import readings
from ..services.llm import LLMCallError, LLMService, LLMUnavailable, get_llm_service
from ..services.ratelimit import READING_LIMITS, rate_limit

router = APIRouter(tags=["divination"])


@router.post("/reading")
def create_reading(
    req: ReadingRequest,
    db: Session = Depends(get_db),
    llm: LLMService = Depends(get_llm_service),
    _rl: None = Depends(rate_limit("reading", READING_LIMITS)),
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


@router.post("/reading/stream")
def reading_stream(
    req: ReadingRequest,
    db: Session = Depends(get_db),
    llm: LLMService = Depends(get_llm_service),
    _rl: None = Depends(rate_limit("reading", READING_LIMITS)),
) -> StreamingResponse:
    return StreamingResponse(
        readings.stream_reading(db, req, llm), media_type="text/event-stream"
    )


@router.post("/reading/{reading_id}/chat")
def chat(
    reading_id: int,
    req: ChatRequest,
    db: Session = Depends(get_db),
    llm: LLMService = Depends(get_llm_service),
) -> dict:
    try:
        return readings.chat(db, reading_id, req.message, llm)
    except LookupError:
        raise HTTPException(status_code=404, detail="Гадание не найдено.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except LLMUnavailable:
        raise HTTPException(status_code=503, detail="Чат временно недоступен.")
    except LLMCallError:
        raise HTTPException(status_code=502, detail="Не удалось получить ответ.")
