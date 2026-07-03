from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field
import os


load_dotenv()


class Settings(BaseModel):
    project_root: Path = Field(default_factory=lambda: Path.cwd())
    storage_backend: str = Field(default_factory=lambda: os.getenv("STORAGE_BACKEND", "local"))
    minio_endpoint: str = Field(default_factory=lambda: os.getenv("MINIO_ENDPOINT", "localhost:9000"))
    minio_access_key: str = Field(default_factory=lambda: os.getenv("MINIO_ACCESS_KEY", "minioadmin"))
    minio_secret_key: str = Field(default_factory=lambda: os.getenv("MINIO_SECRET_KEY", "minioadmin"))
    minio_bucket: str = Field(default_factory=lambda: os.getenv("MINIO_BUCKET", "sicav-documents"))
    minio_secure: bool = Field(default_factory=lambda: os.getenv("MINIO_SECURE", "false").lower() == "true")
    ollama_model: str = Field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b"))


settings = Settings()
