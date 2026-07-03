from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sicav_checker.config import Settings, settings
from sicav_checker.core.logging import log_stage
from sicav_checker.domain.models import ComparisonReport, ComparisonResult, FinancialDocument, ValidationResult
from sicav_checker.services.comparison_service import ComparisonService
from sicav_checker.services.extraction_service import ExtractionService
from sicav_checker.services.normalization_service import NormalizationService
from sicav_checker.services.reporting_service import ReportingService
from sicav_checker.services.storage_service import StorageService
from sicav_checker.services.validation_service import ValidationService


@dataclass(slots=True)
class PipelineResult:
    documents: list[FinancialDocument]
    comparisons: list[ComparisonResult]
    validations: list[ValidationResult]
    missing_years: list[int]
    report_paths: list[Path]

    @property
    def report(self) -> ComparisonReport:
        return ComparisonReport(
            documents=self.documents,
            comparisons=self.comparisons,
            validations=self.validations,
            missing_years=self.missing_years,
        )


class PipelineOrchestrator:
    """Coordinates the FinVerify application pipeline across services."""

    def __init__(
        self,
        extraction_service: ExtractionService | None = None,
        normalization_service: NormalizationService | None = None,
        validation_service: ValidationService | None = None,
        comparison_service: ComparisonService | None = None,
        reporting_service: ReportingService | None = None,
        storage_service: StorageService | None = None,
        app_settings: Settings = settings,
    ) -> None:
        self.settings = app_settings
        self.extraction_service = extraction_service or ExtractionService()
        self.normalization_service = normalization_service or NormalizationService()
        self.validation_service = validation_service or ValidationService()
        self.comparison_service = comparison_service or ComparisonService(tolerance=app_settings.comparison_tolerance)
        self.reporting_service = reporting_service or ReportingService()
        self.storage_service = storage_service or StorageService(
            extracted_dir=app_settings.resolve(app_settings.extracted_json_dir),
            backend=app_settings.storage_backend,
        )

    def extract(self, raw_dir: Path) -> list[FinancialDocument]:
        with log_stage("pipeline_extract", raw_dir=str(raw_dir)):
            documents = self.extraction_service.extract_directory(raw_dir)
            normalized = self.normalization_service.normalize_documents(documents)
            self.storage_service.save_documents(normalized)
            return normalized

    def compare(self) -> tuple[list[FinancialDocument], list[ComparisonResult], list[ValidationResult], list[int]]:
        with log_stage("pipeline_compare"):
            documents = self.storage_service.load_documents()
            validations = self.validation_service.validate_documents(documents)
            comparisons = self.comparison_service.compare_documents(documents)
            missing_years = self._missing_years([document.document_year for document in documents if document.document_year is not None])
            return documents, comparisons, validations, missing_years

    def report(self, reports_dir: Path | None = None) -> PipelineResult:
        with log_stage("pipeline_report"):
            documents, comparisons, validations, missing_years = self.compare()
            comparison_report = ComparisonReport(
                documents=documents,
                comparisons=comparisons,
                validations=validations,
                missing_years=missing_years,
            )
            output_dir = reports_dir or self.settings.resolve(self.settings.reports_dir)
            report_paths = self.reporting_service.generate(comparison_report, output_dir)
            return PipelineResult(documents, comparisons, validations, missing_years, report_paths)

    def run_all(self, raw_dir: Path, reports_dir: Path | None = None) -> PipelineResult:
        with log_stage("pipeline_all", raw_dir=str(raw_dir)):
            self.extract(raw_dir)
            return self.report(reports_dir=reports_dir)

    @staticmethod
    def _missing_years(years: list[int]) -> list[int]:
        if not years:
            return []
        available = set(years)
        return [year for year in range(min(years), max(years) + 1) if year not in available]