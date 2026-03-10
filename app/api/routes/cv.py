import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import CVFile
from app.services.storage import save_upload
from app.schemas.responses import UploadResponse

router = APIRouter(prefix="/v1/cv", tags=["cv"])

@router.post("/upload", response_model=UploadResponse)
def upload_cv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    suffix = (file.filename.split(".")[-1] or "").lower()
    if suffix not in ("pdf", "docx", "doc"):
        raise HTTPException(status_code=400, detail="Only pdf/doc/docx supported")

    path, digest, mime = save_upload(file)
    row = CVFile(
        id=uuid.uuid4(),
        original_filename=file.filename,
        mime_type=mime,
        storage_path=path,
        sha256=digest,
    )
    db.add(row)
    db.commit()
    return UploadResponse(cv_file_id=str(row.id))