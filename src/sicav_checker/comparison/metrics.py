from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from sicav_checker.comparison.coverage import (
    DUPLICATE_STATUSES,
    MISMATCH_STATUSES,
    MISSING_NEW_STATUSES,
    MISSING_OLD_STATUSES,
    OK_STATUSES,
)
from sicav_checker.domain.models import ComparisonResult, Evidence, FinancialDocument, Severity, Status, ValidationResult
from sicav_checker.normalization.label_normalizer import normalize_label

STRUCTURAL_STATUSES = {Status.DUPLICATE_LABEL, Status.PARSE_LOW_CONFIDENCE, Status.LOW_CONFIDENCE_EXTRACTION}
POLLUTED_FRAGMENTS = ("bilan_arrete", "etat_resultat_annee", "etat_variation_actif_net_annee", "note_annee", "annee_20")
CRITICAL_KEYS = {"total_actif", "actif_net", "total_passif_et_actif_net", "resultat_net", "valeur_liquidative"}


def build_metric_breakdown(
    old_document: FinancialDocument | None,
    new_document: FinancialDocument | None,
    comparisons: list[ComparisonResult],
    validations: list[ValidationResult] | None = None,
) -> dict[str, Any]:
    validations = validations or []
    compared = [item for item in comparisons if item.old_value is not None and item.new_value is not None and item.status not in DUPLICATE_STATUSES]
    exact_matches = sum(1 for item in compared if item.status in OK_STATUSES)
    actual_mismatches = sum(1 for item in comparisons if item.status in MISMATCH_STATUSES)
    missing_old = sum(1 for item in comparisons if item.status in MISSING_OLD_STATUSES)
    missing_new = sum(1 for item in comparisons if item.status in MISSING_NEW_STATUSES)
    duplicate_labels = sum(1 for item in comparisons if item.status in DUPLICATE_STATUSES)
    low_confidence = sum(1 for item in comparisons if item.status in {Status.PARSE_LOW_CONFIDENCE, Status.LOW_CONFIDENCE_EXTRACTION})
    polluted_labels = _polluted_label_count(comparisons)
    critical_financial = sum(1 for item in comparisons if _is_critical_financial_mismatch(item))
    identity_failures = sum(1 for item in validations if item.status in MISMATCH_STATUSES and item.severity == Severity.CRITICAL)

    old_keys = _unique_current_keys(old_document) if old_document else set()
    new_keys = _unique_previous_keys(new_document) if new_document else set()
    expected_keys = old_keys | new_keys
    paired_keys = {
        (item.statement, item.canonical_label)
        for item in comparisons
        if item.old_label is not None and item.new_label is not None and item.status not in DUPLICATE_STATUSES
    }

    financial_denominator = len(compared)
    financial_consistency = _percent(exact_matches, financial_denominator)
    coverage_denominator = len(expected_keys)
    extraction_coverage = _percent(len(paired_keys), coverage_denominator)
    structural_issue_count = duplicate_labels + polluted_labels + low_confidence
    structural_denominator = max(len(comparisons), 1)
    structural_quality = round(max(0.0, 100.0 - (structural_issue_count / structural_denominator * 100)), 2)

    extraction_confidence = _average_confidence([doc for doc in (old_document, new_document) if doc is not None])
    risk = _risk_breakdown(
        actual_mismatches=actual_mismatches,
        critical_financial=critical_financial,
        identity_failures=identity_failures,
        missing_total=missing_old + missing_new,
        duplicate_labels=duplicate_labels,
        polluted_labels=polluted_labels,
        low_confidence=low_confidence,
        extraction_coverage=extraction_coverage,
        extraction_confidence=extraction_confidence,
    )
    verdict = _verdict(risk, actual_mismatches, critical_financial, identity_failures, missing_old + missing_new, structural_issue_count, extraction_coverage, extraction_confidence)

    return {
        "financial_consistency": financial_consistency,
        "financial_consistency_numerator": exact_matches,
        "financial_consistency_denominator": financial_denominator,
        "extraction_coverage": extraction_coverage,
        "extraction_coverage_numerator": len(paired_keys),
        "extraction_coverage_denominator": coverage_denominator,
        "structural_quality": structural_quality,
        "structural_issue_count": structural_issue_count,
        "actual_mismatches": actual_mismatches,
        "missing_in_old_current": missing_old,
        "missing_in_new_comparative": missing_new,
        "missing_accounts": missing_old + missing_new,
        "duplicate_labels": duplicate_labels,
        "polluted_labels": polluted_labels,
        "low_confidence_parse": low_confidence,
        "critical_accounting_errors": critical_financial + identity_failures,
        "carry_forward_ok": exact_matches,
        "carry_forward_mismatch": actual_mismatches,
        "actually_compared_values": financial_denominator,
        "extraction_confidence": extraction_confidence,
        "risk": risk,
        "verdict": verdict,
        "why_verdict": _why_verdict(verdict, actual_mismatches, critical_financial + identity_failures, missing_old + missing_new, structural_issue_count),
        "metric_debug": {
            "financial_consistency": {"numerator": exact_matches, "denominator": financial_denominator, "formula": "exact_matches / actually_compared_values * 100"},
            "extraction_coverage": {"numerator": len(paired_keys), "denominator": coverage_denominator, "formula": "paired_unique_accounts / expected_unique_accounts * 100"},
            "structural_quality": {"issues": structural_issue_count, "denominator": structural_denominator, "formula": "100 - structural_issues / comparison_rows * 100"},
            "risk_score_inputs": risk.get("inputs", {}),
            "verdict_reason": verdict.get("reason", ""),
        },
    }


