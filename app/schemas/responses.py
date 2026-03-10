from pydantic import BaseModel
from typing import Optional, Any

class UploadResponse(BaseModel):
    cv_file_id: str

class JobCreateResponse(BaseModel):
    job_id: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    error_message: Optional[str] = None

class JobResultResponse(BaseModel):
    job_id: str
    result: Any