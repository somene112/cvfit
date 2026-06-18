import uuid
from datetime import datetime

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    from sqlalchemy import JSON

    def Vector(dim):
        return JSON

from sqlalchemy import Boolean, String, Text, DateTime, Integer, Enum, ForeignKey, true
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

JOB_STATUS = ("queued", "running", "succeeded", "failed")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    jobs = relationship("AnalysisJob", back_populates="user")


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
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    parent_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_jobs.id"),
        nullable=True,
        index=True,
    )
    analysis_group_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    status: Mapped[str] = mapped_column(Enum(*JOB_STATUS, name="job_status"), default="queued")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    result_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    report_docx_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    access_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cv_file = relationship("CVFile", back_populates="jobs")
    jd_doc = relationship("JDDoc", back_populates="jobs")
    user = relationship("User", back_populates="jobs")


APPLICATION_STATUS = (
    "draft",
    "analyzing",
    "improving_cv",
    "ready_to_apply",
    "interview_prep",
    "applied",
    "archived",
    # Phase 6 Target Jobs statuses (additive; Phase 5 statuses preserved above).
    "saved",
    "interviewing",
    "rejected",
    "offer",
)

CAREER_PROFILE_ITEM_TYPE = (
    "skill",
    "project",
    "experience",
    "education",
    "certification",
    "achievement",
    "link",
)


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    jd_text: Mapped[str] = mapped_column(Text, nullable=False)
    target_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(*APPLICATION_STATUS, name="application_status"),
        nullable=False,
        default="draft",
        server_default="draft",
        index=True,
    )
    # nullable FK — attached after creation via attach-analysis endpoint
    best_analysis_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_jobs.id"),
        nullable=True,
        index=True,
    )
    # Phase 6 Target Jobs additive fields (all nullable; Phase 5 rows leave them NULL).
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_readiness_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])
    best_analysis_job = relationship("AnalysisJob", foreign_keys=[best_analysis_job_id])


class CareerProfileItem(Base):
    __tablename__ = "career_profile_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    item_type: Mapped[str] = mapped_column(
        Enum(*CAREER_PROFILE_ITEM_TYPE, name="career_profile_item_type"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    evidence_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])


ARTIFACT_TYPE = (
    "application_package",
    "cover_letter_draft",
    "interview_practice_result",
    "readiness_summary",
)


class ApplicationArtifact(Base):
    __tablename__ = "application_artifacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    application_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True)
    artifact_type: Mapped[str] = mapped_column(
        Enum(*ARTIFACT_TYPE, name="application_artifact_type"),
        nullable=False,
        index=True,
    )
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])
    application = relationship("Application", foreign_keys=[application_id])


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    application_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("analysis_jobs.id"), nullable=True, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    rubric_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    feedback_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])
    application = relationship("Application", foreign_keys=[application_id])
    job = relationship("AnalysisJob", foreign_keys=[job_id])


class TextEmbedding(Base):
    __tablename__ = "text_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_type: Mapped[str] = mapped_column(String(50))
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list] = mapped_column(Vector(384))
    meta_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Phase 6 — Learning Roadmap
#
# Constrained fields (priority / task_type / status) are stored as plain
# strings and validated at the Pydantic schema layer. This keeps the migration
# additive (plain CREATE TABLE) and avoids native enum-type churn. Allowed
# values are documented here for reference.
# ---------------------------------------------------------------------------

LEARNING_TASK_PRIORITY = ("high", "medium", "low")
LEARNING_TASK_TYPE = ("article", "project", "practice", "interview_prep", "profile_evidence")
LEARNING_TASK_STATUS = ("todo", "in_progress", "done")


class LearningTask(Base):
    __tablename__ = "learning_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    target_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True, index=True)
    application_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True, index=True)
    analysis_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("analysis_jobs.id"), nullable=True, index=True)
    skill: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    task_type: Mapped[str] = mapped_column(String(30), nullable=False, default="practice")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_to_add: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="todo", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])


# ---------------------------------------------------------------------------
# Phase 6 — Interview Practice v2 (sessions / questions / answers)
#
# Additive tables — the Phase 5 `interview_answers` table is left untouched.
# Constrained fields stored as strings, validated at the Pydantic layer.
# ---------------------------------------------------------------------------

INTERVIEW_QUESTION_TYPE = ("technical", "behavioral", "project", "HR", "gap_check")
INTERVIEW_DIFFICULTY = ("easy", "medium", "hard")
INTERVIEW_SESSION_TYPE = ("mixed", "technical", "behavioral", "project", "HR", "gap_check")
INTERVIEW_SESSION_STATUS = ("active", "completed", "archived")
INTERVIEW_RUBRIC_DIMENSIONS = ("relevance", "evidence", "clarity", "structure", "confidence", "risk")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    target_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True, index=True)
    application_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True, index=True)
    analysis_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("analysis_jobs.id"), nullable=True, index=True)
    session_type: Mapped[str] = mapped_column(String(30), nullable=False, default="mixed")
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])


class InterviewSessionQuestion(Base):
    __tablename__ = "interview_session_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False, index=True)
    question_type: Mapped[str] = mapped_column(String(30), nullable=False, default="behavioral")
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    related_evidence_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    rubric_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session = relationship("InterviewSession", foreign_keys=[session_id])


class InterviewSessionAnswer(Base):
    __tablename__ = "interview_session_answers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False, index=True)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interview_session_questions.id"), nullable=False, index=True)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    score_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    feedback_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session = relationship("InterviewSession", foreign_keys=[session_id])
    question = relationship("InterviewSessionQuestion", foreign_keys=[question_id])
