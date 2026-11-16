"""UT-09: feedback module (FR-15)."""


def reply_id(client, h):
    return client.post("/api/chat/ask", json={"question": "How do I file an FIR at the police station?"},
                       headers=h).json()["message_id"]


def test_submit_rating_and_comment(client, user_h):
    mid = reply_id(client, user_h)
    r = client.post("/api/feedback", json={"message_id": mid, "rating": 4, "comment": "helpful"}, headers=user_h)
    assert r.status_code == 201


def test_error_report_only(client, user_h):
    mid = reply_id(client, user_h)
    assert client.post("/api/feedback", json={"message_id": mid, "is_error_report": True}, headers=user_h).status_code == 201


def test_empty_feedback_rejected(client, user_h):
    mid = reply_id(client, user_h)
    assert client.post("/api/feedback", json={"message_id": mid}, headers=user_h).status_code == 422


def test_rating_out_of_range_rejected(client, user_h):
    mid = reply_id(client, user_h)
    assert client.post("/api/feedback", json={"message_id": mid, "rating": 9}, headers=user_h).status_code == 422


def test_duplicate_feedback_conflict(client, user_h):
    mid = reply_id(client, user_h)
    client.post("/api/feedback", json={"message_id": mid, "rating": 5}, headers=user_h)
    assert client.post("/api/feedback", json={"message_id": mid, "rating": 1}, headers=user_h).status_code == 409


def test_cannot_rate_other_users_response(client, user_h, user2_h):
    mid = reply_id(client, user_h)
    assert client.post("/api/feedback", json={"message_id": mid, "rating": 5}, headers=user2_h).status_code == 404


def test_unknown_message_404(client, user_h):
    assert client.post("/api/feedback", json={"message_id": 99999, "rating": 5}, headers=user_h).status_code == 404


def test_requires_auth(client):
    assert client.post("/api/feedback", json={"message_id": 1, "rating": 5}).status_code == 401
