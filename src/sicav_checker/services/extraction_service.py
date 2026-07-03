from __future__ import annotations

from pathlib import Path

from sicav_checker.core.logging import log_stage
from sicav_checker.evidence.evidence_tracker import EvidenceTracker
from sicav_checker.domain.models import FinancialDocument
from sicav_checker.exceptions import ExtractionError
from sicav_checker.extraction.pdf_loader import list_pdfs
from sicav_checker.extraction.statement_extractor import extract_document


class ExtractionService:
    """Turns PDFs into canonical FinancialDocument objects."""

    def __init__(self, evidence_tracker: EvidenceTracker | None = None) -> None:
        self.evidence_tracker = evidence_tracker or EvidenceTracker()

    def extract_pdf(self, path: Path) -> FinancialDocument:
        with log_stage("extract_pdf", file=str(path)):
            try:
                return self.evidence_tracker.attach(extract_document(path))
            except ValueError as exc:
                raise ExtractionError(str(exc)) from exc

    def extract_directory(self, raw_dir: Path) -> list[FinancialDocument]:
        with log_stage("extract_directory", raw_dir=str(raw_dir)):
            return [self.extract_pdf(path) for path in list_pdfs(raw_dir)]