import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.db.models import CVFile
from app.services.storage import UploadValidationError, save_upload
from app.schemas.responses import UploadResponse

router = APIRouter(prefix="/v1/cv", tags=["cv"])
SUPPORTED_CV_EXTENSIONS = {".pdf", ".docx"}

@router.post("/upload", response_model=UploadResponse)
def upload_cv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail={
            "code": "CV_MISSING_FILENAME",
            "message": "Missing filename.",
        })
    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_CV_EXTENSIONS:
        raise HTTPException(status_code=400, detail={
            "code": "CV_UNSUPPORTED_FILE_TYPE",
            "message": "Only PDF and DOCX files are supported.",
        })

    try:
        path, digest, mime = save_upload(file)
        size_bytes = file.file.tell()
    except UploadValidationError as exc:
        detail: dict = {
            "code": exc.code,
            "message": str(exc),
        }
        if exc.code == "CV_FILE_TOO_LARGE":
            detail["max_size_mb"] = settings.CV_MAX_UPLOAD_MB
        raise HTTPException(status_code=400, detail=detail)

    row = CVFile(
        id=uuid.uuid4(),
        original_filename=file.filename,
        mime_type=mime,
        storage_path=path,
        sha256=digest,
    )
    db.add(row)
    db.commit()
    cv_id = str(row.id)
    return UploadResponse(
        cv_file_id=cv_id,
        cv_id=cv_id,
        filename=file.filename,
        content_type=mime,
        size_bytes=size_bytes,
    )
