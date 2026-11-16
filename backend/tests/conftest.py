import os
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp()
os.environ["BCRYPT_ROUNDS"] = "4"
os.environ["LLM_API_KEY"] = ""  # tests never hit the network
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "AdminPass1"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import security  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed(db)
    security.reset_throttle()
    yield


@pytest.fixture()
def client():
    return TestClient(app)


def _register(client, username, password="Passw0rd1"):
    r = client.post("/api/auth/register", json={"username": username, "password": password})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def user_h(client):
    return _register(client, "alice")


@pytest.fixture()
def user2_h(client):
    return _register(client, "bob")


@pytest.fixture()
def admin_h(client):
    r = client.post("/api/auth/login", json={"username": "admin", "password": "AdminPass1"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def db():
    with SessionLocal() as session:
        yield session
