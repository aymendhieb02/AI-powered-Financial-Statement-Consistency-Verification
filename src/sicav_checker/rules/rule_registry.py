from __future__ import annotations

from pydantic import BaseModel

from sicav_checker.models import Severity


class AccountingRule(BaseModel):
    id: str
    name: str
    category: str = "General"
    severity: Severity = Severity.MEDIUM
    statement: str
    expression: str
    message: str = ""


class RuleRegistry:
    def __init__(self) -> None:
        self._rules: dict[str, AccountingRule] = {}

    def register(self, rule: AccountingRule) -> None:
        self._rules[rule.id] = rule

    def all(self) -> list[AccountingRule]:
        return list(self._rules.values())

    def get(self, rule_id: str) -> AccountingRule | None:
        return self._rules.get(rule_id)
