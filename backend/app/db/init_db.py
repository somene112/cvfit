from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import engine, Base
from app.db import models as _models  # noqa: F401


# Runtime images currently install only app code, not the Alembic script
# directory. Update this constant whenever a new migration head is added.
EXPECTED_ALEMBIC_HEAD = "20260531_0001"


class RuntimeSchemaError(RuntimeError):
    pass


def _required_schema() -> dict[str, set[str]]:
    return {
        table.name: {column.name for column in table.columns}
        for table in Base.metadata.sorted_tables
    }


def _format_missing_schema(missing_items: list[str]) -> str:
    return (
        "Database schema is not initialized. Run alembic upgrade head. "
        f"Missing schema items: {', '.join(missing_items)}"
    )


def check_runtime_schema() -> None:
    try:
        with engine.connect() as conn:
            inspector = inspect(conn)
            table_names = set(inspector.get_table_names())
            missing_items: list[str] = []

            for table_name, required_columns in _required_schema().items():
                if table_name not in table_names:
                    missing_items.append(table_name)
                    continue

                existing_columns = {
                    column["name"] for column in inspector.get_columns(table_name)
                }
                for column_name in sorted(required_columns - existing_columns):
                    missing_items.append(f"{table_name}.{column_name}")

            if missing_items:
                raise RuntimeSchemaError(_format_missing_schema(missing_items))

            if "alembic_version" not in table_names:
                raise RuntimeSchemaError(
                    "Database schema is not at Alembic head. Run alembic upgrade head. "
                    "Missing alembic_version table."
                )

            versions = {
                row[0]
                for row in conn.execute(text("SELECT version_num FROM alembic_version"))
            }
            if EXPECTED_ALEMBIC_HEAD not in versions:
                current = ", ".join(sorted(versions)) if versions else "<none>"
                raise RuntimeSchemaError(
                    "Database schema is not at Alembic head. Run alembic upgrade head. "
                    f"Expected {EXPECTED_ALEMBIC_HEAD}, found {current}."
                )
    except RuntimeSchemaError:
        raise
    except SQLAlchemyError as exc:
        raise RuntimeSchemaError(
            "Database schema check failed. Confirm the database is reachable and run "
            "alembic upgrade head if the schema has not been initialized."
        ) from exc


def init_db() -> None:
    check_runtime_schema()
