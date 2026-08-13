"""Тематические пресеты вопросов (каталог формулировок).

Это заглушечный стартовый набор (по 1 на тему). Контент-редактор (Таня)
расширяет до 40–60 пресетов, 5–8 на тему. `prompt_focus` подставляется в
промпт толкования дополнительной строкой; `question_template` — редактируемый
текст, который подставляется в поле вопроса.
"""
from typing import TypedDict


class Preset(TypedDict):
    slug: str
    topic: str
    title: str
    subtitle: str
    question_template: str
    prompt_focus: str


PRESETS: list[Preset] = [
    {
        "slug": "stoit-li-menyat-rabotu",
        "topic": "career",
        "title": "Стоит ли менять работу",
        "subtitle": "Текущее место, новое, риски и сроки",
        "question_template": "Стоит ли мне менять работу этой весной?",
        "prompt_focus": "Разбирай в плоскости карьеры: текущее положение, риски перехода, сроки.",
    },
    {
        "slug": "vosstanavlivat-li-otnosheniya",
        "topic": "love",
        "title": "Восстанавливать ли отношения",
        "subtitle": "Чувства, границы, реалистичность",
        "question_template": "Стоит ли пытаться восстановить эти отношения?",
        "prompt_focus": "Разбирай в плоскости отношений: чувства, границы, реалистичность шага.",
    },
    {
        "slug": "kuda-uhodyat-dengi",
        "topic": "finance",
        "title": "Куда уходят деньги",
        "subtitle": "Привычки, приоритеты, устойчивость",
        "question_template": "Почему мне не удаётся откладывать деньги?",
        "prompt_focus": "Разбирай в плоскости финансов: привычки, приоритеты, устойчивость.",
    },
    {
        "slug": "stoit-li-pereezzhat",
        "topic": "change",
        "title": "Стоит ли переезжать",
        "subtitle": "Готовность, ресурсы, сроки",
        "question_template": "Стоит ли мне переезжать в другой город?",
        "prompt_focus": "Разбирай в плоскости перемен и переезда: готовность, ресурсы, сроки.",
    },
    {
        "slug": "kak-najti-prizvanie",
        "topic": "self",
        "title": "Как найти призвание",
        "subtitle": "Сильные стороны, интерес, смысл",
        "question_template": "В какой сфере мне стоит развиваться?",
        "prompt_focus": "Разбирай в плоскости самопознания: сильные стороны, интерес, смысл.",
    },
]

PRESET_BY_SLUG: dict[str, Preset] = {p["slug"]: p for p in PRESETS}
