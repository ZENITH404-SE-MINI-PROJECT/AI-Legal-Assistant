"""UT-10: admin module (FR-16..FR-19)."""

REF = {"entry_type": "case", "title": "Test v. Case", "citation": "(2024) 1 SCC 1", "domain": "consumer",
       "keywords": "test,widget", "summary": "A summary long enough to pass validation."}
TPL = {"title": "Test Template", "category": "consumer", "description": "d", "body": "Hello {{name}} welcome"}


def test_reference_crud(client, admin_h, user_h):
    rid = client.post("/api/admin/references", json=REF, headers=admin_h).json()["id"]
    assert any(x["id"] == rid for x in client.get("/api/admin/references", headers=admin_h).json())
    upd = dict(REF, title="Renamed v. Case")
    assert client.put(f"/api/admin/references/{rid}", json=upd, headers=admin_h).status_code == 200
    assert client.get("/api/case-law", params={"q": "Renamed"}, headers=user_h).json()
    assert client.delete(f"/api/admin/references/{rid}", headers=admin_h).status_code == 204
    assert client.delete(f"/api/admin/references/{rid}", headers=admin_h).status_code == 404


def test_new_reference_is_used_by_chat(client, admin_h, user_h):
    client.post("/api/admin/references", json=dict(REF, entry_type="procedure", keywords="widget,gadget,refund",
                                                    title="Widget refund procedure",
                                                    summary="Return the widget to the seller within seven days for refund."),
                headers=admin_h)
    d = client.post("/api/chat/ask", json={"question": "I want a refund for my defective widget gadget"},
                    headers=user_h).json()
    assert any("Widget" in s for s in d["sources"])


def test_invalid_domain_and_type_rejected(client, admin_h):
    assert client.post("/api/admin/references", json=dict(REF, domain="astrology"), headers=admin_h).status_code == 422
    assert client.post("/api/admin/references", json=dict(REF, entry_type="x"), headers=admin_h).status_code == 422


def test_user_cannot_modify_knowledge_base(client, user_h):
    assert client.post("/api/admin/references", json=REF, headers=user_h).status_code == 403
    assert client.post("/api/admin/templates", json=TPL, headers=user_h).status_code == 403


def test_template_crud(client, admin_h, user_h):
    tid = client.post("/api/admin/templates", json=TPL, headers=admin_h).json()["id"]
    assert client.get(f"/api/templates/{tid}", headers=user_h).json()["placeholders"] == ["name"]
    assert client.put(f"/api/admin/templates/{tid}", json=dict(TPL, title="Edited T"), headers=admin_h).status_code == 200
    assert client.delete(f"/api/admin/templates/{tid}", headers=admin_h).status_code == 204
    assert client.get(f"/api/templates/{tid}", headers=user_h).status_code == 404


def test_feedback_review_and_resolve(client, admin_h, user_h):
    mid = client.post("/api/chat/ask", json={"question": "How do I file an FIR at the police station?"},
                      headers=user_h).json()["message_id"]
    client.post("/api/feedback", json={"message_id": mid, "is_error_report": True, "comment": "wrong"}, headers=user_h)
    items = client.get("/api/admin/feedback", params={"unresolved_only": True}, headers=admin_h).json()
    assert len(items) == 1 and items[0]["response_text"]
    fid = items[0]["id"]
    assert client.put(f"/api/admin/feedback/{fid}", json={"resolved": True, "admin_note": "fixed"},
                      headers=admin_h).status_code == 200
    assert client.get("/api/admin/feedback", params={"unresolved_only": True}, headers=admin_h).json() == []


def test_user_management(client, admin_h, user_h):
    users = client.get("/api/admin/users", headers=admin_h).json()
    alice = next(u for u in users if u["username"] == "alice")
    assert client.put(f"/api/admin/users/{alice['id']}/role", json={"role": "admin"}, headers=admin_h).status_code == 200
    assert client.put(f"/api/admin/users/{alice['id']}/role", json={"role": "wizard"}, headers=admin_h).status_code == 422
    assert client.delete(f"/api/admin/users/{alice['id']}", headers=admin_h).status_code == 204


def test_admin_cannot_demote_or_delete_self(client, admin_h):
    me = client.get("/api/auth/me", headers=admin_h).json()
    assert client.put(f"/api/admin/users/{me['id']}/role", json={"role": "user"}, headers=admin_h).status_code == 400
    assert client.delete(f"/api/admin/users/{me['id']}", headers=admin_h).status_code == 400
