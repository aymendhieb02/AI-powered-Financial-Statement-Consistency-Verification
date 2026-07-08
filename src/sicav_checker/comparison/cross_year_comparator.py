from __future__ import annotations

import json
from dataclasses import dataclass
from math import isclose
from pathlib import Path

from sicav_checker.comparison.anomaly_classifier import classify_severity
from sicav_checker.comparison.label_matcher import match_label
from sicav_checker.models import ComparisonResult, ExtractedDocument, StatementRow, Status
from sicav_checker.normalization.label_normalizer import normalize_label


@dataclass(frozen=True)
class RowEntry:
    key: str
    row: StatementRow


VARIATION_STATEMENT_KEYS = {"variation_actif_net", "etat_variation_actif_net"}
VARIATION_CONTEXTS = {"souscriptions", "rachats", "operations_exploitation", "actif_net", "nombre_actions"}
VARIATION_CONTEXTUAL_LABELS = {
    "capital",
    "regularisation_sommes_non_distribuables",
    "regularisation_sommes_distribuables",
    "en_debut_exercice",
    "en_fin_exercice",
}


def compare_documents(old_doc: ExtractedDocument, new_doc: ExtractedDocument, tolerance: float = 0.001) -> list[ComparisonResult]:
    results: list[ComparisonResult] = []
    pair = f"{old_doc.document_year}->{new_doc.document_year}"
    statements = sorted(set(old_doc.statements) | set(new_doc.statements))

    for statement_name in statements:
        old_statement = old_doc.statements.get(statement_name)
        new_statement = new_doc.statements.get(statement_name)
        old_entries, old_duplicate_groups = _dedupe_entries(statement_name, old_statement.rows if old_statement else [])
        new_entries, new_duplicate_groups = _dedupe_entries(statement_name, new_statement.rows if new_statement else [])

        for duplicate_group in old_duplicate_groups.values():
            results.append(_duplicate_result(pair, old_doc.document_year, statement_name, duplicate_group, old_side=True))
        for duplicate_group in new_duplicate_groups.values():
            results.append(_duplicate_result(pair, old_doc.document_year, statement_name, duplicate_group, old_side=False))

        new_by_key = {entry.key: entry for entry in new_entries}
        used_new: set[str] = set()
        old_unique_keys = {entry.key for entry in old_entries}
        old_duplicate_keys = set(old_duplicate_groups)
        new_duplicate_keys = set(new_duplicate_groups)

        for old_entry in old_entries:
            if old_entry.key in new_duplicate_keys:
                continue
            matched_key, score, renamed = match_label(old_entry.key, [entry.key for entry in new_entries if entry.key not in used_new])
            new_entry = new_by_key.get(matched_key) if matched_key else None
            if new_entry:
                used_new.add(new_entry.key)
            results.append(_compare_entry(pair, old_doc.document_year, statement_name, old_entry, new_entry, tolerance, score, renamed))

        for new_entry in new_entries:
            if new_entry.key in used_new or new_entry.key in old_unique_keys or new_entry.key in old_duplicate_keys:
                continue
            results.append(_missing_old_result(pair, old_doc.document_year, statement_name, new_entry))

    _write_debug_json(results)
    return results


def _dedupe_entries(statement_name: str, rows: list[StatementRow]) -> tuple[list[RowEntry], dict[str, list[RowEntry]]]:
    grouped: dict[str, list[RowEntry]] = {}
    for row in rows:
        key = _canonical_key(statement_name, row)
        if not row.canonical_label:
            row.canonical_label = key
        grouped.setdefault(key, []).append(RowEntry(key=key, row=row))

    unique = [entries[0] for entries in grouped.values() if len(entries) == 1]
    duplicates = {key: entries for key, entries in grouped.items() if len(entries) > 1}
    return unique, duplicates


def _canonical_key(statement_name: str, row: StatementRow) -> str:
    statement_key = normalize_label(statement_name) or statement_name
    canonical = (row.canonical_label or "").strip()
    if not canonical:
        label_key = normalize_label(row.label) or "unknown_line"
        canonical = f"{statement_key}__{label_key}"

    if statement_key in VARIATION_STATEMENT_KEYS:
        return _variation_key_with_context(canonical, row)
    return canonical


def _variation_key_with_context(canonical: str, row: StatementRow) -> str:
    if canonical.startswith("variation_actif_net__") and canonical.count("__") >= 2:
        return canonical

    legacy = _legacy_variation_key(canonical)
    if legacy:
        return legacy

    base = canonical.split("__")[-1]
    if base not in VARIATION_CONTEXTUAL_LABELS:
        return canonical

    evidence = row.evidence
    context = ""
    if evidence is not None:
        context = normalize_label(evidence.section_name or evidence.section or "")
    if context in {"etat_variation_actif_net", "variation_actif_net"}:
        context = ""
    if context in VARIATION_CONTEXTS:
        return f"variation_actif_net__{context}__{base}"
    return canonical


