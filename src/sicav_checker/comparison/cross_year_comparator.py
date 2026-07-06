from __future__ import annotations

from dataclasses import dataclass
from math import isclose

from sicav_checker.comparison.anomaly_classifier import classify_severity
from sicav_checker.comparison.label_matcher import match_label
from sicav_checker.models import ComparisonResult, ExtractedDocument, StatementRow, Status
from sicav_checker.normalization.label_normalizer import normalize_label


@dataclass(frozen=True)
class RowEntry:
    key: str
    row: StatementRow


def _canonical_key(statement_name: str, row: StatementRow) -> str:
    canonical = row.canonical_label or ""
    if canonical:
        return canonical
    statement_key = normalize_label(statement_name) or statement_name
    label_key = normalize_label(row.label) or "unknown_line"
    return f"{statement_key}__{label_key}"


def _row_entries(statement_name: str, rows: list[StatementRow]) -> list[RowEntry]:
    counts: dict[str, int] = {}
    entries: list[RowEntry] = []
    for row in rows:
        base = _canonical_key(statement_name, row)
        counts[base] = counts.get(base, 0) + 1
        key = base if counts[base] == 1 else f"{base}__line_{counts[base]}"
        if not row.canonical_label:
            row.canonical_label = base
        entries.append(RowEntry(key=key, row=row))
    return entries


def _entry_map(entries: list[RowEntry]) -> dict[str, RowEntry]:
    return {entry.key: entry for entry in entries}


def compare_documents(old_doc: ExtractedDocument, new_doc: ExtractedDocument, tolerance: float = 0.001) -> list[ComparisonResult]:
    results: list[ComparisonResult] = []
    pair = f"{old_doc.document_year}->{new_doc.document_year}"
    statements = sorted(set(old_doc.statements) | set(new_doc.statements))

    for statement_name in statements:
        old_statement = old_doc.statements.get(statement_name)
        new_statement = new_doc.statements.get(statement_name)
        old_entries = _row_entries(statement_name, old_statement.rows if old_statement else [])
        new_entries = _row_entries(statement_name, new_statement.rows if new_statement else [])
        new_rows = _entry_map(new_entries)
        used_new: set[str] = set()

        for old_entry in old_entries:
            label = old_entry.key
            old_row = old_entry.row
            matched_label, score, renamed = match_label(label, [entry.key for entry in new_entries if entry.key not in used_new])
            new_entry = new_rows.get(matched_label) if matched_label else None
            new_row = new_entry.row if new_entry else None
            if new_entry:
                used_new.add(new_entry.key)

            status = Status.OK
            note = ""
            old_value = old_row.current_value
            new_value = new_row.previous_value if new_row else None

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
                    canonical_label=old_row.canonical_label or label,
                    old_value=old_value,
                    new_value=new_value,
                    status=status,
                    severity=classify_severity(old_row.canonical_label or label),
                    delta=delta,
                    confidence=min(old_row.confidence, new_row.confidence if new_row else 1.0),
                    note=note,
                    old_evidence=old_row.evidence,
                    new_evidence=new_row.evidence if new_row else None,
                    matching_method=new_row.match.method if new_row and new_row.match else ("fuzzy" if renamed else "exact"),
                )
            )

        for new_entry in new_entries:
            if new_entry.key in used_new:
                continue
            new_row = new_entry.row
            results.append(
                ComparisonResult(
                    pair=pair,
                    year=old_doc.document_year,
                    statement=statement_name,
                    old_label=None,
                    new_label=new_row.label,
                    canonical_label=new_row.canonical_label or new_entry.key,
                    old_value=None,
                    new_value=new_row.previous_value,
                    status=Status.MISSING_IN_OLD,
                    severity=classify_severity(new_row.canonical_label or new_entry.key),
                    confidence=new_row.confidence,
                    new_evidence=new_row.evidence,
                    matching_method=new_row.match.method if new_row.match else "unmatched",
                )
            )
    return results
