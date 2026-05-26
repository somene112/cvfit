from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = REPO_ROOT / "frontend"


def test_frontend_app_uses_real_mvp_endpoints():
    script = (FRONTEND_ROOT / "static" / "app.js").read_text(encoding="utf-8")

    assert "Analyze CV clicked" not in script
    assert "alert(" not in script
    assert "/v1/cv/upload" in script
    assert "/v1/jobs/create-score" in script
    assert "/result?access_token=" in script
    assert "/report?access_token=" in script


def test_frontend_template_contains_script_ids():
    html = (FRONTEND_ROOT / "templates" / "index.html").read_text(encoding="utf-8")

    required_ids = [
        "cvFile",
        "fileName",
        "jobDescription",
        "analyzeBtn",
        "statusCard",
        "statusTitle",
        "statusPercent",
        "statusMessage",
        "progressBar",
        "errorState",
        "resultCard",
        "resultSummary",
        "fitScore",
        "scoreBreakdown",
        "skillGaps",
        "downloadReport",
    ]

    for element_id in required_ids:
        assert f'id="{element_id}"' in html


def test_frontend_does_not_print_access_tokens():
    script = (FRONTEND_ROOT / "static" / "app.js").read_text(encoding="utf-8")

    assert "console.log" not in script
    assert "console.error" not in script
    assert "access_token=<hidden>" in script
    assert "redactToken" in script


def test_frontend_uses_same_origin_relative_api_calls():
    script = (FRONTEND_ROOT / "static" / "app.js").read_text(encoding="utf-8")

    assert "API_BASE_URL" not in script
    assert "https://cvfit.onrender.com" not in script
    assert "fetch('/v1/" not in script
    assert "requestJson('/v1/cv/upload'" in script
    assert "requestJson('/v1/jobs/create-score'" in script
