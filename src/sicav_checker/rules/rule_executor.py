from __future__ import annotations

from time import perf_counter

from sicav_checker.core.logging import logger
from sicav_checker.models import FinancialDocument, RuleResult, Severity, Status
from sicav_checker.rules.rule_registry import AccountingRule


class RuleExecutor:
    def execute(self, rule: AccountingRule, document: FinancialDocument) -> RuleResult:
        start = perf_counter()
        statement = document.statements.get(rule.statement)
        values = {row.canonical_label: row.current_value for row in statement.rows} if statement else {}
        page = next((row.page for row in statement.rows if row.canonical_label in rule.expression), None) if statement else None
        status = Status.MISMATCH
        actual = None
        try:
            actual = bool(eval(rule.expression, {"__builtins__": {}}, values))
            status = Status.OK if actual else Status.MISMATCH
        except Exception as exc:
            actual = str(exc)
            status = Status.MISMATCH
        duration = perf_counter() - start
        logger.info("Rule executed id={} status={} duration={:.4f}s", rule.id, status, duration)
        return RuleResult(
            rule_id=rule.id,
            rule_name=rule.name,
            status=status,
            severity=rule.severity if isinstance(rule.severity, Severity) else Severity(str(rule.severity)),
            expected=True,
            actual=actual,
            confidence=1.0 if status == Status.OK else 0.8,
            execution_time=duration,
            page=page,
            statement=rule.statement,
            message=rule.message,
        )