def build_review_items(
    comparisons: list[ComparisonResult],
    old_document: FinancialDocument | None = None,
    new_document: FinancialDocument | None = None,
) -> list[dict[str, Any]]:
    old_year = old_document.document_year if old_document else None
    new_year = new_document.document_year if new_document else None
    old_engine = old_document.extraction_method if old_document else "unknown"
    new_engine = new_document.extraction_method if new_document else "unknown"
    return [_review_item(item, index, old_year, new_year, old_engine, new_engine) for index, item in enumerate(comparisons, start=1)]


def write_metric_debug(path: Path, metrics: dict[str, Any], review_items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"metrics": metrics.get("metric_debug", {}), "summary": metrics, "review_items": review_items}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_comparison_debug(path: Path, review_items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"items": review_items}, indent=2, ensure_ascii=False), encoding="utf-8")


def _review_item(item: ComparisonResult, index: int, old_year: int | None, new_year: int | None, old_engine: str, new_engine: str) -> dict[str, Any]:
    expected = item.old_value
    actual = item.new_value
    difference = item.delta
    difference_percent = None
    if isinstance(expected, (int, float)) and expected != 0 and isinstance(difference, (int, float)):
        difference_percent = round((float(difference) / float(expected)) * 100, 4)
    explanation, technical_reason, accountant_reason, recommended_action, evidence_type = _explain(item, old_year, new_year)
    old_evidence = _evidence(item.old_evidence, item.old_label, item.old_value, item.statement, old_engine)
    new_evidence = _evidence(item.new_evidence, item.new_label, item.new_value, item.statement, new_engine)
    return {
        "id": f"{item.pair}:{item.statement}:{item.canonical_label}:{index}",
        "pair": item.pair,
        "year": item.year,
        "statement": item.statement,
        "statement_name": item.statement,
        "account_label_old": item.old_label,
        "account_label_new": item.new_label,
        "old_label": item.old_label,
        "new_label": item.new_label,
        "canonical_label": item.canonical_label,
        "status": item.status.value if hasattr(item.status, "value") else str(item.status),
        "severity": item.severity.value if hasattr(item.severity, "value") else str(item.severity),
        "old_current_value": item.old_value,
        "old_previous_value": None,
        "new_current_value": None,
        "new_previous_value": item.new_value,
        "old_value": item.old_value,
        "new_value": item.new_value,
        "expected_value": expected,
        "actual_value": actual,
        "difference": difference,
        "delta": difference,
        "difference_percent": difference_percent,
        "explanation": explanation,
        "technical_reason": technical_reason,
        "accountant_reason": accountant_reason,
        "recommended_action": recommended_action,
        "old_document_year": old_year,
        "new_document_year": new_year,
        "compared_year": old_year,
        "old_page": old_evidence.get("page"),
        "new_page": new_evidence.get("page"),
        "old_section": item.statement,
        "new_section": item.statement,
        "old_line_text": old_evidence.get("raw_text"),
        "new_line_text": new_evidence.get("raw_text"),
        "old_bbox": old_evidence.get("bounding_box"),
        "new_bbox": new_evidence.get("bounding_box"),
        "confidence": item.confidence,
        "extraction_engine": new_engine if new_engine != "unknown" else old_engine,
        "evidence_type": evidence_type,
        "matching_method": item.matching_method,
        "note": item.note,
        "old_evidence": old_evidence,
        "new_evidence": new_evidence,
    }


