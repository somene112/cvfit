"""
Phase 5 backend tests — Application Package and Cover Letter APIs.

Tests follow the same in-memory fake DB pattern established in
test_phase5_applications_profile.py. No real database required.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api.routes.applications import router as applications_router
from app.api.routes.profile import router as profile_router
from app.core.security import create_access_token
from app.db.models import (
    AnalysisJob,
    Application,
    ApplicationArtifact,
    CareerProfileItem,
    User,
)
from app.db.session import get_db
from app.api.deps import get_current_user


# ---------------------------------------------------------------------------
# Fake DB (mirrors test_phase5_applications_profile.py)
# ---------------------------------------------------------------------------

class FakeDb:
    def __init__(self):
        self._store: dict[tuple, Any] = {}
        self._query_results: dict[type, list] = {}

    def _key(self, model, pk):
        return (model.__tablename__, pk)

    def add(self, obj):
        pk = obj.id
        self._store[self._key(type(obj), pk)] = obj
        model_type = type(obj)
        if model_type not in self._query_results:
            self._query_results[model_type] = []
        if obj not in self._query_results[model_type]:
            self._query_results[model_type].append(obj)

    def get(self, model, pk):
        return self._store.get(self._key(model, pk))

    def delete(self, obj):
        key = self._key(type(obj), obj.id)
        self._store.pop(key, None)
        lst = self._query_results.get(type(obj), [])
        if obj in lst:
            lst.remove(obj)

    def commit(self):
        pass

    def refresh(self, obj):
        pass

    def query(self, model):
        return FakeQuery(self._query_results.get(model, []), model)


class FakeQuery:
    def __init__(self, rows, model):
        self._rows = list(rows)
        self._model = model

    def filter(self, *args):
        new_rows = list(self._rows)
        for expr in args:
            try:
                col_key = expr.left.key
                col_val = expr.right.value
                new_rows = [r for r in new_rows if getattr(r, col_key, None) == col_val]
            except AttributeError:
                pass
        return FakeQuery(new_rows, self._model)

    def order_by(self, *args):
        try:
            col_key = args[0].key
        except Exception:
            return self
        try:
            self._rows = sorted(
                self._rows,
                key=lambda r: getattr(r, col_key, None) or datetime.min,
                reverse=True,
            )
        except Exception:
            pass
        return self

    def all(self):
        return list(self._rows)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(email: str = "user@example.com") -> User:
    return User(id=uuid.uuid4(), email=email, password_hash="hash", is_active=True)


def make_application(
    user_id: uuid.UUID,
    status: str = "draft",
    best_analysis_job_id: Optional[uuid.UUID] = None,
    company_name: Optional[str] = "TestCo",
) -> Application:
    now = datetime.utcnow()
    return Application(
        id=uuid.uuid4(),
        user_id=user_id,
        job_title="Backend Developer",
        company_name=company_name,
        jd_text="We need a backend developer with Python, FastAPI and PostgreSQL skills.",
        target_role="Backend",
        status=status,
        best_analysis_job_id=best_analysis_job_id,
        created_at=now,
        updated_at=now,
    )


def make_job(
    user_id: uuid.UUID,
    status: str = "succeeded",
    fit_score: float = 78.5,
    matched_skills: Optional[list] = None,
    missing_skills: Optional[list] = None,
) -> AnalysisJob:
    now = datetime.utcnow()
    if matched_skills is None:
        matched_skills = [
            {"skill": "FastAPI", "requirement_type": "must_have"},
            {"skill": "PostgreSQL", "requirement_type": "must_have"},
        ]
    if missing_skills is None:
        missing_skills = [
            {"skill": "Docker", "requirement_type": "nice_to_have"},
        ]
    result_json = {
        "overall_fit_score": fit_score,
        "scores": {"fit_score": fit_score},
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
    } if status == "succeeded" else None
    return AnalysisJob(
        id=uuid.uuid4(),
        user_id=user_id,
        cv_file_id=uuid.uuid4(),
        jd_id=uuid.uuid4(),
        status=status,
        progress=100 if status == "succeeded" else 0,
        result_json=result_json,
        created_at=now,
        updated_at=now,
    )


def make_profile_item(
    user_id: uuid.UUID,
    item_type: str = "project",
    title: str = "E-commerce API",
    skills: Optional[list] = None,
) -> CareerProfileItem:
    now = datetime.utcnow()
    return CareerProfileItem(
        id=uuid.uuid4(),
        user_id=user_id,
        item_type=item_type,
        title=title,
        description="Built a REST API using FastAPI and PostgreSQL.",
        skills_json=skills or ["FastAPI", "PostgreSQL"],
        evidence_text="github.com/user/project",
        source="GitHub",
        created_at=now,
        updated_at=now,
    )


def make_artifact(
    user_id: uuid.UUID,
    application_id: uuid.UUID,
    artifact_type: str = "application_package",
    payload: Optional[dict] = None,
) -> ApplicationArtifact:
    now = datetime.utcnow()
    default_payload = {
        "readiness_summary": {"readiness_level": "ready", "fit_score": 78.5},
        "disclaimer": "Test disclaimer.",
    }
    return ApplicationArtifact(
        id=uuid.uuid4(),
        user_id=user_id,
        application_id=application_id,
        artifact_type=artifact_type,
        payload_json=payload or default_payload,
        created_at=now,
    )


def make_cover_letter_artifact(
    user_id: uuid.UUID,
    application_id: uuid.UUID,
) -> ApplicationArtifact:
    now = datetime.utcnow()
    payload = {
        "opening": "I am writing to express my interest.",
        "why_role_company": "This role aligns with my background.",
        "relevant_evidence": [{"evidence_item": "FastAPI experience", "source": "matched_skill", "cv_reference": "matched_skill: FastAPI"}],
        "contribution_fit": "My skills match the role requirements.",
        "closing": "I look forward to discussing further.",
        "review_notes": ["Please verify claims."],
        "missing_evidence": [],
        "disclaimer": "This is a draft cover letter generated from your CV and job description. It must be reviewed and edited before submission. It does not guarantee any hiring outcome.",
    }
    return ApplicationArtifact(
        id=uuid.uuid4(),
        user_id=user_id,
        application_id=application_id,
        artifact_type="cover_letter_draft",
        payload_json=payload,
        created_at=now,
    )


def build_app_client(db: FakeDb, user: User) -> TestClient:
    app = FastAPI()
    app.include_router(applications_router)
    app.include_router(profile_router)
    token = create_access_token(str(user.id))
    db.add(user)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    client = TestClient(app)
    client._auth_headers = {"Authorization": f"Bearer {token}"}
    return client


def build_unauthed_client(db: FakeDb) -> TestClient:
    app = FastAPI()
    app.include_router(applications_router)
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Auth tests
# ---------------------------------------------------------------------------

class TestPackageAuth:
    def test_generate_package_without_auth_returns_401(self):
        db = FakeDb()
        client = build_unauthed_client(db)
        resp = client.post(f"/v1/applications/{uuid.uuid4()}/package/generate")
        assert resp.status_code == 401

    def test_get_package_without_auth_returns_401(self):
        db = FakeDb()
        client = build_unauthed_client(db)
        assert client.get(f"/v1/applications/{uuid.uuid4()}/package").status_code == 401

    def test_download_package_without_auth_returns_401(self):
        db = FakeDb()
        client = build_unauthed_client(db)
        assert client.get(f"/v1/applications/{uuid.uuid4()}/package/download").status_code == 401

    def test_generate_cover_letter_without_auth_returns_401(self):
        db = FakeDb()
        client = build_unauthed_client(db)
        resp = client.post(f"/v1/applications/{uuid.uuid4()}/cover-letter/generate")
        assert resp.status_code == 401

    def test_get_cover_letter_without_auth_returns_401(self):
        db = FakeDb()
        client = build_unauthed_client(db)
        assert client.get(f"/v1/applications/{uuid.uuid4()}/cover-letter").status_code == 401

    def test_patch_cover_letter_without_auth_returns_401(self):
        db = FakeDb()
        client = build_unauthed_client(db)
        assert client.patch(f"/v1/applications/{uuid.uuid4()}/cover-letter", json={}).status_code == 401


# ---------------------------------------------------------------------------
# Ownership tests
# ---------------------------------------------------------------------------

class TestArtifactOwnership:
    def test_user_cannot_get_another_users_package(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        app_b = make_application(user_b.id)
        artifact_b = make_artifact(user_b.id, app_b.id, "application_package")
        db.add(app_b)
        db.add(artifact_b)
        client = build_app_client(db, user_a)

        resp = client.get(f"/v1/applications/{app_b.id}/package")

        assert resp.status_code == 404

    def test_user_cannot_get_another_users_cover_letter(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        app_b = make_application(user_b.id)
        artifact_b = make_cover_letter_artifact(user_b.id, app_b.id)
        db.add(app_b)
        db.add(artifact_b)
        client = build_app_client(db, user_a)

        resp = client.get(f"/v1/applications/{app_b.id}/cover-letter")

        assert resp.status_code == 404

    def test_artifact_response_never_includes_storage_key(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        artifact = make_artifact(user.id, app.id, "application_package")
        artifact.storage_key = "s3://bucket/secret-key"
        db.add(app)
        db.add(artifact)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/package")

        assert resp.status_code == 200
        assert "storage_key" not in resp.json()

    def test_user_cannot_generate_package_for_another_users_application(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        app_b = make_application(user_b.id)
        db.add(app_b)
        client = build_app_client(db, user_a)

        resp = client.post(f"/v1/applications/{app_b.id}/package/generate")

        assert resp.status_code == 404

    def test_user_cannot_generate_cover_letter_for_another_users_application(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        app_b = make_application(user_b.id)
        db.add(app_b)
        client = build_app_client(db, user_a)

        resp = client.post(f"/v1/applications/{app_b.id}/cover-letter/generate")

        assert resp.status_code == 404

    def test_user_cannot_generate_cover_letter_using_another_users_job(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        job_b = make_job(user_b.id)
        app_a = make_application(user_a.id, best_analysis_job_id=job_b.id)
        db.add(app_a)
        db.add(job_b)
        client = build_app_client(db, user_a)

        resp = client.post(f"/v1/applications/{app_a.id}/cover-letter/generate")

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Package generation tests
# ---------------------------------------------------------------------------

class TestPackageGeneration:
    def test_generate_package_without_analysis_returns_422(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.post(f"/v1/applications/{app.id}/package/generate")

        assert resp.status_code == 422
        assert "attach" in resp.json()["detail"].lower()

    def test_generate_package_with_analysis_returns_201(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id, fit_score=78.5)
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        resp = client.post(f"/v1/applications/{app.id}/package/generate")

        assert resp.status_code == 201
        body = resp.json()
        assert body["application_id"] == str(app.id)
        assert body["artifact_type"] == "application_package"
        assert body["status"] == "generated"
        assert "artifact_id" in body

    def test_package_payload_includes_readiness_summary(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id, fit_score=80.0)
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        client.post(f"/v1/applications/{app.id}/package/generate")
        resp = client.get(f"/v1/applications/{app.id}/package")

        assert resp.status_code == 200
        payload = resp.json()["payload_json"]
        assert "readiness_summary" in payload
        assert payload["readiness_summary"]["readiness_level"] == "ready"
        assert payload["readiness_summary"]["fit_score"] == 80.0

    def test_package_payload_includes_best_cv_analysis(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id, fit_score=60.0)
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        client.post(f"/v1/applications/{app.id}/package/generate")
        resp = client.get(f"/v1/applications/{app.id}/package")

        payload = resp.json()["payload_json"]
        assert "best_cv_analysis" in payload
        assert "matched_skills" in payload["best_cv_analysis"]
        assert "missing_skills" in payload["best_cv_analysis"]

    def test_package_payload_includes_disclaimer(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        client.post(f"/v1/applications/{app.id}/package/generate")
        resp = client.get(f"/v1/applications/{app.id}/package")

        payload = resp.json()["payload_json"]
        assert "disclaimer" in payload
        assert len(payload["disclaimer"]) > 0

    def test_get_package_returns_404_when_not_generated(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/package")

        assert resp.status_code == 404

    def test_get_package_returns_latest_artifact(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        client.post(f"/v1/applications/{app.id}/package/generate")
        resp = client.get(f"/v1/applications/{app.id}/package")

        assert resp.status_code == 200
        assert resp.json()["artifact_type"] == "application_package"
        assert resp.json()["application_id"] == str(app.id)

    def test_download_package_returns_json_with_download_format(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        client.post(f"/v1/applications/{app.id}/package/generate")
        resp = client.get(f"/v1/applications/{app.id}/package/download")

        assert resp.status_code == 200
        body = resp.json()
        assert body["download_format"] == "json"
        assert body["artifact_type"] == "application_package"
        assert "payload_json" in body
        assert "storage_key" not in body

    def test_download_package_returns_404_when_not_generated(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/package/download")

        assert resp.status_code == 404

    def test_package_includes_evidence_checklist_for_matched_skills(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id, fit_score=70.0, matched_skills=[{"skill": "FastAPI", "requirement_type": "must_have"}])
        app = make_application(user.id, best_analysis_job_id=job.id)
        profile_item = make_profile_item(user.id, skills=["FastAPI", "PostgreSQL"])
        db.add(app)
        db.add(job)
        db.add(profile_item)
        client = build_app_client(db, user)

        client.post(f"/v1/applications/{app.id}/package/generate")
        resp = client.get(f"/v1/applications/{app.id}/package")

        payload = resp.json()["payload_json"]
        checklist = payload.get("evidence_checklist", [])
        fastapi_entry = next((e for e in checklist if e["skill"] == "FastAPI"), None)
        assert fastapi_entry is not None
        assert fastapi_entry["has_profile_evidence"] is True


# ---------------------------------------------------------------------------
# Cover letter generation tests
# ---------------------------------------------------------------------------

class TestCoverLetterGeneration:
    def test_generate_cover_letter_without_analysis_returns_422(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.post(f"/v1/applications/{app.id}/cover-letter/generate")

        assert resp.status_code == 422
        assert "attach" in resp.json()["detail"].lower()

    def test_generate_cover_letter_returns_201(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        resp = client.post(f"/v1/applications/{app.id}/cover-letter/generate")

        assert resp.status_code == 201
        body = resp.json()
        assert body["application_id"] == str(app.id)
        assert body["artifact_type"] == "cover_letter_draft"
        assert body["status"] == "generated"

    def test_cover_letter_payload_has_required_structure(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        client.post(f"/v1/applications/{app.id}/cover-letter/generate")
        resp = client.get(f"/v1/applications/{app.id}/cover-letter")

        assert resp.status_code == 200
        cl = resp.json()["payload_json"]
        for key in ("opening", "why_role_company", "relevant_evidence", "contribution_fit",
                    "closing", "review_notes", "missing_evidence", "disclaimer"):
            assert key in cl, f"Missing key: {key}"

    def test_cover_letter_missing_skills_go_to_missing_evidence_not_body(self):
        user = make_user()
        db = FakeDb()
        job = make_job(
            user.id,
            matched_skills=[{"skill": "FastAPI", "requirement_type": "must_have"}],
            missing_skills=[{"skill": "Kubernetes", "requirement_type": "must_have"}],
        )
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        client.post(f"/v1/applications/{app.id}/cover-letter/generate")
        resp = client.get(f"/v1/applications/{app.id}/cover-letter")
        cl = resp.json()["payload_json"]

        assert any("Kubernetes" in item for item in cl["missing_evidence"])
        body_text = cl["opening"] + cl["why_role_company"] + cl["contribution_fit"]
        assert "I am proficient in Kubernetes" not in body_text
        assert "expertise in Kubernetes" not in body_text

    def test_cover_letter_weak_evidence_flagged_in_review_notes(self):
        user = make_user()
        db = FakeDb()
        job = make_job(
            user.id,
            matched_skills=[{"skill": "Docker", "requirement_type": "must_have"}],
            missing_skills=[],
        )
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        # No profile items with Docker evidence
        client = build_app_client(db, user)

        client.post(f"/v1/applications/{app.id}/cover-letter/generate")
        resp = client.get(f"/v1/applications/{app.id}/cover-letter")
        cl = resp.json()["payload_json"]

        notes_text = " ".join(cl["review_notes"])
        assert "Docker" in notes_text

    def test_cover_letter_uses_neutral_wording_when_company_name_missing(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        app = make_application(user.id, best_analysis_job_id=job.id, company_name=None)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        client.post(f"/v1/applications/{app.id}/cover-letter/generate")
        resp = client.get(f"/v1/applications/{app.id}/cover-letter")
        cl = resp.json()["payload_json"]

        full_text = " ".join([
            cl["opening"], cl["why_role_company"], cl["contribution_fit"], cl["closing"]
        ])
        assert "None" not in full_text
        assert "[Company]" not in full_text
        notes_text = " ".join(cl["review_notes"])
        assert "company" in notes_text.lower()

    def test_cover_letter_includes_disclaimer(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        client.post(f"/v1/applications/{app.id}/cover-letter/generate")
        resp = client.get(f"/v1/applications/{app.id}/cover-letter")
        cl = resp.json()["payload_json"]

        assert cl["disclaimer"]
        assert "draft" in cl["disclaimer"].lower()
        assert "does not guarantee" in cl["disclaimer"].lower()

    def test_cover_letter_get_returns_404_when_not_generated(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/cover-letter")

        assert resp.status_code == 404

    def test_cover_letter_response_does_not_include_storage_key(self):
        user = make_user()
        db = FakeDb()
        job = make_job(user.id)
        app = make_application(user.id, best_analysis_job_id=job.id)
        db.add(app)
        db.add(job)
        client = build_app_client(db, user)

        client.post(f"/v1/applications/{app.id}/cover-letter/generate")
        resp = client.get(f"/v1/applications/{app.id}/cover-letter")

        assert "storage_key" not in resp.json()


# ---------------------------------------------------------------------------
# Cover letter PATCH tests
# ---------------------------------------------------------------------------

class TestCoverLetterPatch:
    def test_patch_cover_letter_updates_allowed_fields(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        artifact = make_cover_letter_artifact(user.id, app.id)
        db.add(app)
        db.add(artifact)
        client = build_app_client(db, user)

        resp = client.patch(f"/v1/applications/{app.id}/cover-letter", json={
            "opening": "Updated opening text.",
            "closing": "Updated closing text.",
        })

        assert resp.status_code == 200
        cl = resp.json()["payload_json"]
        assert cl["opening"] == "Updated opening text."
        assert cl["closing"] == "Updated closing text."

    def test_patch_cover_letter_preserves_disclaimer(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        original_disclaimer = "This is a draft cover letter generated from your CV and job description. It must be reviewed and edited before submission. It does not guarantee any hiring outcome."
        artifact = make_cover_letter_artifact(user.id, app.id)
        db.add(app)
        db.add(artifact)
        client = build_app_client(db, user)

        resp = client.patch(f"/v1/applications/{app.id}/cover-letter", json={
            "opening": "Changed opening.",
        })

        assert resp.status_code == 200
        cl = resp.json()["payload_json"]
        assert cl["disclaimer"] == original_disclaimer

    def test_patch_cover_letter_cannot_change_artifact_type(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        artifact = make_cover_letter_artifact(user.id, app.id)
        db.add(app)
        db.add(artifact)
        client = build_app_client(db, user)

        resp = client.patch(f"/v1/applications/{app.id}/cover-letter", json={
            "artifact_type": "application_package",
            "opening": "Changed opening.",
        })

        assert resp.status_code == 200
        assert resp.json()["artifact_type"] == "cover_letter_draft"

    def test_patch_cover_letter_returns_404_when_not_generated(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.patch(f"/v1/applications/{app.id}/cover-letter", json={
            "opening": "New opening.",
        })

        assert resp.status_code == 404

    def test_patch_cover_letter_updates_relevant_evidence_list(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        artifact = make_cover_letter_artifact(user.id, app.id)
        db.add(app)
        db.add(artifact)
        client = build_app_client(db, user)

        new_evidence = [
            {"evidence_item": "New project evidence", "source": "profile_item", "cv_reference": "project: My App"}
        ]
        resp = client.patch(f"/v1/applications/{app.id}/cover-letter", json={
            "relevant_evidence": new_evidence,
        })

        assert resp.status_code == 200
        cl = resp.json()["payload_json"]
        assert cl["relevant_evidence"] == new_evidence

    def test_patch_cover_letter_for_another_users_application_returns_404(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        db = FakeDb()
        app_b = make_application(user_b.id)
        artifact_b = make_cover_letter_artifact(user_b.id, app_b.id)
        db.add(app_b)
        db.add(artifact_b)
        client = build_app_client(db, user_a)

        resp = client.patch(f"/v1/applications/{app_b.id}/cover-letter", json={
            "opening": "Hacked opening.",
        })

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Regression tests
# ---------------------------------------------------------------------------

class TestRegression:
    def test_existing_application_crud_still_works(self):
        user = make_user()
        db = FakeDb()
        client = build_app_client(db, user)

        resp = client.post("/v1/applications", json={
            "job_title": "Backend Developer",
            "jd_text": "Looking for a Python/FastAPI developer.",
        })

        assert resp.status_code == 201
        assert resp.json()["status"] == "draft"

    def test_existing_profile_crud_still_works(self):
        user = make_user()
        db = FakeDb()
        client = build_app_client(db, user)

        resp = client.post("/v1/profile/items", json={
            "item_type": "project",
            "title": "My Project",
            "description": "Built with FastAPI.",
        })

        assert resp.status_code == 201
        assert resp.json()["title"] == "My Project"

    def test_readiness_endpoint_still_returns_not_started(self):
        user = make_user()
        db = FakeDb()
        app = make_application(user.id)
        db.add(app)
        client = build_app_client(db, user)

        resp = client.get(f"/v1/applications/{app.id}/readiness")

        assert resp.status_code == 200
        assert resp.json()["readiness_level"] == "not_started"
