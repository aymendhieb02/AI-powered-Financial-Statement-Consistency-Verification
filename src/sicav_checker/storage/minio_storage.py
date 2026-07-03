from __future__ import annotations

from io import BytesIO

try:
    from loguru import logger
except ImportError:
    class _Logger:
        def warning(self, message: str, *args: object) -> None:
            print("WARNING: " + message.format(*args))
    logger = _Logger()

from sicav_checker.config import settings
from sicav_checker.storage.local_storage import LocalStorageAdapter
from sicav_checker.storage.storage_adapter import StorageAdapter


class MinioStorageAdapter(StorageAdapter):
    def __init__(self) -> None:
        try:
            from minio import Minio

            self.client = Minio(
                settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure,
            )
            self.bucket = settings.minio_bucket
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
            self.fallback: LocalStorageAdapter | None = None
        except Exception as exc:
            logger.warning("MinIO unavailable, falling back to local storage: {}", exc)
            self.client = None
            self.bucket = settings.minio_bucket
            self.fallback = LocalStorageAdapter(".")

    def save_bytes(self, key: str, data: bytes) -> None:
        if self.fallback:
            self.fallback.save_bytes(key, data)
            return
        self.client.put_object(self.bucket, self.normalize_key(key), BytesIO(data), len(data))

    def load_bytes(self, key: str) -> bytes:
        if self.fallback:
            return self.fallback.load_bytes(key)
        response = self.client.get_object(self.bucket, self.normalize_key(key))
        return response.read()

    def exists(self, key: str) -> bool:
        if self.fallback:
            return self.fallback.exists(key)
        try:
            self.client.stat_object(self.bucket, self.normalize_key(key))
            return True
        except Exception:
            return False