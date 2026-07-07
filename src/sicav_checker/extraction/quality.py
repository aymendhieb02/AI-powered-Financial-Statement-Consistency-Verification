from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from sicav_checker.models import ExtractedDocument
from sicav_checker.normalization.label_normalizer import normalize_label

COMPARABLE_STATEMENTS = ("bilan", "etat_resultat", "etat_variation_actif_net")
REQUIRED_TOTALS = {
    "total_actif",
    "total_passif",
    "actif_net",
    "total_passif_et_actif_net",
    "total_revenus_placements",
    "resultat_net",
    "valeur_liquidative",
    "taux_rendement",
}
POLLUTED_LABEL_FRAGMENTS = (
    "bilan_arrete",
    "etat_resultat_annee",
    "etat_variation_actif_net_annee",
    "montants_exprimes",
    "annee_202",
    "note_annee",
)


@dataclass(slots=True)
class ExtractionQualityReport:
    engine_name: str
    total_rows: int
    rows_by_statement: dict[str, int]
    required_statements_found: int
    required_totals_found: int
    parsed_number_count: int
    null_number_count: int
    numeric_population_rate: float
    polluted_label_count: int
    duplicate_label_count: int
    missing_required_statement_count: int
    arithmetic_consistency_score: float
    warnings: list[str] = field(default_factory=list)
    score: float = 0.0
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")


def score_extraction(
    document: ExtractedDocument,
    engine_name: str,
    warnings: list[str] | None = None,
) -> ExtractionQualityReport:
    rows_by_statement = {name: len(statement.rows) for name, statement in document.statements.items()}
    all_rows = [row for statement in document.statements.values() for row in statement.rows]
    total_rows = len(all_rows)
    required_statements_found = sum(1 for name in COMPARABLE_STATEMENTS if rows_by_statement.get(name, 0) > 0)
    missing_required_statement_count = len(COMPARABLE_STATEMENTS) - required_statements_found

    canonical_labels = [normalize_label(row.canonical_label or row.label) for row in all_rows]
    required_totals_found = len(REQUIRED_TOTALS.intersection(canonical_labels))
    parsed_number_count = sum(1 for row in all_rows for value in (row.current_value, row.previous_value) if value is not None)
    possible_number_count = max(total_rows * 2, 1)
    null_number_count = possible_number_count - parsed_number_count if total_rows else 0
    numeric_population_rate = parsed_number_count / possible_number_count if total_rows else 0.0
    polluted_label_count = sum(1 for row in all_rows if _is_polluted_label(row.label))
    duplicate_label_count = _duplicate_count(document)
    arithmetic_consistency_score = _arithmetic_consistency(document)

    if total_rows == 0:
        report_warnings = list(warnings or [])
        report_warnings.append("empty_extraction")
        return ExtractionQualityReport(
            engine_name=engine_name,
            total_rows=0,
            rows_by_statement=rows_by_statement,
            required_statements_found=required_statements_found,
            required_totals_found=0,
            parsed_number_count=0,
            null_number_count=0,
            numeric_population_rate=0.0,
            polluted_label_count=0,
            duplicate_label_count=0,
            missing_required_statement_count=missing_required_statement_count,
            arithmetic_consistency_score=0.0,
            warnings=report_warnings,
            score=0.0,
            confidence=0.0,
        )

    statement_score = required_statements_found / len(COMPARABLE_STATEMENTS)
    totals_score = required_totals_found / len(REQUIRED_TOTALS)
    row_scope_score = min(total_rows / 45, 1.0)
    label_quality = 1.0 - min(polluted_label_count / max(total_rows, 1), 1.0)
    duplicate_quality = 1.0 - min(duplicate_label_count / max(total_rows, 1), 1.0)

    # Row count is deliberately only one signal; garbage-heavy table extraction
    # still scores poorly through labels, numbers, totals, and arithmetic.
    score = (
        0.22 * statement_score
        + 0.20 * totals_score
        + 0.22 * numeric_population_rate
        + 0.12 * row_scope_score
        + 0.12 * label_quality
        + 0.04 * duplicate_quality
        + 0.08 * arithmetic_consistency_score
    )
    score = round(max(0.0, min(score, 1.0)), 4)
    report_warnings = list(warnings or [])
    if missing_required_statement_count:
        report_warnings.append(f"missing_required_statements={missing_required_statement_count}")
    if total_rows < 20:
        report_warnings.append(f"low_row_count={total_rows}")
    if polluted_label_count:
        report_warnings.append(f"polluted_labels={polluted_label_count}")

    return ExtractionQualityReport(
        engine_name=engine_name,
        total_rows=total_rows,
        rows_by_statement=rows_by_statement,
        required_statements_found=required_statements_found,
        required_totals_found=required_totals_found,
        parsed_number_count=parsed_number_count,
        null_number_count=null_number_count,
        numeric_population_rate=round(numeric_population_rate, 4),
        polluted_label_count=polluted_label_count,
        duplicate_label_count=duplicate_label_count,
        missing_required_statement_count=missing_required_statement_count,
        arithmetic_consistency_score=round(arithmetic_consistency_score, 4),
        warnings=report_warnings,
        score=score,
        confidence=score,
    )


def _is_polluted_label(label: str) -> bool:
    normalized = normalize_label(label)
    return any(fragment in normalized for fragment in POLLUTED_LABEL_FRAGMENTS)


def _duplicate_count(document: ExtractedDocument) -> int:
    duplicates = 0
    for statement in document.statements.values():
        seen: set[str] = set()
        for row in statement.rows:
            key = normalize_label(row.canonical_label or row.label)
            if key in seen:
                duplicates += 1
            seen.add(key)
    return duplicates


def _arithmetic_consistency(document: ExtractedDocument) -> float:
    balance = document.statements.get("bilan")
    if balance is None:
        return 0.5
    values = {normalize_label(row.canonical_label or row.label): row.current_value for row in balance.rows}
    checks: list[bool] = []
    total_actif = values.get("total_actif")
    total_passif = values.get("total_passif")
    actif_net = values.get("actif_net")
    total_passif_actif_net = values.get("total_passif_et_actif_net") or values.get("total_passif_actif_net")
    if total_actif is not None and total_passif_actif_net is not None:
        checks.append(_close(total_actif, total_passif_actif_net))
    if total_actif is not None and total_passif is not None and actif_net is not None:
        checks.append(_close(actif_net, total_actif - total_passif))
    return sum(checks) / len(checks) if checks else 0.5


def _close(left: float | int, right: float | int, tolerance: float = 1.0) -> bool:
    return abs(float(left) - float(right)) <= tolerance
