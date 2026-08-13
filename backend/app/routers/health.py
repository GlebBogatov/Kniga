"""Health-check: liveness и диагностика канала LLM (кэш 5 минут)."""
import time

from fastapi import APIRouter

from ..config import settings
from ..services.llm import get_llm_service

router = APIRouter(tags=["health"])

_TTL = 300.0
_llm_cache: tuple[float, dict] | None = None


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/health/llm")
def health_llm() -> dict:
    """Тестовый вызов LLM (max_tokens=5). Результат кэшируется на 5 минут —
    быстрая диагностика «канал упал / ключ протух / прокси лёг»."""
    global _llm_cache
    now = time.monotonic()
    if _llm_cache and now - _llm_cache[0] < _TTL:
        return _llm_cache[1]

    result = {"provider": settings.llm_provider, "ok": False, "latency_ms": None}
    start = time.monotonic()
    try:
        svc = get_llm_service()
        svc.call_text(None, [{"role": "user", "content": "ping"}],
                      model=settings.model_light, max_tokens=5)
        result["ok"] = True
    except Exception:
        result["ok"] = False
    result["latency_ms"] = round((time.monotonic() - start) * 1000)

    _llm_cache = (now, result)
    return result
