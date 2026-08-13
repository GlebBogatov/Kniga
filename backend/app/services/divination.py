"""Расчёт выпавшего символа по вводу пользователя.

Режимы:
  - "8":     одна триграмма (для новичков);
  - "64":    гексаграмма из нижней + верхней триграмм;
  - "coins": шесть бросков трёх монет (значения 6/7/8/9, снизу вверх) ->
             первичная гексаграмма, изменяющиеся линии, вторичная гексаграмма.

Символы возвращаются как обычные dict (Pydantic-схемы формализуются в schemas.py).
"""
import secrets

from ..data.hexagrams import HEXAGRAMS, KING_WEN
from ..data.trigrams import TRIGRAMS, TRIGRAM_BY_LINES

# 6 — старый инь (инь, меняется); 7 — молодой ян; 8 — молодой инь;
# 9 — старый ян (ян, меняется). Значение -> (бит линии, признак изменения).
LINE_VALUES: dict[int, tuple[int, bool]] = {
    6: (0, True),
    7: (1, False),
    8: (0, False),
    9: (1, True),
}
VALID_TOSSES = frozenset(LINE_VALUES)


def trigram_symbol(trigram_id: str) -> dict:
    if trigram_id not in TRIGRAMS:
        raise ValueError(f"unknown trigram id: {trigram_id!r}")
    t = TRIGRAMS[trigram_id]
    return {
        "kind": "trigram",
        "id": t["id"], "name": t["name"], "hanzi": t["hanzi"],
        "lines": list(t["lines"]),
        "image": t["image"], "action": t["action"], "family": t["family"],
        "element": t["element"], "direction": t["direction"],
        "classic": t["classic"],
    }


def _trigram_brief(trigram_id: str) -> dict:
    """Компактное представление триграммы внутри гексаграммы."""
    t = TRIGRAMS[trigram_id]
    return {
        "id": t["id"], "name": t["name"], "hanzi": t["hanzi"],
        "lines": list(t["lines"]), "image": t["image"],
        "action": t["action"], "element": t["element"],
    }


def hexagram_number_from_lines(lines: list[int]) -> int:
    if len(lines) != 6 or any(b not in (0, 1) for b in lines):
        raise ValueError("hexagram requires 6 binary lines")
    lower_id = TRIGRAM_BY_LINES[tuple(lines[0:3])]
    upper_id = TRIGRAM_BY_LINES[tuple(lines[3:6])]
    return KING_WEN[lower_id][upper_id]


def hexagram_symbol(lower_id: str, upper_id: str) -> dict:
    if lower_id not in TRIGRAMS or upper_id not in TRIGRAMS:
        raise ValueError("unknown trigram id")
    number = KING_WEN[lower_id][upper_id]
    hx = HEXAGRAMS[number]
    lines = list(TRIGRAMS[lower_id]["lines"]) + list(TRIGRAMS[upper_id]["lines"])
    return {
        "kind": "hexagram",
        "number": number, "name": hx["name"], "title": hx["title"],
        "essence": hx["essence"], "lines": lines,
        "lower": _trigram_brief(lower_id), "upper": _trigram_brief(upper_id),
    }


def hexagram_symbol_by_number(number: int) -> dict:
    hx = HEXAGRAMS[number]
    return hexagram_symbol(hx["lower"], hx["upper"])


def virtual_toss() -> list[int]:
    """Виртуальный бросок 6 линий методом трёх монет.

    Каждая линия — сумма трёх монет (каждая 2 или 3 очка) -> {6,7,8,9}.
    Сохраняет классическое неравномерное распределение: 7 и 8 — по 3/8,
    6 и 9 — по 1/8. Источник случайности — secrets (не равномерный выбор
    из {6,7,8,9}, который сломал бы традиционные вероятности).
    """
    return [sum(secrets.randbelow(2) + 2 for _ in range(3)) for _ in range(6)]


def coins_symbol(tosses: list[int] | None) -> dict:
    if tosses is None:
        tosses = virtual_toss()
    if len(tosses) != 6 or any(v not in VALID_TOSSES for v in tosses):
        raise ValueError("tosses must be 6 values from {6,7,8,9}")

    primary_lines = [LINE_VALUES[v][0] for v in tosses]
    changing = [i for i, v in enumerate(tosses) if LINE_VALUES[v][1]]  # 0-based

    result = hexagram_symbol_by_number(hexagram_number_from_lines(primary_lines))
    result["tosses"] = list(tosses)
    result["changing_lines"] = [i + 1 for i in changing]  # индексы 1..6 снизу вверх

    if changing:
        secondary_lines = [
            (1 - b) if i in changing else b for i, b in enumerate(primary_lines)
        ]
        result["secondary"] = hexagram_symbol_by_number(
            hexagram_number_from_lines(secondary_lines)
        )
    else:
        result["secondary"] = None
    return result
