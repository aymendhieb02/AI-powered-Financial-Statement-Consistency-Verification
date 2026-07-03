from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from sicav_checker.domain.models import ComparisonReport
from sicav_checker.reporting.excel_report import write_excel_report
from sicav_checker.reporting.json_report import write_json_report


class ReportGenerator(ABC):
    """Base interface for accountant-facing report generators."""

    @abstractmethod
    def generate(self, report: ComparisonReport, output_dir: Path) -> Path:
        raise NotImplementedError


class ExcelGenerator(ReportGenerator):
    def __init__(self, filename: str = "maxula_consistency_report.xlsx") -> None:
        self.filename = filename

    def generate(self, report: ComparisonReport, output_dir: Path) -> Path:
        return write_excel_report(output_dir / self.filename, report.documents, report.comparisons, report.validations, report.missing_years)


class JsonGenerator(ReportGenerator):
    def __init__(self, filename: str = "maxula_consistency_report.json") -> None:
        self.filename = filename

    def generate(self, report: ComparisonReport, output_dir: Path) -> Path:
        return write_json_report(output_dir / self.filename, report.documents, report.comparisons, report.validations, report.missing_years)