def _legacy_variation_key(canonical: str) -> str | None:
    rest = ""
    if canonical.startswith("variation_actif_net__"):
        rest = canonical.removeprefix("variation_actif_net__")
    elif canonical.startswith("variation_actif_net_"):
        rest = canonical.removeprefix("variation_actif_net_")
    if not rest:
        return None
    for context in sorted(VARIATION_CONTEXTS, key=len, reverse=True):
        prefix = f"{context}_"
        if rest.startswith(prefix):
            base = rest[len(prefix):]
            if base in VARIATION_CONTEXTUAL_LABELS:
                return f"variation_actif_net__{context}__{base}"
    return None


def _compare_entry(
    pair: str,
    year: int,
    statement_name: str,
    old_entry: RowEntry,
    new_entry: RowEntry | None,
    tolerance: float,
    score: float,
    renamed: bool,
) -> ComparisonResult:
    old_row = old_entry.row
    new_row = new_entry.row if new_entry else None
    old_value = old_row.current_value
    new_value = new_row.previous_value if new_row else None

    if old_row.confidence < 0.75 or (new_row and new_row.confidence < 0.75):
        status = Status.PARSE_LOW_CONFIDENCE
    elif new_row is None:
        status = Status.MISSING_IN_NEW_COMPARATIVE
    elif old_value is None or new_value is None:
        status = Status.CARRY_FORWARD_MISMATCH if old_value != new_value else Status.CARRY_FORWARD_OK
    else:
        status = Status.CARRY_FORWARD_OK if isclose(float(old_value), float(new_value), abs_tol=tolerance) else Status.CARRY_FORWARD_MISMATCH

    note = ""
    if status == Status.CARRY_FORWARD_OK and renamed:
        status = Status.LABEL_RENAMED
        note = f"Fuzzy label match score {score:.1f}"

    delta = None
    if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
        delta = float(new_value) - float(old_value)

    return ComparisonResult(
        pair=pair,
        year=year,
        statement=statement_name,
        old_label=old_row.label,
        new_label=new_row.label if new_row else None,
        canonical_label=old_entry.key,
        old_value=old_value,
        new_value=new_value,
        status=status,
        severity=classify_severity(old_entry.key, status),
        delta=delta,
        confidence=min(old_row.confidence, new_row.confidence if new_row else 1.0),
        note=note,
        old_evidence=old_row.evidence,
        new_evidence=new_row.evidence if new_row else None,
        matching_method=new_row.match.method if new_row and new_row.match else ("fuzzy" if renamed else "exact"),
    )


def _missing_old_result(pair: str, year: int, statement_name: str, new_entry: RowEntry) -> ComparisonResult:
    row = new_entry.row
    return ComparisonResult(
        pair=pair,
        year=year,
        statement=statement_name,
        old_label=None,
        new_label=row.label,
        canonical_label=new_entry.key,
        old_value=None,
        new_value=row.previous_value,
        status=Status.MISSING_IN_OLD_CURRENT,
        severity=classify_severity(new_entry.key, Status.MISSING_IN_OLD_CURRENT),
        confidence=row.confidence,
        new_evidence=row.evidence,
        matching_method=row.match.method if row.match else "unmatched",
    )


def _duplicate_result(pair: str, year: int, statement_name: str, entries: list[RowEntry], old_side: bool) -> ComparisonResult:
    primary = entries[0].row
    candidate_evidence = [entry.row.evidence for entry in entries if entry.row.evidence is not None]
    return ComparisonResult(
        pair=pair,
        year=year,
        statement=statement_name,
        old_label=primary.label if old_side else None,
        new_label=None if old_side else primary.label,
        canonical_label=entries[0].key,
        old_value=primary.current_value if old_side else None,
        new_value=None if old_side else primary.previous_value,
        status=Status.DUPLICATE_LABEL,
        severity=classify_severity(entries[0].key, Status.DUPLICATE_LABEL),
        confidence=primary.confidence,
        note="Duplicate canonical label detected; not used in deterministic comparison.",
        old_evidence=primary.evidence if old_side else None,
        new_evidence=None if old_side else primary.evidence,
        duplicate_candidates=candidate_evidence,
        matching_method="duplicate_label",
    )


def _write_debug_json(results: list[ComparisonResult]) -> None:
    debug_dir = Path("logs") / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "statement_name": item.statement,
            "old_label": item.old_label,
            "new_label": item.new_label,
            "canonical_label": item.canonical_label,
            "old_current_value": item.old_value,
            "new_previous_value": item.new_value,
            "carry_forward_delta": item.delta,
            "status": item.status,
            "severity": item.severity,
            "confidence": item.confidence,
        }
        for item in results
    ]
    (debug_dir / "comparison_debug.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
