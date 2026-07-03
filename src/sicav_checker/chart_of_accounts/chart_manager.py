from __future__ import annotations

from sicav_checker.chart_of_accounts.canonical_mapper import CanonicalMapper
from sicav_checker.models import FinancialDocument


class ChartManager:
    def __init__(self, mapper: CanonicalMapper | None = None) -> None:
        self.mapper = mapper or CanonicalMapper()

    def apply(self, document: FinancialDocument) -> FinancialDocument:
        for statement in document.statements.values():
            existing = [row.canonical_label for row in statement.rows]
            for row in statement.rows:
                match = self.mapper.map_label(row.label, existing)
                row.canonical_label = match.canonical_label
                row.match = match
        return document
