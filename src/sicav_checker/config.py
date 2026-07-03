from __future__ import annotations

from pathlib import Path
from typing import Literal

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    from pydantic import BaseModel as BaseSettings
    SettingsConfigDict = dict

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> None:
        return None


load_dotenv()


class Settings(BaseSettings):
    """Application configuration shared by CLI and future API/UI clients."""

    app_name: str = "FinVerify"
    environment: Literal["development", "testing", "production"] = "development"
    project_root: Path = Path.cwd()
    data_dir: Path = Path("data")
    raw_pdfs_dir: Path = Path("data/raw_pdfs")
    extracted_json_dir: Path = Path("data/extracted_json")
    reports_dir: Path = Path("data/reports")

    storage_backend: str = "local"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "sicav-documents"
    minio_secure: bool = False

    ollama_model: str = "qwen2.5-coder:7b"
    fuzzy_match_threshold: int = 88
    comparison_tolerance: float = 0.001

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def resolve(self, path: Path) -> Path:
        return path if path.is_absolute() else self.project_root / path


settings = Settings()