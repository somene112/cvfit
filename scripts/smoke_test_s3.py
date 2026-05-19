from __future__ import annotations

import os
import sys

from smoke_test_local import main as run_smoke


def _configured_value(name: str) -> str:
    return os.environ.get(name, "").strip()


def main() -> int:
    bucket = _configured_value("S3_BUCKET")
    prefix = _configured_value("S3_PREFIX").strip("/")
    backend = _configured_value("STORAGE_BACKEND") or "unknown"

    if backend.lower() != "s3":
        print(
            "warning: local script environment STORAGE_BACKEND is not s3; "
            "the running API/worker must be started with docker-compose.s3.yml"
        )
    if bucket:
        target = f"{bucket}/{prefix}" if prefix else bucket
        print(f"s3 smoke target prefix={target}")
    else:
        print("s3 smoke target prefix is not set in this shell; relying on API/worker environment")

    result = run_smoke()
    if result == 0:
        print("s3 smoke test passed")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
