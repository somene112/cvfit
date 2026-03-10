import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

JOB_STATUS = ("queued", "running", "succeeded", "failed")

class CVFile(Base):
    __tablename__ = "cv_files"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(120))
    storage_path: Mapped[str] = mapped_column(String(500))
    sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    jobs = relationship("AnalysisJob", back_populates="cv_file")

class JDDoc(Base):
    __tablename__ = "jd_docs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jd_text: Mapped[str] = mapped_column(Text)
    role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    jobs = relationship("AnalysisJob", back_populates="jd_doc")

class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    cv_file_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cv_files.id"))
    jd_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jd_docs.id"))

    status: Mapped[str] = mapped_column(Enum(*JOB_STATUS, name="job_status"), default="queued")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    result_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    report_docx_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cv_file = relationship("CVFile", back_populates="jobs")
    jd_doc = relationship("JDDoc", back_populates="jobs")