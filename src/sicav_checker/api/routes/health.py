from __future__ import annotations

from fastapi import APIRouter

from sicav_checker import __version__
from sicav_checker.api.schemas.api_models import HealthResponse, SettingsResponse
from sicav_checker.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", app=settings.app_name, version=__version__, storage_backend=settings.storage_backend)


@router.get("/settings", response_model=SettingsResponse)
def api_settings() -> SettingsResponse:
    minio_configured = bool(settings.minio_endpoint and settings.minio_bucket)
    return SettingsResponse(
        storage_backend=settings.storage_backend,
        ai_enabled=True,
        ollama_model=settings.ollama_model,
        minio_configured=minio_configured,
    )