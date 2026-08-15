"""Бизнес-логика гадания и дневника: символ, промпт, вызов LLM, запись, анализ."""
import json

from sqlalchemy.orm import Session

from .. import schemas
from ..config import settings
from ..data.question_presets import PRESET_BY_SLUG
from ..models import ChatMessage, Reading
from . import content, prompts
from .divination import coins_symbol, hexagram_symbol, trigram_symbol
from .llm import LLMCallError, LLMService, LLMUnavailable, get_llm_service


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


def preset_focus_for(req: schemas.ReadingRequest) -> str | None:
    if req.preset_slug:
        preset = PRESET_BY_SLUG.get(req.preset_slug)
        if preset:
            return preset["prompt_focus"]
    return None


def create_reading(
    db: Session,
    req: schemas.ReadingRequest,
    llm: LLMService | None = None,
    *,
    preset_focus: str | None = None,
    user_id: int | None = None,
) -> dict:
    llm = llm or get_llm_service()
    symbol = build_symbol(req)
    is_coins = "changing_lines" in symbol
    if preset_focus is None:
        preset_focus = preset_focus_for(req)

    prompt = prompts.build_interpretation_prompt(
        symbol, req.question, style=req.style, preset_focus=preset_focus,
        content=content.effective_map(db),
    )
    schema = (
        schemas.COINS_INTERPRETATION_SCHEMA if is_coins else schemas.INTERPRETATION_SCHEMA
    )
    data = llm.call_structured(
        prompt, schema, model=settings.model_interpretation, max_tokens=1000
    )

    reading = Reading(
        user_id=user_id,
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


# --- Дневник ---


def list_journal(
    db: Session, limit: int = 100, offset: int = 0, *, user_id: int | None = None
) -> list[dict]:
    rows = (
        db.query(Reading)
        .filter(Reading.user_id == user_id)
        .order_by(Reading.created_at.desc(), Reading.id.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return [
        {
            "id": r.id,
            "ts": r.created_at.isoformat() if r.created_at else None,
            "mode": r.mode,
            "symbol_label": r.symbol_label,
            "element": r.element,
            "question": r.question,
            "interpretation": r.interpretation,
            "advice": r.advice,
        }
        for r in rows
    ]


def delete_reading(db: Session, reading_id: int, *, user_id: int | None = None) -> bool:
    row = db.get(Reading, reading_id)
    if row is None or row.user_id != user_id:
        return False
    db.delete(row)
    db.commit()
    return True


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def stream_reading(
    db: Session, req: schemas.ReadingRequest, llm: LLMService | None = None,
    *, user_id: int | None = None,
):
    """Генератор SSE: стримит текст толкования, затем добирает поля и сохраняет запись."""
    llm = llm or get_llm_service()
    try:
        symbol = build_symbol(req)
    except ValueError as exc:
        yield _sse("error", {"detail": str(exc)})
        return

    is_coins = "changing_lines" in symbol
    parts: list[str] = []
    try:
        stream_prompt = prompts.prompt_interpretation_stream(
            symbol, req.question, style=req.style, preset_focus=preset_focus_for(req),
            content=content.effective_map(db),
        )
        for chunk in llm.stream_text(
            stream_prompt, model=settings.model_interpretation, max_tokens=700
        ):
            parts.append(chunk)
            yield _sse("delta", {"text": chunk})

        interpretation = "".join(parts).strip()
        schema = schemas.COINS_TRAILER_SCHEMA if is_coins else schemas.TRAILER_SCHEMA
        trailer = llm.call_structured(
            prompts.prompt_trailer(symbol, req.question, interpretation, style=req.style),
            schema, model=settings.model_interpretation, max_tokens=400,
        )
    except (LLMUnavailable, LLMCallError):
        yield _sse("error", {"detail": "Толкование временно недоступно."})
        return

    reading = Reading(
        user_id=user_id,
        mode=req.mode, symbol_key=symbol_key(symbol), symbol_label=symbol_label(symbol),
        element=symbol_element(symbol), question=req.question, interpretation=interpretation,
        advice=trailer["advice"], caution=trailer["caution"], next_step=trailer["next_step"],
        prompt_snapshot=stream_prompt,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    done = {
        "reading_id": reading.id, "symbol": symbol, "interpretation": interpretation,
        "advice": trailer["advice"], "caution": trailer["caution"], "next_step": trailer["next_step"],
    }
    if is_coins:
        done["lines_commentary"] = trailer.get("lines_commentary", [])
    yield _sse("done", done)


CHAT_LIMIT = 5


def chat(db: Session, reading_id: int, message: str, llm: LLMService | None = None) -> dict:
    llm = llm or get_llm_service()
    reading = db.get(Reading, reading_id)
    if reading is None:
        raise LookupError("Гадание не найдено.")

    used = sum(1 for m in reading.messages if m.role == "user")
    if used >= CHAT_LIMIT:
        raise ValueError(f"Достигнут лимит уточнений ({CHAT_LIMIT}).")

    system = prompts.chat_system_prompt(
        reading.symbol_label, reading.question, reading.interpretation, reading.advice
    )
    history = [{"role": m.role, "content": m.content} for m in reading.messages]
    messages = history + [{"role": "user", "content": message}]

    reply = llm.call_text(
        system, messages, model=settings.model_interpretation, max_tokens=1000
    )

    db.add(ChatMessage(reading_id=reading_id, role="user", content=message))
    db.add(ChatMessage(reading_id=reading_id, role="assistant", content=reply))
    db.commit()

    return {"reply": reply, "remaining": CHAT_LIMIT - (used + 1)}


def analyze_journal(
    db: Session, llm: LLMService | None = None, *, user_id: int | None = None
) -> dict:
    llm = llm or get_llm_service()
    rows = (
        db.query(Reading)
        .filter(Reading.user_id == user_id)
        .order_by(Reading.created_at.desc(), Reading.id.desc())
        .all()
    )
    if len(rows) < 2:
        raise ValueError("Для анализа нужно минимум 2 записи в дневнике.")

    entries = [
        {
            "date": r.created_at.isoformat() if r.created_at else None,
            "symbol": r.symbol_label,
            "element": r.element,
            "question": r.question,
        }
        for r in rows
    ]
    prompt = prompts.journal_analysis_prompt(json.dumps(entries, ensure_ascii=False))
    data = llm.call_structured(
        prompt, schemas.JOURNAL_ANALYSIS_SCHEMA,
        model=settings.model_interpretation, max_tokens=1500,
    )
    return {"analysis_markdown": data["analysis_markdown"]}
