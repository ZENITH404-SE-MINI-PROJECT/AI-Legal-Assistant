"""Document upload and analysis (FR-13, FR-14). Files are private to their owner."""
import io
import json
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from . import config, llm_service
from .database import get_db
from .deps import get_current_user
from .models import LegalDocument, User

router = APIRouter(prefix="/documents", tags=["documents"])

_MAGIC = {"pdf": b"%PDF", "docx": b"PK\x03\x04"}


def extract_text(file_type: str, data: bytes) -> str:
    if file_type == "txt":
        return data.decode("utf-8", errors="ignore")
    if file_type == "pdf":
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    if file_type == "docx":
        from docx import Document
        return "\n".join(p.text for p in Document(io.BytesIO(data)).paragraphs)
    raise ValueError("unsupported type")


def validate_upload(filename: str, data: bytes) -> str:
    """Returns normalised file type or raises ValueError (size/format checks)."""
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()
    if ext not in config.ALLOWED_UPLOAD_TYPES:
        raise ValueError("Only PDF, TXT or DOCX files are accepted.")
    if len(data) == 0:
        raise ValueError("The file is empty.")
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise ValueError(f"File exceeds the {config.MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.")
    magic = _MAGIC.get(ext)
    if magic and not data.startswith(magic):
        raise ValueError("File content does not match its extension.")
    return ext


def _owned(db: Session, user: User, did: str) -> LegalDocument:
    doc = db.get(LegalDocument, did)
    if doc is None or doc.user_id != user.id:  # never reveal other users' documents
        raise HTTPException(404, "Document not found")
    return doc


def _out(d: LegalDocument) -> dict:
    return {"id": d.id, "name": d.original_name, "file_type": d.file_type,
            "uploaded_at": d.uploaded_at.isoformat(), "summary": d.summary,
            "key_clauses": json.loads(d.key_clauses or "[]"), "disclaimer": config.DISCLAIMER}


@router.post("", status_code=201)
async def upload(file: UploadFile = File(...), user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    data = await file.read(config.MAX_UPLOAD_BYTES + 1)
    try:
        ftype = validate_upload(file.filename or "", data)
        text = extract_text(ftype, data)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    except Exception:
        raise HTTPException(422, "Could not read the document; it may be corrupted.")
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    path = os.path.join(config.UPLOAD_DIR, f"{uuid.uuid4()}.{ftype}")  # server-chosen name, no traversal
    with open(path, "wb") as fh:
        fh.write(data)
    summary, clauses = llm_service.analyze_document(text)
    doc = LegalDocument(user_id=user.id, file_path=path, original_name=os.path.basename(file.filename or "file"),
                        file_type=config.ALLOWED_UPLOAD_TYPES[ftype], summary=summary,
                        key_clauses=json.dumps(clauses))
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return _out(doc)


@router.get("")
def list_documents(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    docs = (db.query(LegalDocument).filter(LegalDocument.user_id == user.id)
            .order_by(LegalDocument.uploaded_at.desc()).all())
    return [_out(d) for d in docs]


@router.get("/{did}")
def get_document(did: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _out(_owned(db, user, did))


@router.delete("/{did}", status_code=204)
def delete_document(did: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = _owned(db, user, did)
    try:
        os.remove(doc.file_path)
    except OSError:
        pass
    db.delete(doc)
    db.commit()
