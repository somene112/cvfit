import os, uuid, hashlib
from pathlib import Path
from fastapi import UploadFile
from app.core.config import settings

UPLOAD_DIR = Path(settings.STORAGE_ROOT) / "uploads"
REPORT_DIR = Path(settings.STORAGE_ROOT) / "reports"

def ensure_dirs():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()

def save_upload(file: UploadFile) -> tuple[str, str, str]:
    """
    returns (storage_path, sha256, mime_type)
    """
    ensure_dirs()
    content = file.file.read()
    digest = sha256_bytes(content)

    ext = Path(file.filename).suffix.lower() or ".bin"
    name = f"{uuid.uuid4().hex}{ext}"
    path = UPLOAD_DIR / name

    with open(path, "wb") as f:
        f.write(content)

    mime = file.content_type or "application/octet-stream"
    return str(path), digest, mime

def report_path(job_id: str) -> str:
    ensure_dirs()
    return str(REPORT_DIR / f"{job_id}.docx")