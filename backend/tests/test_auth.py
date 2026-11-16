"""Authentication, RBAC and security requirements (SRS 6.3)."""
import time

import jwt

from app import config, security
from app.models import User


def test_register_and_login(client):
    r = client.post("/api/auth/register", json={"username": "carol", "password": "Passw0rd1"})
    assert r.status_code == 201 and r.json()["role"] == "user"
    r = client.post("/api/auth/login", json={"username": "carol", "password": "Passw0rd1"})
    assert r.status_code == 200 and r.json()["access_token"]


def test_password_is_hashed_not_plaintext(client, db):
    client.post("/api/auth/register", json={"username": "dave", "password": "Passw0rd1"})
    u = db.query(User).filter_by(username="dave").one()
    assert u.password_hash != "Passw0rd1" and u.password_hash.startswith("$2")


def test_weak_password_rejected(client):
    for pw in ["short1", "allletters", "12345678"]:
        r = client.post("/api/auth/register", json={"username": "erin", "password": pw})
        assert r.status_code == 422


def test_bad_username_rejected(client):
    r = client.post("/api/auth/register", json={"username": "a b", "password": "Passw0rd1"})
    assert r.status_code == 422


def test_duplicate_username_rejected(client, user_h):
    r = client.post("/api/auth/register", json={"username": "alice", "password": "Passw0rd1"})
    assert r.status_code == 409


def test_wrong_password_unauthorized(client, user_h):
    r = client.post("/api/auth/login", json={"username": "alice", "password": "Wrong123x"})
    assert r.status_code == 401


def test_lockout_after_repeated_failures(client, user_h):
    for _ in range(security.MAX_FAILURES):
        client.post("/api/auth/login", json={"username": "alice", "password": "Wrong123x"})
    r = client.post("/api/auth/login", json={"username": "alice", "password": "Passw0rd1"})
    assert r.status_code == 429


def test_protected_route_requires_token(client):
    assert client.get("/api/chat/conversations").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer junk"}).status_code == 401


def test_expired_token_rejected(client, db):
    u = db.query(User).filter_by(username="admin").one()
    expired = jwt.encode({"sub": u.id, "role": "admin", "exp": int(time.time()) - 10},
                         config.SECRET_KEY, algorithm=config.ALGORITHM)
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401


def test_standard_user_cannot_use_admin_api(client, user_h):
    assert client.get("/api/admin/users", headers=user_h).status_code == 403


def test_delete_my_data(client, user_h):
    client.post("/api/chat/ask", json={"question": "How do I file an FIR at the police station?"}, headers=user_h)
    assert client.delete("/api/auth/me/data", headers=user_h).status_code == 204
    assert client.get("/api/chat/conversations", headers=user_h).json() == []


def test_security_headers_present(client):
    r = client.get("/api/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
