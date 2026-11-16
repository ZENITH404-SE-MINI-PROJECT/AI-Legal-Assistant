"""Ratings, comments and error reports tied to a response (FR-15)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import schemas
from .database import get_db
from .deps import get_current_user
from .models import Conversation, Feedback, Message, User

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", status_code=201)
def submit_feedback(body: schemas.FeedbackIn, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if body.rating is None and not body.comment.strip() and not body.is_error_report:
        raise HTTPException(422, "Provide a rating, a comment, or mark it as an error report")
    msg = db.get(Message, body.message_id)
    conv = db.get(Conversation, msg.conversation_id) if msg else None
    if msg is None or conv is None or conv.user_id != user.id or msg.role != "assistant":
        raise HTTPException(404, "Response not found")
    if db.query(Feedback).filter(Feedback.message_id == msg.id).first():
        raise HTTPException(409, "Feedback already submitted for this response")
    fb = Feedback(message_id=msg.id, user_id=user.id, rating=body.rating,
                  comment=body.comment.strip(), is_error_report=body.is_error_report)
    db.add(fb)
    db.commit()
    return {"id": fb.id, "status": "received"}
