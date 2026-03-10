from pydantic import BaseModel, Field
from typing import Literal, List, Optional

class ScoreOptions(BaseModel):
    target_role: Optional[str] = None
    language: Literal["vi","en"] = "vi"
    strictness: Literal["lenient","balanced","strict"] = "balanced"
    output_formats: List[Literal["json","docx"]] = ["json","docx"]

class ScoreCreateRequest(BaseModel):
    cv_file_id: str
    jd_text: str = Field(min_length=30)
    options: ScoreOptions = ScoreOptions()