from __future__ import annotations

from dataclasses import dataclass
import os
import sys
import warnings

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import SAWarning


REQUIRED_SCHEMA = {
    "users": {
        "id",
        "email",
        "password_hash",
        "full_name",
        "is_active",
        "created_at",
        "updated_at",
    },
    "cv_files": {
        "id",
        "original_filename",
        "mime_type",
        "storage_path",
        "sha256",
        "created_at",
    },
    "jd_docs": {"id", "jd_text", "role", "created_at"},
    "analysis_jobs": {
        "id",
        "cv_file_id",
        "jd_id",
        "user_id",
        "status",
        "progress",
        "error_message",
        "result_json",
        "report_docx_path",
        "access_token_hash",
        "created_at",
        "updated_at",
    },
    "text_embeddings": {
        "id",
        "owner_type",
        "owner_id",
        "text",
        "embedding",
        "meta_json",
        "created_at",
    },
}


@dataclass(frozen=True)
class SchemaCheckResult:
    required_tables: dict[str, set[str]]
    existing_tables: set[str]
    missing_items: list[str]
    alembic_versions: list[str]
    vector_extension_exists: bool | None
    dialect: str | None

    @property
    def baseline_matches(self) -> bool:
        return not self.missing_items

    @property
    def alembic_version_exists(self) -> bool:
        return "alembic_version" in self.existing_tables

    @property
    def app_tables_present(self) -> set[str]:
        return set(self.required_tables) & self.existing_tables

    @property
    def app_tables_missing(self) -> set[str]:
        return set(self.required_tables) - self.existing_tables

    @property
    def appears_empty(self) -> bool:
        return not self.app_tables_present and not self.alembic_version_exists


def _print_status(label: str, ok: bool, detail: str = "") -> None:
    status = "ok" if ok else "missing"
    suffix = f": {detail}" if detail else ""
    print(f"{label}: {status}{suffix}")


def check_schema(database_url: str) -> SchemaCheckResult:
    warnings.filterwarnings(
        "ignore",
        message="Did not recognize type 'vector'.*",
        category=SAWarning,
    )

    engine = create_engine(database_url, future=True)
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names(schema="public"))

    missing_items: list[str] = []
    for table, required_columns in REQUIRED_SCHEMA.items():
        if table not in existing_tables:
            missing_items.append(table)
            continue

        existing_columns = {column["name"] for column in inspector.get_columns(table)}
        missing_columns = sorted(required_columns - existing_columns)
        missing_items.extend(f"{table}.{column}" for column in missing_columns)

    alembic_versions: list[str] = []
    vector_extension_exists: bool | None = None
    dialect: str | None = None

    with engine.connect() as connection:
        dialect = connection.dialect.name
        if "alembic_version" in existing_tables:
            alembic_versions = [
                str(row[0])
                for row in connection.execute(text("SELECT version_num FROM alembic_version"))
            ]

        if dialect == "postgresql":
            vector_extension_exists = (
                connection.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")).scalar()
                is not None
            )
            if not vector_extension_exists:
                missing_items.append("vector extension")

    return SchemaCheckResult(
        required_tables=REQUIRED_SCHEMA,
        existing_tables=existing_tables,
        missing_items=missing_items,
        alembic_versions=alembic_versions,
        vector_extension_exists=vector_extension_exists,
        dialect=dialect,
    )


def print_schema_result(result: SchemaCheckResult) -> None:
    for table, required_columns in result.required_tables.items():
        if table not in result.existing_tables:
            _print_status(table, False)
            continue

        missing_columns = sorted(
            item.split(".", 1)[1]
            for item in result.missing_items
            if item.startswith(f"{table}.")
        )
        if missing_columns:
            _print_status(table, False, ", ".join(missing_columns))
        else:
            _print_status(table, True)

    _print_status("alembic_version table", result.alembic_version_exists)

    if result.vector_extension_exists is None:
        print(f"vector extension: skipped for {result.dialect}")
    else:
        _print_status("vector extension", result.vector_extension_exists)


def main() -> int:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is required; value was not printed.", file=sys.stderr)
        return 2

    try:
        result = check_schema(database_url)

    except SQLAlchemyError as exc:
        print(f"schema check failed: {exc.__class__.__name__}", file=sys.stderr)
        return 2

    print_schema_result(result)
    if result.missing_items:
        print("baseline schema check failed")
        return 1

    print("baseline schema check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
