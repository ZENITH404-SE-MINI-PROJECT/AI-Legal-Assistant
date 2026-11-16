"""Keyword retrieval from the knowledge base (stage 2, FR-05)."""
import re
from typing import List

from sqlalchemy.orm import Session

from .models import CaseReference

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is", "are", "was", "be", "i",
    "my", "me", "we", "you", "your", "can", "do", "does", "how", "what", "when", "where", "which",
    "who", "if", "it", "this", "that", "with", "as", "at", "by", "from", "about", "should", "will",
    "would", "could", "have", "has", "had", "not", "am", "they", "them", "their", "get", "want",
}


def tokenize(text: str) -> List[str]:
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 1]


def score_entry(entry: CaseReference, tokens: List[str]) -> int:
    kw = {k.strip().lower() for k in (entry.keywords or "").split(",") if k.strip()}
    kw_tokens = set(tokenize(" ".join(kw)))
    title_tokens = set(tokenize(entry.title))
    body_tokens = set(tokenize(entry.summary))
    score = 0
    for t in set(tokens):
        if t in kw_tokens:
            score += 3
        if t in title_tokens:
            score += 2
        if t in body_tokens:
            score += 1
    return score


def retrieve(db: Session, query: str, domain: str, limit: int = 3, min_score: int = 3) -> List[CaseReference]:
    tokens = tokenize(query)
    if not tokens:
        return []
    entries = db.query(CaseReference).filter(CaseReference.domain == domain).all()
    scored = [(score_entry(e, tokens), e) for e in entries]
    scored = [(s, e) for s, e in scored if s >= min_score]
    scored.sort(key=lambda pair: (-pair[0], pair[1].id))
    return [e for _, e in scored[:limit]]
