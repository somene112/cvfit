from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


SECRET_NAMES = {"AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "DATABASE_URL", "REDIS_URL"}


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        raise FileNotFoundError(f"env file not found: {path}")

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            raise ValueError(f"{path}:{line_number} is not KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def merged_env(env_file: Path | None) -> dict[str, str]:
    values = dict(os.environ)
    if env_file is not None:
        file_values = load_env_file(env_file)
        values = {**file_values, **values}
    return values


def is_true(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def is_missing(values: dict[str, str], name: str) -> bool:
    return not values.get(name, "").strip()


def validate(mode: str, values: dict[str, str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    required = ["DATABASE_URL", "REDIS_URL", "STORAGE_BACKEND", "CV_MAX_UPLOAD_MB"]
    if mode in {"local", "s3", "render"}:
        required.append("STORAGE_ROOT")

    for name in required:
        if is_missing(values, name):
            errors.append(f"missing required variable: {name}")

    expected_backend = "local" if mode == "local" else "s3"
    backend = values.get("STORAGE_BACKEND", "").strip().lower()
    if backend and backend != expected_backend:
        errors.append(
            f"STORAGE_BACKEND must be {expected_backend!r} for {mode} mode "
            f"(found {backend!r})"
        )

    upload_limit = values.get("CV_MAX_UPLOAD_MB", "").strip()
    if upload_limit:
        try:
            if int(upload_limit) <= 0:
                errors.append("CV_MAX_UPLOAD_MB must be greater than 0")
        except ValueError:
            errors.append("CV_MAX_UPLOAD_MB must be an integer")

    if mode in {"s3", "render"}:
        for name in ["S3_BUCKET", "S3_REGION"]:
            if is_missing(values, name):
                errors.append(f"missing required variable for S3 storage: {name}")

        if not is_true(values.get("AWS_USE_IAM_ROLE", "false")):
            for name in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]:
                if is_missing(values, name):
                    errors.append(
                        f"missing required variable when AWS_USE_IAM_ROLE is false: {name}"
                    )

        if is_missing(values, "S3_PREFIX"):
            warnings.append("S3_PREFIX is empty; use a dedicated prefix for smoke tests")
        if is_missing(values, "S3_ENDPOINT_URL"):
            warnings.append(
                "S3_ENDPOINT_URL is empty; this is fine for AWS S3 but may fail for S3-compatible providers"
            )

    if mode == "local":
        for name in ["FRONTEND_TEMPLATES_DIR", "FRONTEND_STATIC_DIR"]:
            if is_missing(values, name):
                warnings.append(f"{name} is empty; app defaults may still be used")

    return errors, warnings


def print_present_summary(mode: str, values: dict[str, str]) -> None:
    names = [
        "DATABASE_URL",
        "REDIS_URL",
        "STORAGE_BACKEND",
        "STORAGE_ROOT",
        "S3_BUCKET",
        "S3_REGION",
        "S3_ENDPOINT_URL",
        "S3_PREFIX",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_USE_IAM_ROLE",
        "CV_MAX_UPLOAD_MB",
        "FRONTEND_TEMPLATES_DIR",
        "FRONTEND_STATIC_DIR",
    ]
    print(f"env contract mode={mode}")
    for name in names:
        status = "set" if values.get(name, "").strip() else "missing"
        if name in SECRET_NAMES and status == "set":
            status = "set (value hidden)"
        print(f"- {name}: {status}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check CV Fit environment variables without printing secret values."
    )
    parser.add_argument(
        "--mode",
        choices=["local", "s3", "render"],
        required=True,
        help="Environment contract to check.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        help="Optional .env-style file to read before applying current shell overrides.",
    )
    args = parser.parse_args()

    try:
        values = merged_env(args.env_file)
    except (FileNotFoundError, ValueError) as exc:
        print(f"env contract failed: {exc}", file=sys.stderr)
        return 1

    errors, warnings = validate(args.mode, values)
    print_present_summary(args.mode, values)

    for warning in warnings:
        print(f"warning: {warning}")
    for error in errors:
        print(f"error: {error}", file=sys.stderr)

    if errors:
        print("env contract failed", file=sys.stderr)
        return 1

    print("env contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
