from __future__ import annotations

from sicav_checker.core.logging import log_stage
from sicav_checker.domain.models import FinancialDocument, ValidationResult
from sicav_checker.exceptions import ValidationError
from sicav_checker.rules.rule_engine import RuleEngine
from sicav_checker.validation.internal_validator import validate_document


class ValidationService:
    """Runs deterministic accounting validations against canonical documents."""

    def __init__(self, rule_engine: RuleEngine | None = None) -> None:
        self.rule_engine = rule_engine or RuleEngine()

    def validate_document(self, document: FinancialDocument) -> list[ValidationResult]:
        with log_stage("validate_document", year=document.document_year):
            try:
                results = self.rule_engine.validate_document(document)
                return results or validate_document(document)
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc

    def validate_documents(self, documents: list[FinancialDocument]) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        for document in documents:
            results.extend(self.validate_document(document))
        return results