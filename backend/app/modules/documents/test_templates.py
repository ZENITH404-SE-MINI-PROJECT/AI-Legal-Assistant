
from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

# Add the project root to Python's import path.
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from backend.app.modules.documents.templates import router

app = FastAPI()
app.include_router(router)

client = TestClient(app)


def test_list_templates():
    response = client.get("/api/templates/")

    assert response.status_code == 200
    assert "templates" in response.json()


def test_search_rental():
    response = client.get("/api/templates/?search=rental")

    assert response.status_code == 200
    templates = response.json()["templates"]
    assert all(
        "rental" in template.get("name", "").lower()
        or "rental" in template.get("description", "").lower()
        or any(
            "rental" in keyword.lower()
            for keyword in template.get("keywords", [])
        )
        for template in templates
    )


def test_missing_template():
    response = client.get("/api/templates/UNKNOWN-ID")

    assert response.status_code == 404
