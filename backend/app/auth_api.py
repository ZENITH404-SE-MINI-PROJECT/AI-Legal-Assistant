"""Registration, login, profile and data-deletion endpoints."""
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import schemas, security
from .database import get_db
from .deps import get_current_user
from .models import Conversation, LegalDocument, User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.TokenOut, status_code=201)
def register(body: schemas.RegisterIn, db: Session = Depends(get_db)):
    if not security.valid_username(body.username):
        raise HTTPException(422, "Username must be 3-50 characters: letters, digits, _ . -")
    if not security.valid_password(body.password):
        raise HTTPException(422, "Password must be 8+ characters with at least one letter and one digit")
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(409, "Username already taken")
    # Self-registration can only ever create Standard Users (RBAC, SRS 6.3)
    user = User(username=body.username, password_hash=security.hash_password(body.password), role="user")
    db.add(user)
    db.commit()
    return schemas.TokenOut(access_token=security.create_token(user.id, user.role),
                            role=user.role, username=user.username)


@router.post("/login", response_model=schemas.TokenOut)
def login(body: schemas.LoginIn, db: Session = Depends(get_db)):
    if security.is_locked(body.username):
        raise HTTPException(429, "Too many failed attempts. Try again in a few minutes.")
    user = db.query(User).filter(User.username == body.username).first()
    if user is None or not security.verify_password(body.password, user.password_hash):
        security.record_failure(body.username)
        raise HTTPException(401, "Invalid username or password")
    security.clear_failures(body.username)
    return schemas.TokenOut(access_token=security.create_token(user.id, user.role),
                            role=user.role, username=user.username)


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "username": user.username, "role": user.role}


@router.delete("/me/data", status_code=204)
def delete_my_data(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Right to erasure: delete the caller's conversations and uploaded documents."""
    for doc in db.query(LegalDocument).filter(LegalDocument.user_id == user.id).all():
        _remove_file(doc.file_path)
        db.delete(doc)
    for conv in db.query(Conversation).filter(Conversation.user_id == user.id).all():
        db.delete(conv)
    db.commit()


def _remove_file(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass
