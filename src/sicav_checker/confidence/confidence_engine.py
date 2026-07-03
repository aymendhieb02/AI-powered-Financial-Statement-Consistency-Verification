from __future__ import annotations

from statistics import mean

from sicav_checker.models import ComparisonResult, ConfidenceReport, FinancialDocument, RuleResult, ValidationResult


def _avg(values: list[float], default: float = 1.0) -> float:
    return mean(values) if values else default


class ConfidenceEngine:
    def aggregate(self, documents: list[FinancialDocument], comparisons: list[ComparisonResult], validations: list[ValidationResult], rule_results: list[RuleResult] | None = None) -> ConfidenceReport:
        extraction = _avg([row.confidence for doc in documents for statement in doc.statements.values() for row in statement.rows])
        normalization = _avg([row.match.confidence for doc in documents for statement in doc.statements.values() for row in statement.rows if row.match])
        comparison = _avg([item.confidence for item in comparisons])
        rules = _avg([item.confidence for item in (rule_results or [])] or [item.confidence for item in validations])
        overall = _avg([extraction, normalization, comparison, rules])
        return ConfidenceReport(extraction=extraction, normalization=normalization, comparison=comparison, rules=rules, overall=overall)
