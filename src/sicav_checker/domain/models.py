from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator


class Status(str, Enum):
    OK = "OK"
    MISMATCH = "MISMATCH"
    MISSING_IN_OLD = "MISSING_IN_OLD"
    MISSING_IN_NEW = "MISSING_IN_NEW"
    LABEL_RENAMED = "LABEL_RENAMED"
    LOW_CONFIDENCE_EXTRACTION = "LOW_CONFIDENCE_EXTRACTION"
    CARRY_FORWARD_OK = "carry_forward_ok"
    CARRY_FORWARD_MISMATCH = "carry_forward_mismatch"
    MISSING_IN_NEW_COMPARATIVE = "missing_in_new_comparative"
    MISSING_IN_OLD_CURRENT = "missing_in_old_current"
    ADDED_ACCOUNT = "added_account"
    REMOVED_ACCOUNT = "removed_account"
    DUPLICATE_LABEL = "duplicate_label"
    PARSE_LOW_CONFIDENCE = "parse_low_confidence"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskScore(BaseModel):
    level: RiskLevel = RiskLevel.LOW
    score: float = Field(default=0.0, ge=0.0, le=100.0)
    rationale: str = ""


class DocumentMetadata(BaseModel):
    company: str = "MAXULA PLACEMENT SICAV"
    year: int
    source_file: str = ""
    auditor: str | None = None
    pages: list[int] = Field(default_factory=list)
    extraction_method: str = "unknown"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class Evidence(BaseModel):
    line_id: str = ""
    document_id: str = ""
    source_pdf: str = ""
    page: int | None = None
    statement_name: str | None = None
    section_name: str | None = None
    bounding_box: tuple[float, float, float, float] | None = None
    bbox_label: tuple[float, float, float, float] | None = None
    bbox_current: tuple[float, float, float, float] | None = None
    bbox_previous: tuple[float, float, float, float] | None = None
    bbox_row: tuple[float, float, float, float] | None = None
    table_id: str | None = None
    row_number: int | None = None
    column: str | None = None
    extraction_method: str = "unknown"
    raw_text: str = ""
    normalized_line: str = ""
    label_text: str = ""
    value_text_current: str | None = None
    value_text_previous: str | None = None
    normalized_value: float | int | None = None
    current_value: float | int | None = None
    previous_value: float | int | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class MatchMetadata(BaseModel):
    original_label: str = ""
    canonical_label: str = ""
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    method: str = "unknown"


class FinancialLine(BaseModel):
    label: str
    canonical_label: str
    current_value: float | int | None = None
    previous_value: float | int | None = None
    page: int | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    notes: str = ""
    evidence: Evidence | None = None
    match: MatchMetadata | None = None


class StatementSection(BaseModel):
    name: str
    lines: list[FinancialLine] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class FinancialStatement(BaseModel):
    name: str
    sections: list[StatementSection] = Field(default_factory=list)
    rows: list[FinancialLine] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def sync_rows_and_sections(self) -> "FinancialStatement":
        if not self.rows and self.sections:
            self.rows = [line for section in self.sections for line in section.lines]
        if self.rows and not self.sections:
            self.sections = [StatementSection(name=self.name, lines=self.rows, confidence=self.confidence)]
        return self


class BalanceSheet(FinancialStatement):
    name: str = "bilan"
    assets: StatementSection = Field(default_factory=lambda: StatementSection(name="assets"))
    liabilities: StatementSection = Field(default_factory=lambda: StatementSection(name="liabilities"))
    equity: StatementSection = Field(default_factory=lambda: StatementSection(name="equity"))


class IncomeStatement(FinancialStatement):
    name: str = "etat_resultat"


class StatementOfNetAssetVariation(FinancialStatement):
    name: str = "etat_variation_actif_net"


class Notes(BaseModel):
    sections: list[StatementSection] = Field(default_factory=list)


class AuditReports(BaseModel):
    general_report: str | None = None
    special_report: str | None = None


class FinancialDocument(BaseModel):
    metadata: DocumentMetadata | None = None
    balance_sheet: BalanceSheet | None = None
    income_statement: IncomeStatement | None = None
    net_asset_variation: StatementOfNetAssetVariation | None = None
    notes: Notes | None = None
    audit_reports: AuditReports | None = None
    statements: dict[str, FinancialStatement] = Field(default_factory=dict)

    company: str = "MAXULA PLACEMENT SICAV"
    document_year: int | None = None
    source_file: str = ""
    extraction_method: str = "unknown"
    pages: list[int] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def sync_legacy_and_canonical_views(self) -> "FinancialDocument":
        if self.metadata is None:
            if self.document_year is None:
                raise ValueError("FinancialDocument requires metadata.year or document_year")
            self.metadata = DocumentMetadata(
                company=self.company,
                year=self.document_year,
                source_file=self.source_file,
                pages=self.pages,
                extraction_method=self.extraction_method,
                confidence=self.confidence,
            )
        self.company = self.metadata.company
        self.document_year = self.metadata.year
        self.source_file = self.metadata.source_file
        self.pages = self.metadata.pages
        self.extraction_method = self.metadata.extraction_method
        self.confidence = self.metadata.confidence

        if self.balance_sheet is None and "bilan" in self.statements:
            self.balance_sheet = BalanceSheet.model_validate(self.statements["bilan"].model_dump())
        if self.income_statement is None and "etat_resultat" in self.statements:
            self.income_statement = IncomeStatement.model_validate(self.statements["etat_resultat"].model_dump())
        if self.net_asset_variation is None and "etat_variation_actif_net" in self.statements:
            self.net_asset_variation = StatementOfNetAssetVariation.model_validate(self.statements["etat_variation_actif_net"].model_dump())

        if self.balance_sheet is not None:
            self.statements["bilan"] = self.balance_sheet
        if self.income_statement is not None:
            self.statements["etat_resultat"] = self.income_statement
        if self.net_asset_variation is not None:
            self.statements["etat_variation_actif_net"] = self.net_asset_variation
        return self

    @classmethod
    def from_path(cls, path: Path, year: int, statements: dict[str, FinancialStatement] | None = None) -> "FinancialDocument":
        return cls(
            metadata=DocumentMetadata(year=year, source_file=str(path), extraction_method="synthetic"),
            statements=statements or {},
        )


