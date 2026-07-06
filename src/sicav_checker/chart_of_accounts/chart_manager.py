from __future__ import annotations

from sicav_checker.chart_of_accounts.canonical_mapper import CanonicalMapper
from sicav_checker.models import FinancialDocument, MatchMetadata
from sicav_checker.normalization.label_normalizer import normalize_label


class ChartManager:
    def __init__(self, mapper: CanonicalMapper | None = None) -> None:
        self.mapper = mapper or CanonicalMapper()

    def apply(self, document: FinancialDocument) -> FinancialDocument:
        for statement_name, statement in document.statements.items():
            statement_key = normalize_label(statement_name) or statement_name
            for row in statement.rows:
                match = self.mapper.map_label(row.label)
                if match.method == "normalized":
                    fallback = self._fallback_key(statement_key, row.label)
                    match = MatchMetadata(
                        original_label=row.label,
                        canonical_label=fallback,
                        confidence=0.72,
                        method="fallback_normalized_label",
                    )
                row.canonical_label = match.canonical_label
                row.match = match
        return document

    @staticmethod
    def _fallback_key(statement_key: str, label: str) -> str:
        label_key = normalize_label(label) or "unknown_line"
        return f"{statement_key}__{label_key}"
