"""CMS-контент: эффективные значения, черновик → публикация, версии, предпросмотр.

Эффективное значение = опубликованное (если есть) либо дефолт из реестра.
Промпты берут `effective_map(db)` — правки Тани применяются без выката кода.
"""
from sqlalchemy.orm import Session

from ..data.content import CONTENT_DEFAULTS, CONTENT_REGISTRY
from ..models import ContentItem, ContentVersion
from . import prompts
from .divination import trigram_symbol


def effective_map(db: Session) -> dict[str, str]:
    """Ключ → опубликованное значение либо дефолт (для генерации ответов)."""
    rows = {r.key: r for r in db.query(ContentItem).all()}
    out: dict[str, str] = {}
    for key, default in CONTENT_DEFAULTS.items():
        row = rows.get(key)
        out[key] = row.published if (row and row.published is not None) else default
    return out


def draft_map(db: Session) -> dict[str, str]:
    """Ключ → черновик (если есть) либо эффективное значение."""
    rows = {r.key: r for r in db.query(ContentItem).all()}
    eff = effective_map(db)
    out: dict[str, str] = {}
    for key in CONTENT_DEFAULTS:
        row = rows.get(key)
        out[key] = row.draft if (row and row.draft is not None) else eff[key]
    return out


def list_for_editor(db: Session) -> list[dict]:
    rows = {r.key: r for r in db.query(ContentItem).all()}
    items = []
    for field in CONTENT_REGISTRY:
        row = rows.get(field["key"])
        published = row.published if (row and row.published is not None) else None
        draft = row.draft if (row and row.draft is not None) else None
        items.append(
            {
                **field,
                "published": published,
                "draft": draft,
                "effective": published if published is not None else field["default"],
                "dirty": draft is not None and draft != (published if published is not None else field["default"]),
            }
        )
    return items


def _get_or_create(db: Session, key: str) -> ContentItem:
    row = db.get(ContentItem, key)
    if row is None:
        row = ContentItem(key=key)
        db.add(row)
        db.flush()
    return row


def save_draft(db: Session, key: str, value: str) -> None:
    if key not in CONTENT_DEFAULTS:
        raise ValueError("Неизвестный ключ контента.")
    row = _get_or_create(db, key)
    row.draft = value
    db.commit()


def publish(db: Session, key: str) -> None:
    if key not in CONTENT_DEFAULTS:
        raise ValueError("Неизвестный ключ контента.")
    row = _get_or_create(db, key)
    value = row.draft if row.draft is not None else CONTENT_DEFAULTS[key]
    row.published = value
    db.add(ContentVersion(key=key, value=value))
    db.commit()


def revert(db: Session, key: str) -> None:
    """Сбросить черновик к опубликованному (или дефолту)."""
    row = db.get(ContentItem, key)
    if row is not None:
        row.draft = None
        db.commit()


def versions(db: Session, key: str) -> list[dict]:
    rows = (
        db.query(ContentVersion)
        .filter_by(key=key)
        .order_by(ContentVersion.created_at.desc(), ContentVersion.id.desc())
        .all()
    )
    return [
        {"id": v.id, "value": v.value, "created_at": v.created_at.isoformat() if v.created_at else None}
        for v in rows
    ]


def restore(db: Session, key: str, version_id: int) -> None:
    v = db.get(ContentVersion, version_id)
    if v is None or v.key != key:
        raise ValueError("Версия не найдена.")
    row = _get_or_create(db, key)
    row.draft = v.value
    db.commit()


def preview(db: Session, question: str) -> dict:
    """Собрать промпты по ЧЕРНОВИКУ контента — чтобы Таня увидела эффект.

    Без вызова ИИ: показываем сам текст инструкций (толкование + проверка).
    """
    content = draft_map(db)
    symbol = trigram_symbol("qian")
    return {
        "interpretation_prompt": prompts.build_interpretation_prompt(
            symbol, question, content=content
        ),
        "question_check_prompt": prompts.question_check_prompt(question, content),
    }
