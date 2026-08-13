"""Справочник символов и пресетов (данные уже в коде)."""
from fastapi import APIRouter, HTTPException, Query

from ..data.hexagrams import HEXAGRAMS
from ..data.question_presets import PRESET_BY_SLUG, PRESETS
from ..data.trigrams import TRIGRAMS

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
def list_presets(topic: str | None = Query(None)) -> list[dict]:
    return [p for p in PRESETS if topic is None or p["topic"] == topic]


@router.get("/presets/{slug}")
def get_preset(slug: str) -> dict:
    p = PRESET_BY_SLUG.get(slug)
    if p is None:
        raise HTTPException(status_code=404, detail="Пресет не найден.")
    return p
