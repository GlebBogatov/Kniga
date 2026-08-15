"""Реестр редактируемого контента для CMS Тани.

Ключи с дефолтами (из текущего кода). Таня редактирует значения через админку
(черновик → публикация), логика их только подставляет. Дефолт используется,
пока значение не опубликовано.
"""
from typing import TypedDict

from .question_check import QUESTION_CHECK_CRITERIA

SAFETY_DEFAULT = (
    "Важно: не давай медицинских, юридических или финансовых предписаний; "
    "не предсказывай смерть, диагнозы и исход болезни. Если вопрос касается "
    "здоровья, самоповреждения или острого кризиса — мягко порекомендуй "
    "обратиться к профильному специалисту вместо толкования."
)


class ContentField(TypedDict):
    key: str
    group: str
    label: str
    multiline: bool
    default: str


CONTENT_REGISTRY: list[ContentField] = [
    {
        "key": "safety",
        "group": "Безопасность",
        "label": "Блок безопасности (добавляется во все ответы ИИ)",
        "multiline": True,
        "default": SAFETY_DEFAULT,
    },
    {
        "key": "tone",
        "group": "Тон толкования",
        "label": "Дополнительное указание о тоне (необязательно)",
        "multiline": True,
        "default": "",
    },
    {
        "key": "qc_good",
        "group": "Проверка вопроса",
        "label": "Признак хорошего вопроса",
        "multiline": False,
        "default": QUESTION_CHECK_CRITERIA["good"],
    },
    {
        "key": "qc_good_example",
        "group": "Проверка вопроса",
        "label": "Пример хорошего вопроса",
        "multiline": False,
        "default": QUESTION_CHECK_CRITERIA["good_example"],
    },
    {
        "key": "qc_vague",
        "group": "Проверка вопроса",
        "label": "Признак расплывчатого вопроса",
        "multiline": False,
        "default": QUESTION_CHECK_CRITERIA["vague"],
    },
    {
        "key": "qc_vague_example",
        "group": "Проверка вопроса",
        "label": "Пример расплывчатого вопроса",
        "multiline": False,
        "default": QUESTION_CHECK_CRITERIA["vague_example"],
    },
    {
        "key": "qc_hint",
        "group": "Проверка вопроса",
        "label": "Как писать подсказку при расплывчатом вопросе",
        "multiline": False,
        "default": QUESTION_CHECK_CRITERIA["hint_instruction"],
    },
    {
        "key": "qc_crisis",
        "group": "Проверка вопроса",
        "label": "Что считать кризисным вопросом",
        "multiline": True,
        "default": QUESTION_CHECK_CRITERIA["crisis"],
    },
]

CONTENT_DEFAULTS: dict[str, str] = {f["key"]: f["default"] for f in CONTENT_REGISTRY}
