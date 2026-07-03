from __future__ import annotations

from sicav_checker.core.logging import log_stage
from sicav_checker.domain.models import FinancialDocument
from sicav_checker.exceptions import NormalizationError
from sicav_checker.normalization.label_normalizer import normalize_label


class NormalizationService:
    """Normalizes extracted lines inside the canonical document boundary."""

    def normalize_document(self, document: FinancialDocument) -> FinancialDocument:
        with log_stage("normalize_document", year=document.document_year):
            try:
                for statement in document.statements.values():
                    for row in statement.rows:
                        row.canonical_label = row.canonical_label or normalize_label(row.label)
                return FinancialDocument.model_validate(document.model_dump())
            except ValueError as exc:
                raise NormalizationError(str(exc)) from exc

    def normalize_documents(self, documents: list[FinancialDocument]) -> list[FinancialDocument]:
        return [self.normalize_document(document) for document in documents]