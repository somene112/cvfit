from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Iterator


class StorageError(RuntimeError):
    pass


class StorageNotFoundError(StorageError):
    pass


class UploadValidationError(StorageError):
    def __init__(self, message: str, code: str = "CV_UPLOAD_INVALID"):
        super().__init__(message)
        self.code = code


class StorageService(ABC):
    @abstractmethod
    def save_bytes(self, key: str, content: bytes, content_type: str | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
    def read_bytes(self, location: str) -> bytes:
        raise NotImplementedError

    @contextmanager
    @abstractmethod
    def local_path(self, location: str) -> Iterator[str]:
        raise NotImplementedError

    def presigned_url(self, location: str, expires_in: int = 300) -> str | None:
        return None
