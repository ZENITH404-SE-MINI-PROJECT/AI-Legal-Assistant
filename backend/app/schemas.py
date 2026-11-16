"""Pydantic request/response models."""
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class RegisterIn(BaseModel):
    username: str
    password: str


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class AskIn(BaseModel):
    question: str
    conversation_id: Optional[str] = None


class AskOut(BaseModel):
    conversation_id: str
    message_id: int
    in_scope: bool
    domain: Optional[str]
    answer: str
    steps: List[str] = []
    sources: List[str] = []
    disclaimer: str


class FeedbackIn(BaseModel):
    message_id: int
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: str = Field(default="", max_length=2000)
    is_error_report: bool = False


class FillIn(BaseModel):
    values: Dict[str, str]


class ReferenceIn(BaseModel):
    entry_type: str = "case"
    title: str = Field(min_length=3, max_length=200)
    citation: str = ""
    jurisdiction: str = "India"
    domain: str
    keywords: str = ""
    summary: str = Field(min_length=10)
    steps: str = ""


class TemplateIn(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    category: str
    description: str = ""
    body: str = Field(min_length=10)


class FeedbackResolveIn(BaseModel):
    resolved: bool = True
    admin_note: str = ""


class RoleIn(BaseModel):
    role: str
