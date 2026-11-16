"""UT-08: upload and analysis (FR-13, FR-14)."""
import io

from docx import Document
from reportlab.pdfgen import canvas

from app import config, doc_analysis, llm_service

CONTRACT = ("This agreement is made between the parties. The tenant shall pay rent of Rs 10000 monthly. "
            "Either party may terminate this agreement with 30 days notice. The deposit is refundable.")


def up(client, h, name, data, ctype="application/octet-stream"):
    return client.post("/api/documents", files={"file": (name, data, ctype)}, headers=h)


def make_pdf(text):
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 750, text[:90])
    c.save()
    return buf.getvalue()


def make_docx(text):
    buf = io.BytesIO()
    d = Document()
    d.add_paragraph(text)
    d.save(buf)
    return buf.getvalue()


def test_upload_txt_returns_summary_and_clauses(client, user_h):
    r = up(client, user_h, "a.txt", CONTRACT.encode())
    assert r.status_code == 201
    d = r.json()
    assert d["file_type"] == "TXT" and d["summary"] and d["key_clauses"] and d["disclaimer"]


def test_upload_pdf(client, user_h):
    r = up(client, user_h, "a.pdf", make_pdf("The tenant shall pay rent monthly to the landlord."))
    assert r.status_code == 201 and r.json()["file_type"] == "PDF"


def test_upload_docx(client, user_h):
    r = up(client, user_h, "a.docx", make_docx(CONTRACT))
    assert r.status_code == 201 and r.json()["file_type"] == "DOCX"


def test_rejects_unsupported_extension(client, user_h):
    assert up(client, user_h, "evil.exe", b"MZ....").status_code == 422


def test_rejects_empty_file(client, user_h):
    assert up(client, user_h, "a.txt", b"").status_code == 422


def test_rejects_oversize(client, user_h, monkeypatch):
    monkeypatch.setattr(config, "MAX_UPLOAD_BYTES", 100)
    assert up(client, user_h, "a.txt", b"x" * 500).status_code == 422


def test_rejects_extension_content_mismatch(client, user_h):
    assert up(client, user_h, "fake.pdf", b"this is not a pdf").status_code == 422


def test_corrupt_pdf_handled(client, user_h):
    assert up(client, user_h, "bad.pdf", b"%PDF-1.4 garbage").status_code == 422


def test_path_traversal_filename_is_harmless(client, user_h):
    r = up(client, user_h, "../../etc/passwd.txt", CONTRACT.encode())
    assert r.status_code == 201 and "/" not in r.json()["name"]


def test_documents_are_private_to_owner(client, user_h, user2_h):
    did = up(client, user_h, "a.txt", CONTRACT.encode()).json()["id"]
    assert client.get(f"/api/documents/{did}", headers=user2_h).status_code == 404
    assert client.delete(f"/api/documents/{did}", headers=user2_h).status_code == 404
    assert client.get("/api/documents", headers=user2_h).json() == []


def test_list_and_delete_document(client, user_h):
    did = up(client, user_h, "a.txt", CONTRACT.encode()).json()["id"]
    assert len(client.get("/api/documents", headers=user_h).json()) == 1
    assert client.delete(f"/api/documents/{did}", headers=user_h).status_code == 204
    assert client.get("/api/documents", headers=user_h).json() == []


def test_heuristic_summary_empty_text():
    assert llm_service.analyze_document("   ")[1] == []


def test_validate_upload_function():
    assert doc_analysis.validate_upload("x.TXT", b"abc") == "txt"
