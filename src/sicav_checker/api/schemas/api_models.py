from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    storage_backend: str


class ProjectCreate(BaseModel):
    name: str
    company: str
    description: str = ""


class ProjectResponse(BaseModel):
    id: str
    name: str
    company: str
    description: str = ""
    created_at: str


class UploadedDocument(BaseModel):
    filename: str
    size: int
    detected_year: int | None = None
    status: str
    path: str


class UploadResponse(BaseModel):
    uploaded: list[UploadedDocument] = Field(default_factory=list)
    failed: list[dict] = Field(default_factory=list)


class VerificationRunResponse(BaseModel):
    run_id: str
    status: str


class VerificationSummary(BaseModel):
    run_id: str
    status: str
    documents_analyzed: int = 0
    pairs_checked: int = 0
    values_checked: int = 0
    ok_count: int = 0
    mismatch_count: int = 0
    missing_count: int = 0
    critical_anomalies: int = 0
    medium_anomalies: int = 0
    low_anomalies: int = 0
    risk_score: float = 0
    report_paths: list[str] = Field(default_factory=list)


class PaginatedAnomalies(BaseModel):
    items: list[dict]
    total: int
    page: int
    page_size: int


class SettingsResponse(BaseModel):
    storage_backend: str
    ai_enabled: bool
    ollama_model: str
    minio_configured: bool