from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.services.storage.base import UploadValidationError
from app.services.storage.factory import get_storage

CHUNK_SIZE = 1024 * 1024


def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def read_upload_bytes(file: UploadFile, max_bytes: int) -> bytes:
    chunks = []
    total = 0
    while True:
        chunk = file.file.read(CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise UploadValidationError(
                f"CV file too large. Max size is {settings.CV_MAX_UPLOAD_MB} MB.",
                code="CV_FILE_TOO_LARGE",
            )
        chunks.append(chunk)

    if total == 0:
        raise UploadValidationError("Empty CV file", code="CV_FILE_EMPTY")

    return b"".join(chunks)


def save_upload(file: UploadFile) -> tuple[str, str, str]:
    """
    returns (storage_location, sha256, mime_type)
    """
    max_bytes = settings.CV_MAX_UPLOAD_MB * 1024 * 1024
    content = read_upload_bytes(file, max_bytes)
    digest = sha256_bytes(content)

    ext = Path(file.filename or "").suffix.lower() or ".bin"
    key = f"uploads/{uuid.uuid4().hex}{ext}"
    mime = file.content_type or "application/octet-stream"
    location = get_storage().save_bytes(key, content, mime)
    return location, digest, mime


def report_key(job_id: str) -> str:
    return f"reports/{job_id}.docx"


def save_report_file(job_id: str, local_path: str) -> str:
    content = Path(local_path).read_bytes()
    return get_storage().save_bytes(
        report_key(job_id),
        content,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


def report_path(job_id: str) -> str:
    return report_key(job_id)
