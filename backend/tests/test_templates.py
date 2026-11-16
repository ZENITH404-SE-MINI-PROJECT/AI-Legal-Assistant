"""UT-07: template module (FR-11, FR-12)."""
import io

from docx import Document

from app.template_api import fill_template, placeholders

RTI_VALUES = {k: "x" for k in ["public_authority", "authority_address", "date", "period",
                                "information_sought", "fee", "fee_mode", "applicant_name", "applicant_address"]}


def _rti_id(client, h):
    return next(t["id"] for t in client.get("/api/templates", headers=h).json() if "RTI" in t["title"])


def test_placeholders_extracted_in_order_without_duplicates():
    assert placeholders("Hi {{a}} and {{ b }} and {{a}}") == ["a", "b"]


def test_fill_template_substitutes():
    assert fill_template("Dear {{name}}", {"name": " Ravi "}) == "Dear Ravi"


def test_fill_template_missing_value_raises():
    try:
        fill_template("Dear {{name}} {{city}}", {"name": "Ravi"})
        assert False
    except ValueError as exc:
        assert "city" in str(exc)


def test_list_and_search(client, user_h):
    assert len(client.get("/api/templates", headers=user_h).json()) >= 5
    res = client.get("/api/templates", params={"q": "salary"}, headers=user_h).json()
    assert len(res) == 1


def test_filter_by_category(client, user_h):
    res = client.get("/api/templates", params={"category": "rti"}, headers=user_h).json()
    assert res and all(t["category"] == "rti" for t in res)


def test_get_template_lists_placeholders(client, user_h):
    tid = _rti_id(client, user_h)
    assert "applicant_name" in client.get(f"/api/templates/{tid}", headers=user_h).json()["placeholders"]


def test_fill_and_download_txt(client, user_h):
    tid = _rti_id(client, user_h)
    r = client.post(f"/api/templates/{tid}/fill", json={"values": RTI_VALUES}, headers=user_h)
    assert r.status_code == 200 and "attachment" in r.headers["content-disposition"]
    assert "{{" not in r.text


def test_fill_and_download_docx(client, user_h):
    tid = _rti_id(client, user_h)
    r = client.post(f"/api/templates/{tid}/fill", params={"fmt": "docx"}, json={"values": RTI_VALUES}, headers=user_h)
    assert r.status_code == 200
    assert Document(io.BytesIO(r.content)).paragraphs


def test_fill_missing_field_422(client, user_h):
    tid = _rti_id(client, user_h)
    assert client.post(f"/api/templates/{tid}/fill", json={"values": {"date": "1"}}, headers=user_h).status_code == 422


def test_unknown_template_404(client, user_h):
    assert client.get("/api/templates/9999", headers=user_h).status_code == 404


def test_bad_format_rejected(client, user_h):
    tid = _rti_id(client, user_h)
    assert client.post(f"/api/templates/{tid}/fill", params={"fmt": "exe"}, json={"values": RTI_VALUES},
                       headers=user_h).status_code == 422
