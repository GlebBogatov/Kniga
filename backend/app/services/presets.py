"""Пресеты вопросов из БД (CMS Тани) с фолбэком на дефолты из кода.

Пока Таня не тронула пресеты — используется стартовый набор
`data/question_presets.PRESETS`. При редактировании набор сидируется в БД,
и дальше источником становится БД.
"""
import re
import secrets

from sqlalchemy.orm import Session

from ..data.question_presets import PRESETS as DEFAULT_PRESETS
from ..models import PresetItem

PUBLIC_FIELDS = ("slug", "topic", "title", "subtitle", "question_template", "prompt_focus")


def _public(row: PresetItem) -> dict:
    return {f: getattr(row, f) for f in PUBLIC_FIELDS}


def _admin(row: PresetItem) -> dict:
    return {**_public(row), "id": row.id, "sort_order": row.sort_order, "is_active": row.is_active}


def _slugify(title: str) -> str:
    base = re.sub(r"[^a-zа-я0-9]+", "-", (title or "").lower()).strip("-")[:48]
    return f"{base or 'preset'}-{secrets.token_hex(3)}"


def ensure_seeded(db: Session) -> None:
    if db.query(PresetItem).count() == 0:
        for i, p in enumerate(DEFAULT_PRESETS):
            db.add(PresetItem(sort_order=i, is_active=True, **p))
        db.commit()


def effective(db: Session, topic: str | None = None) -> list[dict]:
    rows = (
        db.query(PresetItem)
        .filter(PresetItem.is_active == True)  # noqa: E712
        .order_by(PresetItem.sort_order, PresetItem.id)
        .all()
    )
    if not rows:
        items = [dict(p) for p in DEFAULT_PRESETS]
    else:
        items = [_public(r) for r in rows]
    return [p for p in items if topic is None or p["topic"] == topic]


def by_slug(db: Session, slug: str) -> dict | None:
    row = db.query(PresetItem).filter_by(slug=slug, is_active=True).one_or_none()
    if row is not None:
        return _public(row)
    for p in DEFAULT_PRESETS:
        if p["slug"] == slug:
            return dict(p)
    return None


def focus_for(db: Session, slug: str | None) -> str | None:
    if not slug:
        return None
    p = by_slug(db, slug)
    return p["prompt_focus"] if p else None


# --- Редактирование (CMS) ---


def list_for_editor(db: Session) -> list[dict]:
    ensure_seeded(db)
    rows = db.query(PresetItem).order_by(PresetItem.sort_order, PresetItem.id).all()
    return [_admin(r) for r in rows]


def create(db: Session, data: dict) -> dict:
    order = (db.query(PresetItem).count())
    row = PresetItem(
        slug=data.get("slug") or _slugify(data.get("title", "")),
        topic=data.get("topic", "other"),
        title=data.get("title", ""),
        subtitle=data.get("subtitle", ""),
        question_template=data.get("question_template", ""),
        prompt_focus=data.get("prompt_focus", ""),
        sort_order=order,
        is_active=data.get("is_active", True),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _admin(row)


def update(db: Session, preset_id: int, data: dict) -> dict | None:
    row = db.get(PresetItem, preset_id)
    if row is None:
        return None
    for field in ("topic", "title", "subtitle", "question_template", "prompt_focus", "is_active", "sort_order"):
        if field in data and data[field] is not None:
            setattr(row, field, data[field])
    db.commit()
    db.refresh(row)
    return _admin(row)


def delete(db: Session, preset_id: int) -> bool:
    row = db.get(PresetItem, preset_id)
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True
