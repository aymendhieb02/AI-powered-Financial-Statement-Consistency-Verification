from __future__ import annotations

from pathlib import Path

from sicav_checker.core.logging import log_stage
from sicav_checker.domain.models import ComparisonReport
from sicav_checker.exceptions import ReportingError
from sicav_checker.reporting.report_generator import ExcelGenerator, JsonGenerator, ReportGenerator


class ReportingService:
    """Generates reports from domain report objects."""

    def __init__(self, generators: list[ReportGenerator] | None = None) -> None:
        self.generators = generators or [ExcelGenerator(), JsonGenerator()]

    def generate(self, report: ComparisonReport, reports_dir: Path) -> list[Path]:
        with log_stage("generate_reports", reports_dir=str(reports_dir), generator_count=len(self.generators)):
            try:
                reports_dir.mkdir(parents=True, exist_ok=True)
                return [generator.generate(report, reports_dir) for generator in self.generators]
            except OSError as exc:
                raise ReportingError(str(exc)) from exc