from __future__ import annotations

from sicav_checker.chart_of_accounts.chart_manager import ChartManager
from sicav_checker.core.logging import log_stage
from sicav_checker.domain.models import FinancialDocument
from sicav_checker.exceptions import NormalizationError


class NormalizationService:
    """Normalizes extracted lines inside the canonical document boundary."""

    def __init__(self, chart_manager: ChartManager | None = None) -> None:
        self.chart_manager = chart_manager or ChartManager()

    def normalize_document(self, document: FinancialDocument) -> FinancialDocument:
        with log_stage("normalize_document", year=document.document_year):
            try:
                return FinancialDocument.model_validate(self.chart_manager.apply(document).model_dump())
            except ValueError as exc:
                raise NormalizationError(str(exc)) from exc

    def normalize_documents(self, documents: list[FinancialDocument]) -> list[FinancialDocument]:
        return [self.normalize_document(document) for document in documents]