class Anomaly(BaseModel):
    status: Status
    severity: Severity
    risk_score: RiskScore = Field(default_factory=RiskScore)
    message: str = ""
    line_label: str | None = None


class ComparisonEvidence(BaseModel):
    id: str
    status: str
    severity: str
    statement_name: str
    canonical_label: str
    old_label: str | None = None
    new_label: str | None = None
    old_value: float | int | None = None
    new_value: float | int | None = None
    expected_value: float | int | None = None
    actual_value: float | int | None = None
    difference: float | int | None = None
    difference_percent: float | None = None
    old_page: int | None = None
    new_page: int | None = None
    old_section: str | None = None
    new_section: str | None = None
    old_raw_line: str | None = None
    new_raw_line: str | None = None
    old_bbox: tuple[float, float, float, float] | None = None
    new_bbox: tuple[float, float, float, float] | None = None
    explanation: str = ""
    technical_reason: str = ""
    accountant_reason: str = ""
    recommended_action: str = ""
    issue_type: str = "ok"
    old_document_id: str | None = None
    new_document_id: str | None = None
    duplicate_candidates: list[dict[str, Any]] = Field(default_factory=list)


class ComparisonResult(BaseModel):
    pair: str
    year: int
    statement: str
    old_label: str | None
    new_label: str | None
    canonical_label: str
    old_value: float | int | None
    new_value: float | int | None
    status: Status
    severity: Severity
    delta: float | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    note: str = ""
    anomaly: Anomaly | None = None
    old_evidence: Evidence | None = None
    new_evidence: Evidence | None = None
    duplicate_candidates: list[Evidence] = Field(default_factory=list)
    matching_method: str = "unknown"


class RuleResult(BaseModel):
    rule_id: str
    rule_name: str
    status: Status
    severity: Severity
    expected: float | int | str | None = None
    actual: float | int | str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    execution_time: float = 0.0
    page: int | None = None
    statement: str = ""
    message: str = ""


class ConfidenceReport(BaseModel):
    extraction: float = Field(default=1.0, ge=0.0, le=1.0)
    normalization: float = Field(default=1.0, ge=0.0, le=1.0)
    comparison: float = Field(default=1.0, ge=0.0, le=1.0)
    rules: float = Field(default=1.0, ge=0.0, le=1.0)
    overall: float = Field(default=1.0, ge=0.0, le=1.0)


class VerificationRun(BaseModel):
    run_id: str
    timestamp: str
    project: str = "default"
    documents: list[str] = Field(default_factory=list)
    versions: dict[str, str] = Field(default_factory=dict)
    settings: dict[str, Any] = Field(default_factory=dict)
    results: dict[str, Any] = Field(default_factory=dict)
    report_paths: list[str] = Field(default_factory=list)
    confidence: ConfidenceReport | None = None
    new_anomalies: list[str] = Field(default_factory=list)
    resolved_anomalies: list[str] = Field(default_factory=list)
    changed_risk_score: float | None = None
    changed_confidence: float | None = None


class ValidationResult(BaseModel):
    document_year: int
    statement: str
    rule: str
    status: Status
    severity: Severity
    expected: float | int | None = None
    actual: float | int | None = None
    delta: float | None = None
    note: str = ""
    anomaly: Anomaly | None = None
    rule_id: str | None = None
    rule_name: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    execution_time: float = 0.0
    page: int | None = None


class ReportResult(BaseModel):
    run_id: str
    report_paths: list[str] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)


class ComparisonReport(BaseModel):
    documents: list[FinancialDocument] = Field(default_factory=list)
    comparisons: list[ComparisonResult] = Field(default_factory=list)
    validations: list[ValidationResult] = Field(default_factory=list)
    missing_years: list[int] = Field(default_factory=list)
    rule_results: list[RuleResult] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    confidence: ConfidenceReport | None = None
    verification_history: list[VerificationRun] = Field(default_factory=list)

    @property
    def anomalies(self) -> list[Anomaly]:
        items: list[Anomaly] = []
        for result in [*self.comparisons, *self.validations]:
            if result.anomaly is not None:
                items.append(result.anomaly)
        return items


StatementRow = FinancialLine
Statement = FinancialStatement
ExtractedDocument = FinancialDocument
InternalValidationResult = ValidationResult


def model_dump_jsonable(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")
