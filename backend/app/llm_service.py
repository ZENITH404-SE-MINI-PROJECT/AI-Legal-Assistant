"""Generation stage (stage 3, FR-06/FR-14).

Calls an external LLM when LLM_API_KEY is set; otherwise (or on any failure)
falls back to a deterministic generator built only from the retrieved entries,
so the app stays usable and testable offline.
"""
import json
import logging
import re
from typing import List, Tuple

import httpx

from . import config

log = logging.getLogger("llm_service")

SYSTEM_PROMPT = (
    "You are an informational legal assistant for Indian law. Answer ONLY from the "
    "REFERENCE MATERIAL provided. If the material does not cover the question, say so. "
    "Use plain language. Never claim to be a lawyer, never guarantee an outcome, and "
    "never give definitive legal advice."
)

_UNSAFE = [
    (re.compile(r"\b(you|you'll|you will)\s+(definitely|certainly|surely)?\s*win\b", re.I),
     "you may have a strong position"),
    (re.compile(r"\bguarantee[sd]?\b", re.I), "cannot be assured"),
    (re.compile(r"\b100\s*%\s*(sure|certain|safe)\b", re.I), "likely"),
    (re.compile(r"\bas your (lawyer|advocate|attorney)\b", re.I), "as an informational assistant"),
]


def enforce_safety(text: str) -> str:
    """Remove phrasing that implies guaranteed outcomes or lawyer status (SRS 6.2/6.5)."""
    for pattern, repl in _UNSAFE:
        text = pattern.sub(repl, text)
    return text


def _call_llm(system: str, user: str, max_tokens: int = 700) -> str:
    headers = {"x-api-key": config.LLM_API_KEY, "anthropic-version": "2023-06-01",
               "content-type": "application/json"}
    payload = {"model": config.LLM_MODEL, "max_tokens": max_tokens, "system": system,
               "messages": [{"role": "user", "content": user}]}
    resp = httpx.post(config.LLM_API_URL, headers=headers, json=payload,
                      timeout=config.LLM_TIMEOUT_SECONDS)
    resp.raise_for_status()
    data = resp.json()
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text").strip()


def build_prompt(question: str, entries, history: List[dict]) -> str:
    material = "\n\n".join(
        f"[{i + 1}] {e.title} ({e.citation or e.entry_type})\n{e.summary}"
        + (f"\nSteps:\n{e.steps}" if e.steps else "")
        for i, e in enumerate(entries)
    )
    convo = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in history[-config.HISTORY_WINDOW:])
    return (f"REFERENCE MATERIAL:\n{material}\n\nRECENT CONVERSATION:\n{convo or '(none)'}\n\n"
            f"QUESTION: {question}\n\nAnswer in plain language in under 200 words, "
            f"citing sources as [1], [2].")


def fallback_answer(entries) -> str:
    """Deterministic answer assembled strictly from retrieved material."""
    parts = []
    for i, e in enumerate(entries, 1):
        label = f"{e.title} ({e.citation})" if e.citation else e.title
        parts.append(f"[{i}] {label}: {e.summary}")
    return "Based on the legal references in our knowledge base:\n" + "\n".join(parts)


def generate_answer(question: str, entries, history: List[dict]) -> str:
    if config.LLM_API_KEY:
        try:
            text = _call_llm(SYSTEM_PROMPT, build_prompt(question, entries, history))
            if text:
                return enforce_safety(text)
        except Exception as exc:  # network/provider failure -> graceful degradation
            log.warning("LLM call failed, using fallback: %s", exc)
    return enforce_safety(fallback_answer(entries))


# ---------------- document analysis (FR-14) ----------------
_CLAUSE_HINTS = re.compile(
    r"\b(shall|must|terminat\w*|payment|pay|liabilit\w*|indemn\w*|confidential\w*|"
    r"governing law|jurisdiction|arbitration|notice|penalt\w*|deposit|rent|term of)\b", re.I)


def heuristic_summary(text: str) -> Tuple[str, List[str]]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if len(s.strip()) > 20]
    summary = " ".join(sentences[:3]) if sentences else "No readable text found in the document."
    clauses = [s for s in sentences if _CLAUSE_HINTS.search(s)][:8]
    return summary[:1200], [c[:300] for c in clauses]


def analyze_document(text: str) -> Tuple[str, List[str]]:
    text = (text or "").strip()
    if not text:
        return "No readable text found in the document.", []
    if config.LLM_API_KEY:
        try:
            prompt = ("Summarise this legal document in under 120 words and list up to 8 key clauses. "
                      "Respond ONLY as JSON: {\"summary\": str, \"key_clauses\": [str]}.\n\n" + text[:12000])
            raw = _call_llm(SYSTEM_PROMPT, prompt, max_tokens=900)
            raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
            data = json.loads(raw)
            return enforce_safety(str(data["summary"])), [enforce_safety(str(c)) for c in data["key_clauses"]][:8]
        except Exception as exc:
            log.warning("LLM analysis failed, using heuristic: %s", exc)
    return heuristic_summary(text)
