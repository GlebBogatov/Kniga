"""Health-check. Liveness сейчас; /health/llm — на этапе 4."""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}
