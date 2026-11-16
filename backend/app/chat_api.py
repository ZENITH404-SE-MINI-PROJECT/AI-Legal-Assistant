"""Conversational legal assistant: validate -> classify -> retrieve -> generate (SRS 5.1)."""
import json
import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import classifier, config, llm_service, retrieval, schemas
from .database import get_db
from .deps import get_current_user
from .models import Conversation, Message, User

router = APIRouter(prefix="/chat", tags=["chat"])

_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def validate_query(raw: str) -> str:
    """FR-02: length and content checks. Returns cleaned text or raises ValueError."""
    text = _CTRL.sub("", raw or "").strip()
    if len(text) < config.MIN_QUERY_CHARS:
        raise ValueError(f"Question is too short (minimum {config.MIN_QUERY_CHARS} characters).")
    if len(text) > config.MAX_QUERY_CHARS:
        raise ValueError(f"Question is too long (maximum {config.MAX_QUERY_CHARS} characters).")
    if not re.search(r"[A-Za-z]{3}", text):
        raise ValueError("Please enter your question in words.")
    return text


def _history(conv: Optional[Conversation]) -> List[dict]:
    if conv is None:
        return []
    msgs = conv.messages[-config.HISTORY_WINDOW:]
    return [{"role": m.role, "content": m.content, "domain": m.domain} for m in msgs]


def _get_owned_conversation(db: Session, user: User, cid: str) -> Conversation:
    conv = db.get(Conversation, cid)
    if conv is None or conv.user_id != user.id:
        raise HTTPException(404, "Conversation not found")
    return conv


@router.post("/ask", response_model=schemas.AskOut)
def ask(body: schemas.AskIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        question = validate_query(body.question)
    except ValueError as exc:
        raise HTTPException(422, str(exc))

    conv = _get_owned_conversation(db, user, body.conversation_id) if body.conversation_id else None
    history = _history(conv)

    domain = classifier.classify(question)
    retrieval_text = question
    if domain is None and history:  # FR-10: follow-up inherits the previous domain
        prev = [m["domain"] for m in history if m["role"] == "assistant" and m["domain"]]
        if prev:
            domain = prev[-1]
            prev_q = [m["content"] for m in history if m["role"] == "user"]
            retrieval_text = f"{question} {prev_q[-1] if prev_q else ''}"

    if conv is None:
        conv = Conversation(user_id=user.id, title=question[:60])
        db.add(conv)
        db.flush()

    db.add(Message(conversation_id=conv.id, role="user", content=question, domain=domain))

    steps: List[str] = []
    sources: List[str] = []
    if domain is None:
        in_scope, answer = False, config.OUT_OF_SCOPE_MESSAGE  # FR-04
    else:
        in_scope = True
        entries = retrieval.retrieve(db, retrieval_text, domain)  # FR-05
        if not entries:
            answer = ("I don't have a stored reference that covers this "
                      f"({classifier.DOMAIN_LABELS[domain]}). Please consult a qualified lawyer "
                      "or rephrase with more detail.")
        else:
            answer = llm_service.generate_answer(question, entries, history)  # FR-06
            sources = [f"{e.title}" + (f" - {e.citation}" if e.citation else "") for e in entries]
            for e in entries:  # FR-08: procedure guidance
                if e.entry_type == "procedure" and e.steps:
                    steps = [s.strip() for s in e.steps.split("\n") if s.strip()]
                    break

    reply = Message(conversation_id=conv.id, role="assistant", content=answer, domain=domain,
                    sources=json.dumps(sources))
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return schemas.AskOut(conversation_id=conv.id, message_id=reply.id, in_scope=in_scope,
                          domain=domain, answer=answer, steps=steps, sources=sources,
                          disclaimer=config.DISCLAIMER)  # FR-07


@router.get("/conversations")
def list_conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    convs = (db.query(Conversation).filter(Conversation.user_id == user.id)
             .order_by(Conversation.created_at.desc()).all())
    return [{"id": c.id, "title": c.title, "created_at": c.created_at.isoformat()} for c in convs]


@router.get("/conversations/{cid}")
def get_conversation(cid: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = _get_owned_conversation(db, user, cid)
    return {"id": conv.id, "title": conv.title, "messages": [
        {"id": m.id, "role": m.role, "content": m.content, "domain": m.domain,
         "sources": json.loads(m.sources or "[]"),
         "disclaimer": config.DISCLAIMER if m.role == "assistant" else None}
        for m in conv.messages]}


@router.delete("/conversations/{cid}", status_code=204)
def delete_conversation(cid: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(_get_owned_conversation(db, user, cid))
    db.commit()
