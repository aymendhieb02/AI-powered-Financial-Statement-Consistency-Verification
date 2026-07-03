from __future__ import annotations

from sicav_checker.comparison.cross_year_comparator import compare_documents
from sicav_checker.comparison.pair_builder import build_valid_pairs
from sicav_checker.core.logging import log_stage
from sicav_checker.domain.models import ComparisonResult, FinancialDocument
from sicav_checker.exceptions import ComparisonError


class ComparisonService:
    """Compares consecutive canonical FinancialDocument objects."""

    def __init__(self, tolerance: float = 0.001) -> None:
        self.tolerance = tolerance

    def compare_pair(self, old_document: FinancialDocument, new_document: FinancialDocument) -> list[ComparisonResult]:
        with log_stage("compare_pair", old_year=old_document.document_year, new_year=new_document.document_year):
            try:
                return compare_documents(old_document, new_document, tolerance=self.tolerance)
            except ValueError as exc:
                raise ComparisonError(str(exc)) from exc

    def compare_documents(self, documents: list[FinancialDocument]) -> list[ComparisonResult]:
        docs_by_year = {document.document_year: document for document in documents if document.document_year is not None}
        results: list[ComparisonResult] = []
        with log_stage("compare_documents", document_count=len(documents)):
            for old_year, new_year in build_valid_pairs(list(docs_by_year)):
                results.extend(self.compare_pair(docs_by_year[old_year], docs_by_year[new_year]))
        return results