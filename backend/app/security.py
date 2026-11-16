"""Password hashing, JWT handling and login throttling (SRS 6.3)."""
import re
import time
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from . import config

_PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,128}$")
_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,50}$")

# --- login throttling: 5 failures => 5 minute lock (in-memory, per username) ---
MAX_FAILURES = 5
LOCK_SECONDS = 300
_failures: dict = {}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=config.BCRYPT_ROUNDS)).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def valid_password(password: str) -> bool:
    return bool(_PASSWORD_RE.match(password or ""))


def valid_username(username: str) -> bool:
    return bool(_USERNAME_RE.match(username or ""))


def create_token(user_id: str, role: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_MINUTES)
    payload = {"sub": user_id, "role": role, "exp": exp}
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)


def decode_token(token: str) -> dict:
    """Raises jwt.PyJWTError on invalid/expired tokens."""
    return jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])


def is_locked(username: str) -> bool:
    count, since = _failures.get(username, (0, 0.0))
    if count >= MAX_FAILURES:
        if time.time() - since < LOCK_SECONDS:
            return True
        _failures.pop(username, None)
    return False


def record_failure(username: str) -> None:
    count, _ = _failures.get(username, (0, 0.0))
    _failures[username] = (count + 1, time.time())


def clear_failures(username: str) -> None:
    _failures.pop(username, None)


def reset_throttle() -> None:  # used by tests
    _failures.clear()
