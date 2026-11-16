"""UT-06: case law search (FR-09)."""


def test_search_by_keyword(client, user_h):
    r = client.get("/api/case-law", params={"q": "privacy"}, headers=user_h)
    assert r.status_code == 200 and any("Puttaswamy" in c["title"] for c in r.json())


def test_search_by_citation(client, user_h):
    r = client.get("/api/case-law", params={"citation": "(2015) 5 SCC 1"}, headers=user_h)
    assert [c["title"] for c in r.json()] == ["Shreya Singhal v. Union of India"]


def test_search_by_jurisdiction(client, user_h):
    assert len(client.get("/api/case-law", params={"jurisdiction": "india"}, headers=user_h).json()) > 5


def test_unknown_jurisdiction_empty(client, user_h):
    assert client.get("/api/case-law", params={"jurisdiction": "Atlantis"}, headers=user_h).json() == []


def test_only_cases_not_procedures(client, user_h):
    assert all(c["citation"] for c in client.get("/api/case-law", headers=user_h).json())


def test_wildcard_characters_are_escaped(client, user_h):
    assert client.get("/api/case-law", params={"q": "%"}, headers=user_h).json() == []


def test_requires_auth(client):
    assert client.get("/api/case-law").status_code == 401


def test_limit_validation(client, user_h):
    assert client.get("/api/case-law", params={"limit": 0}, headers=user_h).status_code == 422
