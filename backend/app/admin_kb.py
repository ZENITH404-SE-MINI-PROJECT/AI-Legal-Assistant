"""Administrator tools: knowledge base, templates, feedback, users (FR-16..FR-19)."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import classifier, schemas
from .database import get_db
from .deps import require_admin
from .models import CaseReference, Feedback, Message, Template, User

router = APIRouter(prefix="/admin", tags=["admin"])


def _check_reference(body: schemas.ReferenceIn):
    if body.entry_type not in ("case", "procedure"):
        raise HTTPException(422, "entry_type must be 'case' or 'procedure'")
    if body.domain not in classifier.supported_domains():
        raise HTTPException(422, "Unsupported domain. Allowed: " + ", ".join(classifier.supported_domains()))


# ---- knowledge base (FR-16) ----
@router.get("/references")
def list_refs(entry_type: Optional[str] = None, _=Depends(require_admin), db: Session = Depends(get_db)):
    q = db.query(CaseReference)
    if entry_type:
        q = q.filter(CaseReference.entry_type == entry_type)
    return [{c.name: getattr(r, c.name) for c in CaseReference.__table__.columns} for r in q.all()]


@router.post("/references", status_code=201)
def create_ref(body: schemas.ReferenceIn, _=Depends(require_admin), db: Session = Depends(get_db)):
    _check_reference(body)
    ref = CaseReference(**body.model_dump())
    db.add(ref)
    db.commit()
    return {"id": ref.id}


@router.put("/references/{rid}")
def update_ref(rid: int, body: schemas.ReferenceIn, _=Depends(require_admin), db: Session = Depends(get_db)):
    _check_reference(body)
    ref = db.get(CaseReference, rid)
    if ref is None:
        raise HTTPException(404, "Reference not found")
    for k, v in body.model_dump().items():
        setattr(ref, k, v)
    db.commit()
    return {"id": ref.id}


@router.delete("/references/{rid}", status_code=204)
def delete_ref(rid: int, _=Depends(require_admin), db: Session = Depends(get_db)):
    ref = db.get(CaseReference, rid)
    if ref is None:
        raise HTTPException(404, "Reference not found")
    db.delete(ref)
    db.commit()


# ---- templates (FR-17) ----
@router.post("/templates", status_code=201)
def create_template(body: schemas.TemplateIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    t = Template(**body.model_dump(), created_by=admin.id)
    db.add(t)
    db.commit()
    return {"id": t.id}


@router.put("/templates/{tid}")
def update_template(tid: int, body: schemas.TemplateIn, _=Depends(require_admin), db: Session = Depends(get_db)):
    t = db.get(Template, tid)
    if t is None:
        raise HTTPException(404, "Template not found")
    for k, v in body.model_dump().items():
        setattr(t, k, v)
    db.commit()
    return {"id": t.id}


@router.delete("/templates/{tid}", status_code=204)
def delete_template(tid: int, _=Depends(require_admin), db: Session = Depends(get_db)):
    t = db.get(Template, tid)
    if t is None:
        raise HTTPException(404, "Template not found")
    db.delete(t)
    db.commit()


# ---- feedback review (FR-18) ----
@router.get("/feedback")
def list_feedback(unresolved_only: bool = False, _=Depends(require_admin), db: Session = Depends(get_db)):
    q = db.query(Feedback)
    if unresolved_only:
        q = q.filter(Feedback.resolved.is_(False))
    out = []
    for f in q.order_by(Feedback.created_at.desc()).all():
        msg = db.get(Message, f.message_id)
        out.append({"id": f.id, "message_id": f.message_id, "rating": f.rating, "comment": f.comment,
                    "is_error_report": f.is_error_report, "resolved": f.resolved,
                    "admin_note": f.admin_note, "response_text": msg.content if msg else None})
    return out


@router.put("/feedback/{fid}")
def resolve_feedback(fid: int, body: schemas.FeedbackResolveIn, _=Depends(require_admin),
                     db: Session = Depends(get_db)):
    f = db.get(Feedback, fid)
    if f is None:
        raise HTTPException(404, "Feedback not found")
    f.resolved, f.admin_note = body.resolved, body.admin_note
    db.commit()
    return {"id": f.id, "resolved": f.resolved}


# ---- user management (FR-19) ----
@router.get("/users")
def list_users(_=Depends(require_admin), db: Session = Depends(get_db)):
    return [{"id": u.id, "username": u.username, "role": u.role, "created_at": u.created_at.isoformat()}
            for u in db.query(User).order_by(User.created_at).all()]


@router.put("/users/{uid}/role")
def set_role(uid: str, body: schemas.RoleIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    if body.role not in ("user", "admin"):
        raise HTTPException(422, "role must be 'user' or 'admin'")
    u = db.get(User, uid)
    if u is None:
        raise HTTPException(404, "User not found")
    if u.id == admin.id and body.role != "admin":
        raise HTTPException(400, "Admins cannot demote themselves")
    u.role = body.role
    db.commit()
    return {"id": u.id, "role": u.role}


@router.delete("/users/{uid}", status_code=204)
def delete_user(uid: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    u = db.get(User, uid)
    if u is None:
        raise HTTPException(404, "User not found")
    if u.id == admin.id:
        raise HTTPException(400, "Admins cannot delete themselves")
    db.delete(u)
    db.commit()
