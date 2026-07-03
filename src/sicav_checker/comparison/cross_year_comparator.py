from __future__ import annotations

from math import isclose

from sicav_checker.comparison.anomaly_classifier import classify_severity
from sicav_checker.comparison.label_matcher import match_label
from sicav_checker.models import ComparisonResult, ExtractedDocument, StatementRow, Status


def _row_map(rows: list[StatementRow]) -> dict[str, StatementRow]:
    return {row.canonical_label: row for row in rows}


def compare_documents(old_doc: ExtractedDocument, new_doc: ExtractedDocument, tolerance: float = 0.001) -> list[ComparisonResult]:
    results: list[ComparisonResult] = []
    pair = f"{old_doc.document_year}->{new_doc.document_year}"
    statements = sorted(set(old_doc.statements) | set(new_doc.statements))

    for statement_name in statements:
        old_rows = _row_map(old_doc.statements.get(statement_name, type("Empty", (), {"rows": []})()).rows)
        new_rows = _row_map(new_doc.statements.get(statement_name, type("Empty", (), {"rows": []})()).rows)
        used_new: set[str] = set()

        for label, old_row in old_rows.items():
            matched_label, score, renamed = match_label(label, list(new_rows))
            new_row = new_rows.get(matched_label) if matched_label else None
            if new_row:
                used_new.add(matched_label or "")

            status = Status.OK
            note = ""
            new_value = new_row.previous_value if new_row else None
            old_value = old_row.current_value

            if old_row.confidence < 0.75 or (new_row and new_row.confidence < 0.75):
                status = Status.LOW_CONFIDENCE_EXTRACTION
            elif new_row is None:
                status = Status.MISSING_IN_NEW
            elif old_value is None or new_value is None:
                status = Status.MISMATCH if old_value != new_value else Status.OK
            else:
                status = Status.OK if isclose(float(old_value), float(new_value), abs_tol=tolerance) else Status.MISMATCH

            if status == Status.OK and renamed:
                status = Status.LABEL_RENAMED
                note = f"Fuzzy label match score {score:.1f}"

            delta = None
            if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
                delta = float(new_value) - float(old_value)

            results.append(
                ComparisonResult(
                    pair=pair,
                    year=old_doc.document_year,
                    statement=statement_name,
                    old_label=old_row.label,
                    new_label=new_row.label if new_row else None,
                    canonical_label=label,
                    old_value=old_value,
                    new_value=new_value,
                    status=status,
                    severity=classify_severity(label),
                    delta=delta,
                    confidence=min(old_row.confidence, new_row.confidence if new_row else 1.0),
                    note=note,
                )
            )

        for label, new_row in new_rows.items():
            if label in used_new or label in old_rows:
                continue
            results.append(
                ComparisonResult(
                    pair=pair,
                    year=old_doc.document_year,
                    statement=statement_name,
                    old_label=None,
                    new_label=new_row.label,
                    canonical_label=label,
                    old_value=None,
                    new_value=new_row.previous_value,
                    status=Status.MISSING_IN_OLD,
                    severity=classify_severity(label),
                )
            )
    return results
