"""Pydantic-схемы запросов и JSON-схемы для структурированного вывода LLM.

JSON-схемы передаются в output_config.format — модель возвращает
провалидированный объект, ручной парсинг ```json-ограждений не нужен.
Ограничения structured outputs: additionalProperties=false, без min/maxLength.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

TrigramId = Literal["qian", "kun", "zhen", "xun", "kan", "li", "gen", "dui"]
Mode = Literal["8", "64", "coins"]
Style = Literal["classic", "modern", "short"]


class ReadingRequest(BaseModel):
    mode: Mode
    question: str = Field(min_length=3, max_length=500)
    trigram_id: Optional[TrigramId] = None
    lower_id: Optional[TrigramId] = None
    upper_id: Optional[TrigramId] = None
    tosses: Optional[list[int]] = None
    preset_slug: Optional[str] = None
    style: Optional[Style] = None

    @model_validator(mode="after")
    def _check_fields_for_mode(self) -> "ReadingRequest":
        if self.mode == "8":
            if not self.trigram_id:
                raise ValueError("mode=8 требует trigram_id")
        elif self.mode == "64":
            if not (self.lower_id and self.upper_id):
                raise ValueError("mode=64 требует lower_id и upper_id")
        elif self.mode == "coins":
            if self.tosses is not None:
                if len(self.tosses) != 6 or any(v not in (6, 7, 8, 9) for v in self.tosses):
                    raise ValueError("tosses — 6 значений из {6,7,8,9} или null")
        return self


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)


class QuestionCheckRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


# --- JSON-схемы структурированного вывода ---

INTERPRETATION_SCHEMA = {
    "type": "object",
    "properties": {
        "interpretation": {"type": "string"},
        "advice": {"type": "string"},
        "caution": {"type": "string"},
        "next_step": {"type": "string"},
    },
    "required": ["interpretation", "advice", "caution", "next_step"],
    "additionalProperties": False,
}

COINS_INTERPRETATION_SCHEMA = {
    "type": "object",
    "properties": {
        "interpretation": {"type": "string"},
        "advice": {"type": "string"},
        "caution": {"type": "string"},
        "next_step": {"type": "string"},
        "lines_commentary": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "line": {"type": "integer"},
                    "text": {"type": "string"},
                },
                "required": ["line", "text"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["interpretation", "advice", "caution", "next_step", "lines_commentary"],
    "additionalProperties": False,
}

# Трейлер для стриминга: interpretation стримится текстом отдельно,
# остальные поля добираются компактным вторым вызовом.
TRAILER_SCHEMA = {
    "type": "object",
    "properties": {
        "advice": {"type": "string"},
        "caution": {"type": "string"},
        "next_step": {"type": "string"},
    },
    "required": ["advice", "caution", "next_step"],
    "additionalProperties": False,
}

COINS_TRAILER_SCHEMA = {
    "type": "object",
    "properties": {
        "advice": {"type": "string"},
        "caution": {"type": "string"},
        "next_step": {"type": "string"},
        "lines_commentary": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "line": {"type": "integer"},
                    "text": {"type": "string"},
                },
                "required": ["line", "text"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["advice", "caution", "next_step", "lines_commentary"],
    "additionalProperties": False,
}

QUESTION_CHECK_SCHEMA = {
    "type": "object",
    "properties": {
        "quality": {"type": "string", "enum": ["good", "vague", "yes_no_ok"]},
        "hint": {"type": "string"},
        "crisis": {"type": "boolean"},
    },
    "required": ["quality", "hint", "crisis"],
    "additionalProperties": False,
}

JOURNAL_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {"analysis_markdown": {"type": "string"}},
    "required": ["analysis_markdown"],
    "additionalProperties": False,
}
