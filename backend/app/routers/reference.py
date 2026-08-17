"""Справочник символов и пресетов. Пресеты — из БД (CMS) с фолбэком на код."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..data.hexagrams import HEXAGRAMS
from ..data.trigrams import TRIGRAMS
from ..db import get_db
from ..services import presets as presets_svc

router = APIRouter(tags=["reference"])


def _trigram(t: dict) -> dict:
    return {**t, "lines": list(t["lines"])}


@router.get("/trigrams")
def list_trigrams() -> list[dict]:
    return [_trigram(t) for t in TRIGRAMS.values()]


@router.get("/trigrams/{trigram_id}")
def get_trigram(trigram_id: str) -> dict:
    t = TRIGRAMS.get(trigram_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Триграмма не найдена.")
    return _trigram(t)


@router.get("/hexagrams")
def list_hexagrams() -> list[dict]:
    return list(HEXAGRAMS.values())


@router.get("/hexagrams/{number}")
def get_hexagram(number: int) -> dict:
    hx = HEXAGRAMS.get(number)
    if hx is None:
        raise HTTPException(status_code=404, detail="Гексаграмма не найдена.")
    return hx


@router.get("/presets")
def list_presets(
    topic: str | None = Query(None), db: Session = Depends(get_db)
) -> list[dict]:
    return presets_svc.effective(db, topic)


@router.get("/presets/{slug}")
def get_preset(slug: str, db: Session = Depends(get_db)) -> dict:
    p = presets_svc.by_slug(db, slug)
    if p is None:
        raise HTTPException(status_code=404, detail="Пресет не найден.")
    return p
