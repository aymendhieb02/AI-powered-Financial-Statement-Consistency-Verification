from __future__ import annotations

from pathlib import Path

from sicav_checker.models import FinancialDocument, RuleResult, Severity, Status, ValidationResult
from sicav_checker.rules.rule_executor import RuleExecutor
from sicav_checker.rules.rule_loader import RuleLoader
from sicav_checker.rules.rule_registry import AccountingRule, RuleRegistry


class RuleEngine:
    def __init__(self, loader: RuleLoader | None = None, executor: RuleExecutor | None = None) -> None:
        self.loader = loader or RuleLoader(Path("config/rules"))
        self.executor = executor or RuleExecutor()
        self.registry = RuleRegistry()
        self.mandatory_fields: list[str] = []
        self.reload()

    def reload(self) -> None:
        data = self.loader.load()
        self.registry = RuleRegistry()
        self.mandatory_fields = data.get("mandatory_fields", [])
        for item in data.get("rules", []):
            self.registry.register(AccountingRule(**item))

    def list_rules(self) -> list[AccountingRule]:
        return self.registry.all()

    def execute(self, document: FinancialDocument) -> list[RuleResult]:
        results = [self.executor.execute(rule, document) for rule in self.registry.all()]
        for field in self.mandatory_fields:
            found = any(field == row.canonical_label for statement in document.statements.values() for row in statement.rows)
            results.append(RuleResult(rule_id=f"MANDATORY_{field}", rule_name=f"Mandatory field {field}", status=Status.OK if found else Status.MISSING_IN_NEW, severity=Severity.CRITICAL, expected="present", actual="present" if found else "missing", statement="mandatory_fields", message=f"{field} must be present"))
        return results

    def validate_document(self, document: FinancialDocument) -> list[ValidationResult]:
        validations: list[ValidationResult] = []
        for result in self.execute(document):
            validations.append(ValidationResult(document_year=document.document_year or 0, statement=result.statement, rule=result.rule_name, status=result.status, severity=result.severity, expected=result.expected if isinstance(result.expected, (int, float)) else None, actual=result.actual if isinstance(result.actual, (int, float)) else None, note=result.message, rule_id=result.rule_id, rule_name=result.rule_name, confidence=result.confidence, execution_time=result.execution_time, page=result.page))
        return validations
