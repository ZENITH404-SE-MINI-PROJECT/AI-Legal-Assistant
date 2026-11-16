"""Template library: browse, fill, download (FR-11, FR-12)."""
import io
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import or_
from sqlalchemy.orm import Session

from . import schemas
from .database import get_db
from .deps import get_current_user
from .models import Template, User

router = APIRouter(prefix="/templates", tags=["templates"])
PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z0-9_ ]+?)\s*\}\}")


def placeholders(body: str) -> list:
    seen, out = set(), []
    for name in PLACEHOLDER.findall(body):
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


def fill_template(body: str, values: dict) -> str:
    missing = [p for p in placeholders(body) if not str(values.get(p, "")).strip()]
    if missing:
        raise ValueError("Missing values for: " + ", ".join(missing))
    return PLACEHOLDER.sub(lambda m: str(values[m.group(1)]).strip(), body)


@router.get("")
def list_templates(q: Optional[str] = Query(None, max_length=100),
                   category: Optional[str] = Query(None, max_length=40),
                   _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Template)
    if q:
        pat = f"%{q.strip()}%"
        query = query.filter(or_(Template.title.ilike(pat), Template.description.ilike(pat)))
    if category:
        query = query.filter(Template.category == category)
    return [{"id": t.id, "title": t.title, "category": t.category, "description": t.description}
            for t in query.order_by(Template.title).all()]


def _get(db: Session, tid: int) -> Template:
    t = db.get(Template, tid)
    if t is None:
        raise HTTPException(404, "Template not found")
    return t


@router.get("/{tid}")
def get_template(tid: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    t = _get(db, tid)
    return {"id": t.id, "title": t.title, "category": t.category, "description": t.description,
            "placeholders": placeholders(t.body)}


@router.post("/{tid}/fill")
def fill(tid: int, body: schemas.FillIn, fmt: str = Query("txt", pattern="^(txt|docx)$"),
         _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    t = _get(db, tid)
    try:
        text = fill_template(t.body, body.values)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", t.title)
    if fmt == "docx":
        from docx import Document
        doc = Document()
        for line in text.split("\n"):
            doc.add_paragraph(line)
        buf = io.BytesIO()
        doc.save(buf)
        return Response(buf.getvalue(), headers={"Content-Disposition": f'attachment; filename="{safe}.docx"'},
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    return Response(text, media_type="text/plain; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{safe}.txt"'})
