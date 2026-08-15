"""CMS Тани: /api/cms/* (роль editor или admin) + публичный /api/content.

Позволяет редактировать «настройку ответов» (промпты, критерии проверки,
тон, безопасность) без выката кода: черновик → публикация, версии, откат,
предпросмотр собранного промпта.
"""
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_roles
from ..models import User
from ..services import content

router = APIRouter(tags=["cms"])
editor = require_roles("editor", "admin")


@router.get("/content")
def public_content(db: Session = Depends(get_db)) -> dict:
    """Опубликованные значения (эффективные) — публично."""
    return content.effective_map(db)


@router.get("/cms/content")
def list_content(_: User = Depends(editor), db: Session = Depends(get_db)) -> list[dict]:
    return content.list_for_editor(db)


@router.put("/cms/content/{key}")
def save_draft(
    key: str,
    value: str = Body(..., embed=True),
    _: User = Depends(editor),
    db: Session = Depends(get_db),
) -> dict:
    try:
        content.save_draft(db, key, value)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"ok": True}


@router.post("/cms/content/{key}/publish")
def publish(key: str, _: User = Depends(editor), db: Session = Depends(get_db)) -> dict:
    try:
        content.publish(db, key)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"ok": True}


@router.post("/cms/content/{key}/revert")
def revert(key: str, _: User = Depends(editor), db: Session = Depends(get_db)) -> dict:
    content.revert(db, key)
    return {"ok": True}


@router.get("/cms/content/{key}/versions")
def versions(key: str, _: User = Depends(editor), db: Session = Depends(get_db)) -> list[dict]:
    return content.versions(db, key)


@router.post("/cms/content/{key}/restore/{version_id}")
def restore(
    key: str,
    version_id: int,
    _: User = Depends(editor),
    db: Session = Depends(get_db),
) -> dict:
    try:
        content.restore(db, key, version_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"ok": True}


@router.post("/cms/preview")
def preview(
    question: str = Body("Стоит ли мне менять работу этой весной?", embed=True),
    _: User = Depends(editor),
    db: Session = Depends(get_db),
) -> dict:
    return content.preview(db, question)
