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


class ProjectDetailResponse(ProjectResponse):
    document_count: int = 0
    latest_run_id: str | None = None
    latest_run_status: str | None = None
    latest_risk_score: float | None = None
    latest_confidence: float | None = None
    updated_at: str | None = None


class VerificationRunRequest(BaseModel):
    old_document_id: str | None = None
    new_document_id: str | None = None


class VerificationRunListItem(BaseModel):
    run_id: str
    status: str
    created_at: str
    summary: dict = Field(default_factory=dict)


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
    company: str = ""
    old_document_year: int | None = None
    new_document_year: int | None = None
    compared_year: int | None = None
    overall_confidence: float = 0
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
    old_extracted_lines: int = 0
    new_extracted_lines: int = 0
    comparable_lines: int = 0
    matched_lines: int = 0
    mismatched_lines: int = 0
    missing_in_old: int = 0
    missing_in_new: int = 0
    ignored_lines: int = 0
    comparison_coverage_percentage: float = 0
    financial_consistency: float = 0
    financial_consistency_numerator: int = 0
    financial_consistency_denominator: int = 0
    extraction_coverage: float = 0
    extraction_coverage_numerator: int = 0
    extraction_coverage_denominator: int = 0
    structural_quality: float = 0
    actual_mismatches: int = 0
    missing_in_old_current: int = 0
    missing_in_new_comparative: int = 0
    duplicate_labels: int = 0
    polluted_labels: int = 0
    low_confidence_parse: int = 0
    critical_accounting_errors: int = 0
    carry_forward_ok: int = 0
    carry_forward_mismatch: int = 0
    risk_level: str = "LOW"
    risk_category: str = "LOW"
    risk_rationale: str = ""
    verdict: str = "PASS"
    verdict_reason: str = ""
    why_verdict: dict = Field(default_factory=dict)
    metric_debug: dict = Field(default_factory=dict)


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
