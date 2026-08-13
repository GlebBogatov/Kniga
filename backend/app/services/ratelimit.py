"""Простой in-memory rate limiter по IP (скользящее окно).

Защита ключа: приложение без авторизации + платный API-ключ. Лимиты по IP
заменяют регистрацию на этапе без аккаунтов.
"""
import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import HTTPException, Request

from ..config import settings


class RateLimiter:
    def __init__(self, time_func: Callable[[], float] = time.time):
        self._time = time_func
        self._hits: dict[tuple[str, str], deque] = defaultdict(deque)

    def reset(self) -> None:
        self._hits.clear()

    def check(self, bucket: str, ip: str, limit: int, window: float) -> bool:
        now = self._time()
        dq = self._hits[(bucket, ip)]
        while dq and now - dq[0] >= window:
            dq.popleft()
        if len(dq) >= limit:
            return False
        dq.append(now)
        return True


limiter = RateLimiter()

# (лимит, окно в секундах)
READING_LIMITS = [(10, 3600), (30, 86400)]
QUESTION_LIMITS = [(30, 3600)]
ANALYZE_LIMITS = [(5, 86400)]


def rate_limit(name: str, limits: list[tuple[int, int]]):
    """Фабрика FastAPI-зависимости, ограничивающей запросы по IP."""

    def dependency(request: Request) -> None:
        if not settings.rate_limit_enabled:
            return
        ip = request.client.host if request.client else "unknown"
        for limit, window in limits:
            if not limiter.check(f"{name}:{window}", ip, limit, window):
                raise HTTPException(
                    status_code=429,
                    detail="Слишком много запросов. Попробуйте немного позже.",
                )

    return dependency