def _explain(item: ComparisonResult, old_year: int | None, new_year: int | None) -> tuple[str, str, str, str, str]:
    status = item.status
    old_year_text = str(old_year or item.year)
    new_year_text = str(new_year or "the new")
    if status in OK_STATUSES:
        return (
            f"The {old_year_text} current-year value in the old report matches the {old_year_text} comparative value in the {new_year_text} report.",
            "old_current_value equals new_previous_value within tolerance.",
            "No carry-forward difference was detected for this account.",
            "No action required.",
            "matched_value",
        )
    if status in MISMATCH_STATUSES:
        return (
            f"The {old_year_text} current-year value in the old report is {_fmt(item.old_value)}, but the {old_year_text} comparative value in the {new_year_text} report is {_fmt(item.new_value)}. Difference: {_fmt(item.delta)}.",
            "old_current_value and new_previous_value differ after deterministic numeric comparison.",
            "This may be a real carry-forward error and should be reviewed against the signed reports.",
            "Verify both source values manually and confirm whether the comparative column was carried forward correctly.",
            "financial_mismatch",
        )
    if status in MISSING_OLD_STATUSES:
        return (
            "The account appears in the new report's comparative column, but the matching account was not found in the old report.",
            "new comparative key has no matching old current-year key.",
            "This is likely an extraction or label-mapping issue unless confirmed manually.",
            "Review the old report section and add/adjust label mapping if the account exists there.",
            "missing_old_current",
        )
    if status in MISSING_NEW_STATUSES:
        return (
            "The account exists in the old report but was not found in the comparative column of the new report.",
            "old current-year key has no matching new comparative key.",
            "This is likely a missing extraction, renamed label, or unavailable comparative account.",
            "Review the new report comparative column and confirm whether the account is present under another label.",
            "missing_new_comparative",
        )
    if status in DUPLICATE_STATUSES:
        return (
            "Multiple rows produced the same canonical label.",
            "duplicate canonical labels were quarantined and excluded from financial consistency.",
            "Repeated labels may need parent context, such as Souscriptions versus Rachats or opening versus closing balances.",
            "Add or verify parent context in normalization to disambiguate the repeated account labels.",
            "duplicate_label",
        )
    if status == Status.PARSE_LOW_CONFIDENCE:
        return (
            "The row was parsed with low confidence.",
            "extraction confidence fell below the comparison threshold.",
            "The value may be correct, but the extraction evidence should be checked manually.",
            "Review the raw extracted row and source table layout.",
            "low_confidence_parse",
        )
    return (
        item.note or "This row requires review.",
        "status requires manual interpretation.",
        "Review the row evidence before drawing an accounting conclusion.",
        "Inspect old and new source rows side by side.",
        "review",
    )


