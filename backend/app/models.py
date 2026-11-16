"""ORM models - mirror the ER diagram in SRS Figure 3."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String,
                        Text)
from sqlalchemy.orm import relationship

from .database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(10), nullable=False, default="user")  # user | admin
    created_at = Column(DateTime, default=_now, nullable=False)
    conversations = relationship("Conversation", cascade="all, delete-orphan")
    documents = relationship("LegalDocument", cascade="all, delete-orphan")


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(120), default="New conversation")
    created_at = Column(DateTime, default=_now)
    messages = relationship("Message", cascade="all, delete-orphan",
                            order_by="Message.id")


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(10), nullable=False)  # user | assistant
    content = Column(Text, nullable=False)
    domain = Column(String(40))
    sources = Column(Text, default="")  # JSON list of cited entry titles
    created_at = Column(DateTime, default=_now)
    feedback = relationship("Feedback", uselist=False, cascade="all, delete-orphan")


class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, unique=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    rating = Column(Integer)  # 1..5
    comment = Column(Text, default="")
    is_error_report = Column(Boolean, default=False)
    resolved = Column(Boolean, default=False)
    admin_note = Column(Text, default="")
    created_at = Column(DateTime, default=_now)


class LegalDocument(Base):
    __tablename__ = "legal_documents"
    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    file_path = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)
    summary = Column(Text, default="")
    key_clauses = Column(Text, default="")  # JSON list
    uploaded_at = Column(DateTime, default=_now)


class Template(Base):
    __tablename__ = "templates"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(120), nullable=False)
    category = Column(String(40), nullable=False)
    description = Column(String(255), default="")
    body = Column(Text, nullable=False)  # uses {{placeholder}} syntax
    created_by = Column(String(36), ForeignKey("users.id"))


class CaseReference(Base):
    """Case law entries (type='case') and procedure/knowledge entries (type='procedure')."""
    __tablename__ = "case_references"
    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_type = Column(String(12), nullable=False, default="case")
    title = Column(String(200), nullable=False)
    citation = Column(String(120), default="")
    jurisdiction = Column(String(60), default="India")
    domain = Column(String(40), nullable=False, index=True)
    keywords = Column(Text, default="")  # comma separated
    summary = Column(Text, nullable=False)
    steps = Column(Text, default="")  # newline separated, for procedures
