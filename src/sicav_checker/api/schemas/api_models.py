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


class EvidenceReferenceModel(BaseModel):
    document_id: str | None = None
    source_pdf: str | None = None
    file_name: str | None = None
    page: int | None = None
    page_number: int | None = None
    statement_name: str | None = None
    statement: str | None = None
    section_name: str | None = None
    section: str | None = None
    raw_text: str | None = None
    raw_line: str | None = None
    normalized_line: str | None = None
    label_text: str | None = None
    value_text_current: str | None = None
    value_text_previous: str | None = None
    current_raw: str | None = None
    previous_raw: str | None = None
    current_value: float | int | None = None
    previous_value: float | int | None = None
    value: float | int | None = None
    value_used: float | int | None = None
    value_role: str | None = None
    bounding_box: list[float] | None = None
    bbox_label: list[float] | None = None
    bbox_current: list[float] | None = None
    bbox_previous: list[float] | None = None
    bbox_row: list[float] | None = None
    bbox_value: list[float] | None = None
    extraction_method: str | None = None
    extraction_engine: str | None = None
    confidence: float | None = None


class ComparisonEvidenceModel(BaseModel):
    id: str
    pair: str = ""
    year: int | None = None
    statement: str = ""
    statement_name: str = ""
    page: int | None = None
    section: str | None = None
    canonical_label: str
    hierarchy_path: str | None = None
    status: str
    severity: str
    old_label: str | None = None
    new_label: str | None = None
    account_label_old: str | None = None
    account_label_new: str | None = None
    old_value: float | int | None = None
    new_value: float | int | None = None
    old_current_value: float | int | None = None
    new_previous_value: float | int | None = None
    expected_value: float | int | None = None
    actual_value: float | int | None = None
    difference: float | int | None = None
    difference_percent: float | None = None
    confidence: float = 0
    old_page: int | None = None
    new_page: int | None = None
    old_section: str | None = None
    new_section: str | None = None
    old_raw_line: str | None = None
    new_raw_line: str | None = None
    old_bbox: list[float] | None = None
    new_bbox: list[float] | None = None
    explanation: str = ""
    technical_reason: str = ""
    accountant_reason: str = ""
    recommended_action: str = ""
    reason: str = ""
    issue_type: str = "ok"
    evidence_type: str | None = None
    issue_classification: str | None = None
    status_group: str | None = None
    old_document_id: str | None = None
    new_document_id: str | None = None
    old_evidence: EvidenceReferenceModel | dict | str | None = None
    new_evidence: EvidenceReferenceModel | dict | str | None = None
    duplicate_candidates: list[EvidenceReferenceModel | dict] = Field(default_factory=list)


class EvidenceListResponse(BaseModel):
    items: list[ComparisonEvidenceModel] = Field(default_factory=list)
    total: int = 0


class DocumentPageResponse(BaseModel):
    document_id: str
    page_number: int
    source_file: str
    file_url: str
    image_url: str | None = None
    page_width: float | None = None
    page_height: float | None = None
    statement: str | None = None
    section: str | None = None
    raw_line: str | None = None
    bounding_box: list[float] | None = None


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
    merged_rows: int = 0
    hierarchy_gaps: int = 0
    low_confidence_parse: int = 0
    critical_accounting_errors: int = 0
    carry_forward_ok: int = 0
    carry_forward_mismatch: int = 0
    extraction_confidence: float = 0
    accounting_health: dict = Field(default_factory=dict)
    extraction_status: str = "FAILED"
    extraction_reason: str = ""
    extraction_summary: dict = Field(default_factory=dict)
    comparison_status: str = "FAILED"
    comparison_reason: str = ""
    comparison_summary: dict = Field(default_factory=dict)
    accounting_status: str = "UNKNOWN"
    accounting_reason: str = ""
    accounting_summary: dict = Field(default_factory=dict)
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