def _risk_breakdown(**inputs: Any) -> dict[str, Any]:
    actual_mismatches = inputs["actual_mismatches"]
    critical_financial = inputs["critical_financial"]
    identity_failures = inputs["identity_failures"]
    missing_total = inputs["missing_total"]
    duplicate_labels = inputs["duplicate_labels"]
    polluted_labels = inputs["polluted_labels"]
    low_confidence = inputs["low_confidence"]
    extraction_coverage = inputs["extraction_coverage"]
    extraction_confidence = inputs["extraction_confidence"]
    if critical_financial or identity_failures:
        category, level, score, rationale = "HIGH_FINANCIAL_RISK", "HIGH", 85, "Critical carry-forward mismatch or accounting identity failure detected."
    elif actual_mismatches:
        category, level, score, rationale = "HIGH_FINANCIAL_RISK", "HIGH", 80, "Actual value differences were detected."
    elif extraction_coverage < 80 or extraction_confidence < 0.75 or missing_total >= 5:
        category, level, score, rationale = "HIGH_EXTRACTION_RISK", "HIGH", 60, "Compared values match, but extraction coverage or confidence needs review."
    elif missing_total or duplicate_labels or polluted_labels or low_confidence:
        category, level, score, rationale = "MEDIUM_STRUCTURAL_RISK", "MEDIUM", 35, "No financial mismatch found, but structural extraction or label issues require review."
    else:
        category, level, score, rationale = "LOW", "LOW", 5, "All compared values match and coverage is high."
    return {"category": category, "level": level, "score": score, "rationale": rationale, "inputs": inputs}


def _verdict(risk: dict[str, Any], actual_mismatches: int, critical_financial: int, identity_failures: int, missing_total: int, structural_issues: int, coverage: float, confidence: float) -> dict[str, str]:
    if actual_mismatches or critical_financial or identity_failures:
        return {"label": "FAIL", "reason": "Actual carry-forward mismatch or critical accounting identity issue detected."}
    if missing_total or structural_issues or coverage < 95 or confidence < 0.85:
        return {"label": "NEEDS REVIEW", "reason": "Financial values compared successfully, but some rows require extraction or label review."}
    return {"label": "PASS", "reason": "No financial mismatches, no critical anomalies, and extraction coverage/confidence are high."}


def _why_verdict(verdict: dict[str, str], mismatches: int, critical: int, missing: int, structural: int) -> dict[str, Any]:
    passed = []
    needs_review = []
    if mismatches == 0:
        passed.append("No actual carry-forward value differences were detected.")
    if critical == 0:
        passed.append("No critical accounting errors were detected.")
    if missing:
        needs_review.append(f"{missing} accounts are missing or unpaired and need extraction/label review.")
    if structural:
        needs_review.append(f"{structural} structural extraction issues were detected.")
    return {"verdict": verdict["label"], "reason": verdict["reason"], "passed": passed, "needs_review": needs_review, "issue_type": "financial" if mismatches or critical else ("extraction_structural" if needs_review else "none")}


def _evidence(evidence: Evidence | None, label: str | None, value: float | int | None, statement: str, engine: str) -> dict[str, Any]:
    if evidence is None:
        return {"page": None, "section": statement, "raw_text": label or "", "bounding_box": None, "value": value, "extraction_method": engine}
    payload = evidence.model_dump(mode="json")
    payload.setdefault("section", statement)
    payload.setdefault("raw_text", label or "")
    payload.setdefault("value", value)
    return payload


def _unique_current_keys(document: FinancialDocument) -> set[tuple[str, str]]:
    return {(name, row.canonical_label) for name, statement in document.statements.items() for row in statement.rows if row.canonical_label and row.current_value is not None}


def _unique_previous_keys(document: FinancialDocument) -> set[tuple[str, str]]:
    return {(name, row.canonical_label) for name, statement in document.statements.items() for row in statement.rows if row.canonical_label and row.previous_value is not None}


def _polluted_label_count(comparisons: list[ComparisonResult]) -> int:
    labels = [item.old_label or "" for item in comparisons] + [item.new_label or "" for item in comparisons]
    return sum(1 for label in labels if label and any(fragment in normalize_label(label) for fragment in POLLUTED_FRAGMENTS))


def _is_critical_financial_mismatch(item: ComparisonResult) -> bool:
    if item.status not in MISMATCH_STATUSES:
        return False
    normalized = normalize_label(item.canonical_label)
    return item.severity == Severity.CRITICAL or any(key in normalized for key in CRITICAL_KEYS)


def _average_confidence(documents: list[FinancialDocument]) -> float:
    values = [document.confidence for document in documents]
    return round(sum(values) / len(values), 4) if values else 0.0


def _percent(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) * 100, 2) if denominator else 0.0


def _fmt(value: Any) -> str:
    if value is None:
        return "not found"
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)
