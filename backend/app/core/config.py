from pathlib import Path

from pydantic_settings import BaseSettings


BACKEND_ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    STORAGE_BACKEND: str = "local"
    STORAGE_ROOT: str = "./data"
    CV_MAX_UPLOAD_MB: int = 10
    S3_BUCKET: str = ""
    S3_REGION: str = ""
    S3_ENDPOINT_URL: str = ""
    S3_PREFIX: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_USE_IAM_ROLE: bool = False
    FRONTEND_TEMPLATES_DIR: str = "../frontend/templates"
    FRONTEND_STATIC_DIR: str = "../frontend/static"
    JWT_SECRET_KEY: str = "insecure-local-dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    CORS_ALLOW_CREDENTIALS: bool = False
    CORS_ALLOWED_METHODS: str = "GET,POST,OPTIONS"
    CORS_ALLOWED_HEADERS: str = "Authorization,Content-Type"

    class Config:
        env_file = ("../.env", ".env")
        extra = "ignore"

settings = Settings()


def resolve_path(path_value: str) -> str:
    path = Path(path_value)
    if path.is_absolute():
        return str(path)
    return str((BACKEND_ROOT / path).resolve())


def validate_runtime_config() -> None:
    backend = (settings.STORAGE_BACKEND or "local").lower()
    if backend not in {"local", "s3"}:
        raise RuntimeError("Invalid STORAGE_BACKEND. Expected 'local' or 's3'.")

    if settings.CV_MAX_UPLOAD_MB <= 0:
        raise RuntimeError("CV_MAX_UPLOAD_MB must be greater than 0.")
    if not settings.JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY is required.")
    if not settings.JWT_ALGORITHM:
        raise RuntimeError("JWT_ALGORITHM is required.")
    if settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
        raise RuntimeError("JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be greater than 0.")
    if settings.CORS_ALLOW_CREDENTIALS and "*" in _split_csv(settings.CORS_ALLOWED_ORIGINS):
        raise RuntimeError("CORS_ALLOW_CREDENTIALS cannot be true when CORS_ALLOWED_ORIGINS contains '*'.")

    if backend == "local":
        if not settings.STORAGE_ROOT:
            raise RuntimeError("STORAGE_ROOT is required when STORAGE_BACKEND=local.")
    if not settings.FRONTEND_TEMPLATES_DIR:
        raise RuntimeError("FRONTEND_TEMPLATES_DIR is required.")
    if not settings.FRONTEND_STATIC_DIR:
        raise RuntimeError("FRONTEND_STATIC_DIR is required.")

    if backend == "local":
        return

    if not settings.S3_BUCKET:
        raise RuntimeError("S3_BUCKET is required when STORAGE_BACKEND=s3.")
    if not settings.S3_REGION:
        raise RuntimeError("S3_REGION is required when STORAGE_BACKEND=s3.")
    if not settings.AWS_USE_IAM_ROLE:
        if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
            raise RuntimeError(
                "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are required when "
                "STORAGE_BACKEND=s3 unless AWS_USE_IAM_ROLE=true."
            )


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]
