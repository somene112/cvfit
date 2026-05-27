from __future__ import annotations

import json
import mimetypes
import os
import sys
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


DEFAULT_TIMEOUT_SECONDS = 300
POLL_INTERVAL_SECONDS = 3
REQUEST_TIMEOUT_SECONDS = 45
TERMINAL_STATUSES = {"succeeded", "failed"}
DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


class SmokeError(RuntimeError):
    pass


class HttpStatusError(SmokeError):
    def __init__(self, status_code: int):
        super().__init__(f"unexpected HTTP status {status_code}")
        self.status_code = status_code


def normalize_base_url(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise SmokeError("API_BASE_URL is required")
    if not cleaned.startswith(("http://", "https://")):
        raise SmokeError("API_BASE_URL must start with http:// or https://")
    return cleaned.rstrip("/")


def configured_timeout() -> int:
    raw_value = os.environ.get("SMOKE_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)).strip()
    try:
        timeout = int(raw_value)
    except ValueError as exc:
        raise SmokeError("SMOKE_TIMEOUT_SECONDS must be an integer") from exc
    if timeout <= 0:
        raise SmokeError("SMOKE_TIMEOUT_SECONDS must be greater than zero")
    return timeout


def configured_cv_path() -> Path:
    raw_value = os.environ.get("TEST_CV_PATH", "").strip()
    if not raw_value:
        raise SmokeError("TEST_CV_PATH is required; use a dummy PDF or DOCX CV")
    path = Path(raw_value)
    if not path.is_file():
        raise SmokeError("TEST_CV_PATH must point to an existing file")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise SmokeError("TEST_CV_PATH must point to a PDF or DOCX file")
    return path


def build_url(base_url: str, path: str) -> str:
    return urljoin(f"{base_url}/", path.lstrip("/"))


def request(
    base_url: str,
    method: str,
    path: str,
    *,
    body: dict | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = REQUEST_TIMEOUT_SECONDS,
) -> tuple[int, dict[str, str], bytes]:
    data = None
    final_headers = dict(headers or {})
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        final_headers["Content-Type"] = "application/json"

    req = Request(build_url(base_url, path), data=data, headers=final_headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as response:
            return response.status, dict(response.headers.items()), response.read()
    except HTTPError as exc:
        exc.read()
        return exc.code, dict(exc.headers.items()), b""


def request_json(base_url: str, method: str, path: str, *, body: dict | None = None) -> dict:
    status_code, _, response_body = request(base_url, method, path, body=body)
    if status_code < 200 or status_code >= 300:
        raise HttpStatusError(status_code)
    if not response_body:
        return {}
    return json.loads(response_body.decode("utf-8"))


def expect_rejected(base_url: str, method: str, path: str, label: str) -> None:
    status_code, _, _ = request(base_url, method, path)
    if status_code not in {401, 403}:
        raise SmokeError(f"{label} was not rejected with 401/403")
    print(f"{label} rejected")


def post_multipart_file(base_url: str, path: str, field_name: str, file_path: Path) -> dict:
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    if file_path.suffix.lower() == ".docx":
        content_type = DOCX_CONTENT_TYPE

    boundary = f"----cvfit-phase1-smoke-{uuid.uuid4().hex}"
    parts = [
        f"--{boundary}\r\n".encode("utf-8"),
        (
            f'Content-Disposition: form-data; name="{field_name}"; '
            f'filename="{file_path.name}"\r\n'
        ).encode("utf-8"),
        f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
        file_path.read_bytes(),
        b"\r\n",
        f"--{boundary}--\r\n".encode("utf-8"),
    ]
    req = Request(
        build_url(base_url, path),
        data=b"".join(parts),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        exc.read()
        raise HttpStatusError(exc.code) from exc


def poll_job(base_url: str, job_id: str, timeout_seconds: int) -> dict:
    deadline = time.monotonic() + timeout_seconds
    last_status: dict = {}
    while time.monotonic() < deadline:
        last_status = request_json(base_url, "GET", f"/v1/jobs/{job_id}")
        status = last_status.get("status")
        progress = last_status.get("progress")
        print(f"job status={status} progress={progress}")
        if status in TERMINAL_STATUSES:
            return last_status
        time.sleep(POLL_INTERVAL_SECONDS)
    raise SmokeError(f"job timed out after {timeout_seconds}s")


def verify_no_internal_fields(payload: object, label: str) -> None:
    text = json.dumps(payload, sort_keys=True)
    forbidden = [
        "local_path",
        "access_token",
        "bucket",
        "storage_path",
        "report_docx_path",
        "access_token_hash",
        "file_path",
        "s3_key",
        "object_key",
        "raw_cv_text",
        "cv_text",
    ]
    leaked = [key for key in forbidden if key in text]
    if leaked:
        raise SmokeError(f"{label} exposed internal fields")


def run_smoke(base_url: str, cv_path: Path, timeout_seconds: int) -> int:
    health = request_json(base_url, "GET", "/health")
    if health.get("status") != "ok":
        raise SmokeError("unexpected health response")
    print("health ok")

    uploaded = post_multipart_file(base_url, "/v1/cv/upload", "file", cv_path)
    verify_no_internal_fields(uploaded, "upload response")
    cv_id = uploaded.get("cv_id") or uploaded.get("cv_file_id")
    if not cv_id:
        raise SmokeError("upload response missing cv_id/cv_file_id")
    print("upload ok")

    job = request_json(
        base_url,
        "POST",
        "/v1/jobs/create-score",
        body={
            "cv_id": cv_id,
            "job_description": (
                "Backend Engineer role requiring Python, FastAPI, PostgreSQL, Redis, "
                "Docker, SQL, API testing, background workers, and deployment checks."
            ),
        },
    )
    job_id = job.get("job_id")
    access_token = job.get("access_token")
    if not job_id:
        raise SmokeError("create-score response missing job_id")
    if not access_token:
        raise SmokeError("create-score response missing access_token")
    print("create-score ok")

    wrong_query = urlencode({"access_token": "wrong-token"})
    expect_rejected(base_url, "GET", f"/v1/jobs/{job_id}/result", "result without token")
    expect_rejected(base_url, "GET", f"/v1/jobs/{job_id}/result?{wrong_query}", "result with wrong token")
    expect_rejected(base_url, "GET", f"/v1/jobs/{job_id}/report", "report without token")
    expect_rejected(base_url, "GET", f"/v1/jobs/{job_id}/report?{wrong_query}", "report with wrong token")
    expect_rejected(base_url, "GET", f"/v1/jobs/{job_id}/report/download", "download without token")
    expect_rejected(base_url, "GET", f"/v1/jobs/{job_id}/report/download?{wrong_query}", "download with wrong token")

    final_status = poll_job(base_url, job_id, timeout_seconds)
    if final_status.get("status") == "failed":
        raise SmokeError("job failed; inspect backend logs for sanitized error details")
    if final_status.get("status") != "succeeded":
        raise SmokeError("job ended with unexpected status")

    token_query = urlencode({"access_token": access_token})
    result = request_json(base_url, "GET", f"/v1/jobs/{job_id}/result?{token_query}")
    verify_no_internal_fields(result, "result response")
    if "result" not in result and "overall_fit_score" not in result:
        raise SmokeError("result response missing result/overall_fit_score")
    print("result with correct token ok")

    report = request_json(base_url, "GET", f"/v1/jobs/{job_id}/report?{token_query}")
    report_without_download_url = {key: value for key, value in report.items() if key != "download_url"}
    verify_no_internal_fields(report_without_download_url, "report response")
    if report.get("report_status") not in {None, "ready"}:
        raise SmokeError("report response has unexpected status")
    print("report with correct token ok")

    status_code, headers, content = request(
        base_url,
        "GET",
        f"/v1/jobs/{job_id}/report/download?{token_query}",
        timeout=60,
    )
    if status_code != 200:
        raise HttpStatusError(status_code)
    content_type = headers.get("Content-Type") or headers.get("content-type") or ""
    if DOCX_CONTENT_TYPE not in content_type:
        raise SmokeError("download response was not DOCX")
    if len(content) < 100:
        raise SmokeError("downloaded DOCX response was unexpectedly small")
    print(f"download with correct token ok bytes={len(content)}")
    print("phase 1 backend smoke passed")
    return 0


def main() -> int:
    try:
        base_url = normalize_base_url(os.environ.get("API_BASE_URL", ""))
        cv_path = configured_cv_path()
        return run_smoke(base_url, cv_path, configured_timeout())
    except (SmokeError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"phase 1 backend smoke failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
