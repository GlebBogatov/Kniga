"""Проверка качества вопроса + кризис-фильтр: POST /api/question/check."""
from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..schemas import QUESTION_CHECK_SCHEMA, QuestionCheckRequest
from ..services import content, prompts
from ..services.llm import LLMCallError, LLMService, LLMUnavailable, get_llm_service
from ..services.ratelimit import QUESTION_LIMITS, rate_limit

router = APIRouter(tags=["question"])


@router.post("/question/check")
def check_question(
    req: QuestionCheckRequest,
    db: Session = Depends(get_db),
    llm: LLMService = Depends(get_llm_service),
    _rl: None = Depends(rate_limit("question", QUESTION_LIMITS)),
) -> dict:
    try:
        return llm.call_structured(
            prompts.question_check_prompt(req.question, content.effective_map(db)),
            QUESTION_CHECK_SCHEMA,
            model=settings.model_light,
            max_tokens=300,
        )
    except LLMUnavailable:
        raise HTTPException(status_code=503, detail="Проверка вопроса временно недоступна.")
    except LLMCallError:
        raise HTTPException(status_code=502, detail="Не удалось проверить вопрос.")
