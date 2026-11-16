"""UT-01/UT-04/UT-05: chat module end to end (FR-01..FR-10)."""
from app import config, llm_service


def ask(client, headers, q, cid=None):
    body = {"question": q}
    if cid:
        body["conversation_id"] = cid
    return client.post("/api/chat/ask", json=body, headers=headers)


def test_requires_authentication(client):
    assert client.post("/api/chat/ask", json={"question": "How to file an FIR?"}).status_code == 401


def test_in_scope_answer_has_source_and_disclaimer(client, user_h):
    r = ask(client, user_h, "My landlord will not return my security deposit, what can I do?")
    assert r.status_code == 200
    d = r.json()
    assert d["in_scope"] and d["domain"] == "tenancy"
    assert d["sources"] and d["disclaimer"] == config.DISCLAIMER


def test_out_of_scope_message(client, user_h):
    d = ask(client, user_h, "What is the best recipe for chocolate cake?").json()
    assert d["in_scope"] is False and d["answer"] == config.OUT_OF_SCOPE_MESSAGE
    assert d["sources"] == [] and d["disclaimer"]


def test_too_short_query_rejected(client, user_h):
    assert ask(client, user_h, "hi").status_code == 422


def test_too_long_query_rejected(client, user_h):
    assert ask(client, user_h, "fir " * 400).status_code == 422


def test_symbol_only_query_rejected(client, user_h):
    assert ask(client, user_h, "?????!!!!!").status_code == 422


def test_procedure_guidance_returns_steps(client, user_h):
    d = ask(client, user_h, "How do I file an FIR at a police station?").json()
    assert len(d["steps"]) >= 3


def test_follow_up_inherits_domain(client, user_h):
    first = ask(client, user_h, "My landlord wants to evict me, what notice is required?").json()
    second = ask(client, user_h, "How many days do I get?", first["conversation_id"]).json()
    assert second["conversation_id"] == first["conversation_id"]
    assert second["domain"] == first["domain"] == "tenancy"


def test_domain_without_matching_entry_does_not_fabricate(client, user_h):
    d = ask(client, user_h, "Can I get a will notarised for my wife and adoption inheritance?").json()
    if not d["sources"]:
        assert "don't have a stored reference" in d["answer"]


def test_conversation_history_listed_and_loaded(client, user_h):
    cid = ask(client, user_h, "How can I claim a refund for a defective product?").json()["conversation_id"]
    assert len(client.get("/api/chat/conversations", headers=user_h).json()) == 1
    msgs = client.get(f"/api/chat/conversations/{cid}", headers=user_h).json()["messages"]
    assert [m["role"] for m in msgs] == ["user", "assistant"]


def test_cannot_read_other_users_conversation(client, user_h, user2_h):
    cid = ask(client, user_h, "How can I claim a refund for a defective product?").json()["conversation_id"]
    assert client.get(f"/api/chat/conversations/{cid}", headers=user2_h).status_code == 404
    assert ask(client, user2_h, "Follow up refund question?", cid).status_code == 404


def test_delete_conversation(client, user_h):
    cid = ask(client, user_h, "How can I claim a refund for a defective product?").json()["conversation_id"]
    assert client.delete(f"/api/chat/conversations/{cid}", headers=user_h).status_code == 204
    assert client.get(f"/api/chat/conversations/{cid}", headers=user_h).status_code == 404


# ---- llm_service (UT-04) ----
def test_safety_filter_removes_guarantees():
    out = llm_service.enforce_safety("You will definitely win. I guarantee it, as your lawyer.")
    assert "guarantee" not in out.lower() and "as your lawyer" not in out.lower()
    assert "you will definitely win" not in out.lower()


def test_fallback_uses_only_retrieved_entries(db):
    from app.models import CaseReference
    e = db.query(CaseReference).first()
    assert e.title in llm_service.fallback_answer([e])


def test_llm_failure_falls_back(monkeypatch, db):
    from app.models import CaseReference
    monkeypatch.setattr(config, "LLM_API_KEY", "fake")
    monkeypatch.setattr(llm_service, "_call_llm", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down")))
    e = db.query(CaseReference).first()
    assert e.title in llm_service.generate_answer("q", [e], [])


def test_llm_answer_is_sanitised(monkeypatch, db):
    from app.models import CaseReference
    monkeypatch.setattr(config, "LLM_API_KEY", "fake")
    monkeypatch.setattr(llm_service, "_call_llm", lambda *a, **k: "I guarantee you will win")
    e = db.query(CaseReference).first()
    assert "guarantee" not in llm_service.generate_answer("q", [e], []).lower()


def test_build_prompt_contains_material_and_question(db):
    from app.models import CaseReference
    e = db.query(CaseReference).first()
    prompt = llm_service.build_prompt("my question?", [e], [{"role": "user", "content": "earlier"}])
    assert e.title in prompt and "my question?" in prompt and "earlier" in prompt


def test_clean_text_unchanged_by_safety_filter():
    text = "You may approach the Consumer Commission."
    assert llm_service.enforce_safety(text) == text


def test_llm_success_is_used(monkeypatch, db):
    from app.models import CaseReference
    monkeypatch.setattr(config, "LLM_API_KEY", "fake")
    monkeypatch.setattr(llm_service, "_call_llm", lambda *a, **k: "Plain language answer [1].")
    e = db.query(CaseReference).first()
    assert llm_service.generate_answer("q", [e], []) == "Plain language answer [1]."


def test_call_llm_parses_provider_response(monkeypatch):
    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"content": [{"type": "text", "text": "hello "}, {"type": "text", "text": "world"}]}

    monkeypatch.setattr(config, "LLM_API_KEY", "fake")
    monkeypatch.setattr(llm_service.httpx, "post", lambda *a, **k: Resp())
    assert llm_service._call_llm("sys", "user") == "hello world"


def test_heuristic_summary_extracts_clauses():
    summary, clauses = llm_service.heuristic_summary(
        "This is a rental agreement between two parties. The tenant shall pay rent monthly. "
        "Either party may terminate with notice.")
    assert summary and any("shall pay rent" in c for c in clauses)


def test_document_analysis_uses_llm_json(monkeypatch):
    monkeypatch.setattr(config, "LLM_API_KEY", "fake")
    monkeypatch.setattr(llm_service, "_call_llm",
                        lambda *a, **k: '{"summary": "Short.", "key_clauses": ["Clause A"]}')
    assert llm_service.analyze_document("some text") == ("Short.", ["Clause A"])


def test_document_analysis_bad_llm_json_falls_back(monkeypatch):
    monkeypatch.setattr(config, "LLM_API_KEY", "fake")
    monkeypatch.setattr(llm_service, "_call_llm", lambda *a, **k: "not json")
    summary, _ = llm_service.analyze_document("The tenant shall pay the monthly rent on time always.")
    assert summary
