from __future__ import annotations

from pathlib import Path
from typing import Protocol

from sicav_checker.domain.models import ComparisonReport, ComparisonResult, FinancialDocument, ValidationResult


class ExtractionPort(Protocol):
    def extract_pdf(self, path: Path) -> FinancialDocument:
        ...

    def extract_directory(self, raw_dir: Path) -> list[FinancialDocument]:
        ...


class NormalizationPort(Protocol):
    def normalize_document(self, document: FinancialDocument) -> FinancialDocument:
        ...


class ValidationPort(Protocol):
    def validate_documents(self, documents: list[FinancialDocument]) -> list[ValidationResult]:
        ...


class ComparisonPort(Protocol):
    def compare_documents(self, documents: list[FinancialDocument]) -> list[ComparisonResult]:
        ...


class ReportingPort(Protocol):
    def generate(self, report: ComparisonReport, reports_dir: Path) -> list[Path]:
        ...


class StoragePort(Protocol):
    def save_document(self, document: FinancialDocument, key: str | None = None) -> Path | None:
        ...

    def load_documents(self) -> list[FinancialDocument]:
        ...