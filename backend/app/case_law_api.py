"""Case law search by keyword, jurisdiction or citation (FR-09)."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .database import get_db
from .deps import get_current_user
from .models import CaseReference, User

router = APIRouter(prefix="/case-law", tags=["case-law"])


def _like(term: str) -> str:
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


@router.get("")
def search_case_law(q: Optional[str] = Query(None, max_length=200),
                    jurisdiction: Optional[str] = Query(None, max_length=60),
                    citation: Optional[str] = Query(None, max_length=120),
                    limit: int = Query(20, ge=1, le=50),
                    _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(CaseReference).filter(CaseReference.entry_type == "case")
    if q:
        pat = _like(q.strip())
        query = query.filter(or_(CaseReference.title.ilike(pat, escape="\\"),
                                 CaseReference.keywords.ilike(pat, escape="\\"),
                                 CaseReference.summary.ilike(pat, escape="\\")))
    if jurisdiction:
        query = query.filter(CaseReference.jurisdiction.ilike(_like(jurisdiction.strip()), escape="\\"))
    if citation:
        query = query.filter(CaseReference.citation.ilike(_like(citation.strip()), escape="\\"))
    rows = query.order_by(CaseReference.title).limit(limit).all()
    return [{"id": r.id, "title": r.title, "citation": r.citation, "jurisdiction": r.jurisdiction,
             "domain": r.domain, "summary": r.summary} for r in rows]
