import os
import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, inspect, text


os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _load_adoption_module():
    scripts_dir = BACKEND_ROOT.parent / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    module_path = scripts_dir / "adopt_existing_db_with_alembic.py"
    spec = importlib.util.spec_from_file_location("adopt_existing_db_with_alembic", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_current_checker_module():
    module_path = BACKEND_ROOT.parent / "scripts" / "check_alembic_current.py"
    spec = importlib.util.spec_from_file_location("check_alembic_current", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_alembic_config_exists():
    assert (BACKEND_ROOT / "alembic.ini").is_file()
    assert (BACKEND_ROOT / "alembic" / "env.py").is_file()


def test_initial_migration_exists_and_mentions_current_schema():
    migration = BACKEND_ROOT / "alembic" / "versions" / "20260522_0001_initial_schema.py"

    text = migration.read_text(encoding="utf-8")

    assert "CREATE EXTENSION IF NOT EXISTS vector" in text
    assert '"cv_files"' in text
    assert '"jd_docs"' in text
    assert '"analysis_jobs"' in text
    assert '"text_embeddings"' in text
    assert '"access_token_hash"' in text


def test_models_still_import():
    from app.db import models

    assert models.User.__tablename__ == "users"
    assert models.CVFile.__tablename__ == "cv_files"
    assert models.JDDoc.__tablename__ == "jd_docs"
    assert models.AnalysisJob.__tablename__ == "analysis_jobs"
    assert models.TextEmbedding.__tablename__ == "text_embeddings"


def test_schema_checker_script_tracks_baseline_schema():
    script = BACKEND_ROOT.parent / "scripts" / "check_db_schema.py"

    text = script.read_text(encoding="utf-8")

    assert "REQUIRED_SCHEMA" in text
    assert '"users"' in text
    assert '"analysis_jobs"' in text
    assert '"user_id"' in text
    assert '"access_token_hash"' in text
    assert '"parent_job_id"' in text
    assert '"analysis_group_id"' in text
    assert '"revision_number"' in text
    assert "alembic_version" in text


def test_auth_foundation_migration_exists_and_mentions_schema_changes():
    migration = BACKEND_ROOT / "alembic" / "versions" / "20260531_0001_add_users_and_job_ownership.py"

    text = migration.read_text(encoding="utf-8")

    assert 'revision = "20260531_0001"' in text
    assert 'down_revision = "20260522_0001"' in text
    assert '"users"' in text
    assert '"email"' in text
    assert '"password_hash"' in text
    assert '"user_id"' in text
    assert "fk_analysis_jobs_user_id_users" in text
    assert "ix_analysis_jobs_user_id" in text


def test_analysis_revision_migration_exists_and_mentions_schema_changes():
    migration = BACKEND_ROOT / "alembic" / "versions" / "20260606_0001_add_analysis_revisions.py"

    text = migration.read_text(encoding="utf-8")

    assert 'revision = "20260606_0001"' in text
    assert 'down_revision = "20260531_0001"' in text
    assert '"parent_job_id"' in text
    assert '"analysis_group_id"' in text
    assert '"revision_number"' in text
    assert "fk_analysis_jobs_parent_job_id_analysis_jobs" in text
    assert "ix_analysis_jobs_parent_job_id" in text
    assert "ix_analysis_jobs_analysis_group_id" in text


def test_adoption_logic_refuses_schema_mismatch():
    module = _load_adoption_module()
    result = module.SchemaCheckResult(
        required_tables={"analysis_jobs": {"id", "access_token_hash"}},
        existing_tables={"analysis_jobs"},
        missing_items=["analysis_jobs.access_token_hash"],
        alembic_versions=[],
        vector_extension_exists=True,
        dialect="postgresql",
    )

    assert module.classify_adoption(result, "20260522_0001") == "mismatch"


def test_adoption_logic_allows_stamp_for_matching_unstamped_schema():
    module = _load_adoption_module()
    result = module.SchemaCheckResult(
        required_tables={"analysis_jobs": {"id"}},
        existing_tables={"analysis_jobs"},
        missing_items=[],
        alembic_versions=[],
        vector_extension_exists=True,
        dialect="postgresql",
    )

    assert module.classify_adoption(result, "20260522_0001") == "stamp"


def test_adoption_logic_treats_head_as_already_adopted():
    module = _load_adoption_module()
    result = module.SchemaCheckResult(
        required_tables={"analysis_jobs": {"id"}},
        existing_tables={"analysis_jobs", "alembic_version"},
        missing_items=[],
        alembic_versions=["20260522_0001"],
        vector_extension_exists=True,
        dialect="postgresql",
    )

    assert module.classify_adoption(result, "20260522_0001") == "already_head"


def test_adoption_script_requires_database_url_without_printing_secret(monkeypatch, capsys):
    module = _load_adoption_module()

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(sys, "argv", ["adopt_existing_db_with_alembic.py"])

    assert module.main() == 2
    captured = capsys.readouterr()
    assert "DATABASE_URL is required" in captured.err
    assert "://" not in captured.err


def _sqlite_engine_with_runtime_schema(
    *,
    include_alembic=True,
    alembic_version=None,
    omit_columns=None,
):
    from app.db import init_db

    omit_columns = omit_columns or {}
    alembic_version = alembic_version or init_db.EXPECTED_ALEMBIC_HEAD
    test_engine = create_engine("sqlite+pysqlite:///:memory:")
    with test_engine.begin() as conn:
        for table_name, columns in init_db._required_schema().items():
            column_defs = [
                f'"{column_name}" TEXT'
                for column_name in sorted(columns - omit_columns.get(table_name, set()))
            ]
            conn.execute(text(f'CREATE TABLE "{table_name}" ({", ".join(column_defs)})'))

        if include_alembic:
            conn.execute(text('CREATE TABLE "alembic_version" ("version_num" TEXT NOT NULL)'))
            conn.execute(
                text("INSERT INTO alembic_version (version_num) VALUES (:version_num)"),
                {"version_num": alembic_version},
            )

    return test_engine


def test_runtime_expected_alembic_head_matches_script_head():
    from app.db import init_db

    current_checker = _load_current_checker_module()
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "heads"],
        cwd=BACKEND_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    revisions = current_checker.parse_alembic_revisions(
        f"{result.stdout}\n{result.stderr}"
    )

    assert revisions == [init_db.EXPECTED_ALEMBIC_HEAD]


def test_alembic_revision_parser_ignores_info_lines_and_head_marker():
    current_checker = _load_current_checker_module()

    output = "\n".join(
        [
            "INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.",
            "INFO  [alembic.runtime.migration] Will assume transactional DDL.",
            "20260530_0001 (head)",
        ]
    )

    assert current_checker.parse_alembic_revisions(output) == ["20260530_0001"]


def test_alembic_current_checker_accepts_current_matching_heads():
    current_checker = _load_current_checker_module()

    current_output = "\n".join(
        [
            "INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.",
            "20260530_0001 (head)",
        ]
    )
    heads_output = "20260530_0001 (head)"

    assert current_checker.alembic_current_matches_heads(current_output, heads_output)


def test_alembic_current_checker_rejects_stale_current_revision():
    current_checker = _load_current_checker_module()

    assert not current_checker.alembic_current_matches_heads(
        "20260522_0001",
        "20260530_0001 (head)",
    )


def test_runtime_init_module_has_no_schema_mutation_calls():
    source = (BACKEND_ROOT / "app" / "db" / "init_db.py").read_text(encoding="utf-8")

    assert "create_all" not in source
    assert "CREATE EXTENSION" not in source
    assert "ALTER TABLE" not in source


def test_runtime_init_does_not_call_create_all(monkeypatch):
    from app.db import init_db

    test_engine = create_engine("sqlite+pysqlite:///:memory:")

    def fail_create_all(*args, **kwargs):
        raise AssertionError("runtime init must not create tables")

    monkeypatch.setattr(init_db, "engine", test_engine)
    monkeypatch.setattr(init_db.Base.metadata, "create_all", fail_create_all)

    with pytest.raises(init_db.RuntimeSchemaError, match="Run alembic upgrade head"):
        init_db.init_db()


def test_runtime_init_fails_clearly_for_missing_schema(monkeypatch):
    from app.db import init_db

    test_engine = create_engine("sqlite+pysqlite:///:memory:")
    monkeypatch.setattr(init_db, "engine", test_engine)

    with pytest.raises(init_db.RuntimeSchemaError) as exc:
        init_db.init_db()

    assert "Database schema is not initialized" in str(exc.value)
    assert "Run alembic upgrade head" in str(exc.value)
    assert "analysis_jobs" in str(exc.value)
    assert inspect(test_engine).get_table_names() == []


def test_runtime_schema_check_passes_for_alembic_head_schema(monkeypatch):
    from app.db import init_db

    monkeypatch.setattr(init_db, "engine", _sqlite_engine_with_runtime_schema())

    init_db.check_runtime_schema()


def test_runtime_schema_check_requires_alembic_version(monkeypatch):
    from app.db import init_db

    monkeypatch.setattr(
        init_db,
        "engine",
        _sqlite_engine_with_runtime_schema(include_alembic=False),
    )

    with pytest.raises(init_db.RuntimeSchemaError, match="Missing alembic_version table"):
        init_db.check_runtime_schema()


def test_runtime_schema_check_reports_wrong_alembic_version(monkeypatch):
    from app.db import init_db

    monkeypatch.setattr(
        init_db,
        "engine",
        _sqlite_engine_with_runtime_schema(alembic_version="wrong_revision"),
    )

    with pytest.raises(init_db.RuntimeSchemaError) as exc:
        init_db.check_runtime_schema()

    assert "Database schema is not at Alembic head" in str(exc.value)
    assert f"Expected {init_db.EXPECTED_ALEMBIC_HEAD}, found wrong_revision" in str(exc.value)


def test_access_token_hash_is_not_silently_added_at_runtime(monkeypatch):
    from app.db import init_db

    test_engine = _sqlite_engine_with_runtime_schema(
        omit_columns={"analysis_jobs": {"access_token_hash"}}
    )
    monkeypatch.setattr(
        init_db,
        "engine",
        test_engine,
    )

    with pytest.raises(init_db.RuntimeSchemaError) as exc:
        init_db.init_db()

    assert "analysis_jobs.access_token_hash" in str(exc.value)
    column_names = {
        column["name"] for column in inspect(test_engine).get_columns("analysis_jobs")
    }
    assert "access_token_hash" not in column_names
