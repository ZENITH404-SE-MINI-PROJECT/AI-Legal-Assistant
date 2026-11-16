"""Central configuration, read from environment variables."""
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./legal_assistant.db")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me-in-production-0123456789")
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "30"))  # auto timeout (SRS 6.3)
ALGORITHM = "HS256"
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_API_URL = os.getenv("LLM_API_URL", "https://api.anthropic.com/v1/messages")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
ALLOWED_UPLOAD_TYPES = {"pdf": "PDF", "txt": "TXT", "docx": "DOCX"}

MAX_QUERY_CHARS = 1000
MIN_QUERY_CHARS = 5
HISTORY_WINDOW = 6  # messages reused for follow-ups (FR-10)

DISCLAIMER = (
    "Disclaimer: This is general legal information, not legal advice. "
    "I am an AI assistant, not a lawyer, and no outcome is guaranteed. "
    "For your specific situation please consult a qualified advocate."
)
OUT_OF_SCOPE_MESSAGE = (
    "I couldn't match your question to a legal area I support "
    "(consumer, tenancy, family, employment, cyber/IT, criminal procedure). "
    "Please rephrase, or consult a qualified lawyer for this matter."
)
