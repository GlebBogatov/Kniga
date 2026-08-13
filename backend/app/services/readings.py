"""Бизнес-логика гадания: сборка символа, промпта, вызов LLM, сохранение записи."""
from sqlalchemy.orm import Session

from .. import schemas
from ..config import settings
from ..models import Reading
from . import prompts
from .divination import coins_symbol, hexagram_symbol, trigram_symbol
from .llm import LLMService, get_llm_service


def build_symbol(req: schemas.ReadingRequest) -> dict:
    if req.mode == "8":
        return trigram_symbol(req.trigram_id)
    if req.mode == "64":
        return hexagram_symbol(req.lower_id, req.upper_id)
    return coins_symbol(req.tosses)


def symbol_key(symbol: dict) -> str:
    if symbol["kind"] == "trigram":
        return symbol["id"]
    return f"{symbol['lower']['id']}+{symbol['upper']['id']}"


def symbol_label(symbol: dict) -> str:
    if symbol["kind"] == "trigram":
        return f"Триграмма {symbol['name']} ({symbol['image']})"
    return f"Гексаграмма №{symbol['number']} {symbol['name']} «{symbol['title']}»"


def symbol_element(symbol: dict) -> str:
    if symbol["kind"] == "trigram":
        return symbol["element"]
    return f"{symbol['lower']['element']} / {symbol['upper']['element']}"


def create_reading(
    db: Session,
    req: schemas.ReadingRequest,
    llm: LLMService | None = None,
    *,
    preset_focus: str | None = None,
) -> dict:
    llm = llm or get_llm_service()
    symbol = build_symbol(req)
    is_coins = "changing_lines" in symbol

    prompt = prompts.build_interpretation_prompt(
        symbol, req.question, style=req.style, preset_focus=preset_focus
    )
    schema = (
        schemas.COINS_INTERPRETATION_SCHEMA if is_coins else schemas.INTERPRETATION_SCHEMA
    )
    data = llm.call_structured(
        prompt, schema, model=settings.model_interpretation, max_tokens=1000
    )

    reading = Reading(
        mode=req.mode,
        symbol_key=symbol_key(symbol),
        symbol_label=symbol_label(symbol),
        element=symbol_element(symbol),
        question=req.question,
        interpretation=data["interpretation"],
        advice=data["advice"],
        caution=data["caution"],
        next_step=data["next_step"],
        prompt_snapshot=prompt,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    response = {
        "reading_id": reading.id,
        "symbol": symbol,
        "interpretation": data["interpretation"],
        "advice": data["advice"],
        "caution": data["caution"],
        "next_step": data["next_step"],
    }
    if is_coins:
        response["lines_commentary"] = data.get("lines_commentary", [])
    return response
