from __future__ import annotations

from sicav_checker.core.logging import log_stage
from sicav_checker.domain.models import FinancialDocument, ValidationResult
from sicav_checker.exceptions import ValidationError
from sicav_checker.validation.internal_validator import validate_document


class ValidationService:
    """Runs deterministic accounting validations against canonical documents."""

    def validate_document(self, document: FinancialDocument) -> list[ValidationResult]:
        with log_stage("validate_document", year=document.document_year):
            try:
                return validate_document(document)
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc

    def validate_documents(self, documents: list[FinancialDocument]) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        for document in documents:
            results.extend(self.validate_document(document))
        return results