from __future__ import annotations

import json
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
from sicav_checker.extraction.quality import pollution_reasons
from sicav_checker.normalization.label_normalizer import normalize_label

STRUCTURAL_STATUSES = {Status.DUPLICATE_LABEL, Status.PARSE_LOW_CONFIDENCE, Status.LOW_CONFIDENCE_EXTRACTION}
CRITICAL_KEYS = {"total_actif", "actif_net", "total_passif_et_actif_net", "total_passif_actif_net", "resultat_net", "valeur_liquidative"}
EMBEDDED_TITLE_KEYS = ("variation_de_l_actif_net", "bilan_arrete", "etat_resultat", "note_annee")


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
    merged_rows = _merged_row_count(comparisons)
    hierarchy_gaps = _hierarchy_gap_count(comparisons)
    critical_financial = sum(1 for item in comparisons if _is_critical_financial_mismatch(item))
    identity_failures = sum(1 for item in validations if item.status in MISMATCH_STATUSES and item.severity == Severity.CRITICAL)

    old_keys = _unique_current_keys(old_document) if old_document else set()
    new_keys = _unique_previous_keys(new_document) if new_document else set()
    expected_keys = old_keys | new_keys
    paired_keys = {
        (item.statement, item.canonical_label)
        for item in comparisons
        if (item.old_label is not None and item.new_label is not None) or item.status in DUPLICATE_STATUSES
    }

    financial_denominator = len(compared)
    financial_consistency = _percent(exact_matches, financial_denominator)
    coverage_denominator = len(expected_keys)
    extraction_coverage = _percent(len(paired_keys), coverage_denominator)
    structural_issue_count = duplicate_labels + polluted_labels + low_confidence + merged_rows + hierarchy_gaps
    structural_denominator = max(len(comparisons), 1)
    structural_quality = round(max(0.0, 100.0 - (structural_issue_count / structural_denominator * 100)), 2)

    extraction_confidence = _average_confidence([doc for doc in (old_document, new_document) if doc is not None])
    accounting_health = _accounting_health(financial_consistency, actual_mismatches, critical_financial + identity_failures)
    risk = _risk_breakdown(
        actual_mismatches=actual_mismatches,
        critical_financial=critical_financial,
        identity_failures=identity_failures,
        missing_total=missing_old + missing_new,
        duplicate_labels=duplicate_labels,
        polluted_labels=polluted_labels,
        low_confidence=low_confidence,
        merged_rows=merged_rows,
        hierarchy_gaps=hierarchy_gaps,
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
        "merged_rows": merged_rows,
        "hierarchy_gaps": hierarchy_gaps,
        "low_confidence_parse": low_confidence,
        "critical_accounting_errors": critical_financial + identity_failures,
        "carry_forward_ok": exact_matches,
        "carry_forward_mismatch": actual_mismatches,
        "actually_compared_values": financial_denominator,
        "extraction_confidence": extraction_confidence,
        "accounting_health": accounting_health,
        "risk": risk,
        "verdict": verdict,
        "why_verdict": _why_verdict(verdict, actual_mismatches, critical_financial + identity_failures, missing_old + missing_new, structural_issue_count),
        "metric_debug": {
            "financial_consistency": {"numerator": exact_matches, "denominator": financial_denominator, "formula": "exact_matches / actually_compared_values * 100"},
            "extraction_coverage": {"numerator": len(paired_keys), "denominator": coverage_denominator, "formula": "paired_unique_accounts / expected_unique_accounts * 100"},
            "structural_quality": {"issues": structural_issue_count, "denominator": structural_denominator, "formula": "100 - structural_issues / comparison_rows * 100"},
            "accounting_health": accounting_health,
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
    old_document_id = Path(old_document.source_file).name if old_document and old_document.source_file else None
    new_document_id = Path(new_document.source_file).name if new_document and new_document.source_file else None
    return [_review_item(item, index, old_year, new_year, old_engine, new_engine, old_document_id, new_document_id) for index, item in enumerate(comparisons, start=1)]


def write_metric_debug(path: Path, metrics: dict[str, Any], review_items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"metrics": metrics.get("metric_debug", {}), "summary": metrics, "review_items": review_items}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_comparison_debug(path: Path, review_items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"items": review_items}, indent=2, ensure_ascii=False), encoding="utf-8")


def _review_item(item: ComparisonResult, index: int, old_year: int | None, new_year: int | None, old_engine: str, new_engine: str, old_document_id: str | None, new_document_id: str | None) -> dict[str, Any]:
    expected = item.old_value
    actual = item.new_value
    difference = item.delta
    difference_percent = None
    if isinstance(expected, (int, float)) and expected != 0 and isinstance(difference, (int, float)):
        difference_percent = round((float(difference) / float(expected)) * 100, 4)
    explanation, technical_reason, accountant_reason, recommended_action, evidence_type, reason = _explain(item, old_year, new_year)
    old_evidence = _side_evidence(item.old_evidence, item.old_label, item.old_value, item.statement, old_engine, old_document_id, value_role="current")
    new_evidence = _side_evidence(item.new_evidence, item.new_label, item.new_value, item.statement, new_engine, new_document_id, value_role="previous")
    duplicate_candidates = [
        _side_evidence(
            candidate,
            candidate.label_text or candidate.raw_text or item.canonical_label,
            candidate.current_value if candidate.current_value is not None else candidate.previous_value,
            item.statement,
            candidate.extraction_method or old_engine,
            candidate.document_id or old_document_id or new_document_id,
            value_role="current" if candidate.current_value is not None else "previous",
        )
        for candidate in item.duplicate_candidates
    ]
    polluted = pollution_reasons(item.old_label or "") + pollution_reasons(item.new_label or "")
    unique_polluted = sorted(set(polluted))
    issue_classification = _issue_classification(item, evidence_type, unique_polluted)
    issue_type = _issue_type(item, evidence_type, unique_polluted)
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
        "hierarchy_path": _hierarchy_path(item),
        "status": item.status.value if hasattr(item.status, "value") else str(item.status),
        "status_group": _status_group(item, issue_type),
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
        "reason": reason,
        "explanation": explanation,
        "technical_reason": technical_reason,
        "accountant_reason": accountant_reason,
        "recommended_action": recommended_action,
        "old_document_year": old_year,
        "new_document_year": new_year,
        "compared_year": old_year,
        "old_page": old_evidence.get("page_number") or old_evidence.get("page"),
        "new_page": new_evidence.get("page_number") or new_evidence.get("page"),
        "page": new_evidence.get("page_number") or new_evidence.get("page") or old_evidence.get("page_number") or old_evidence.get("page"),
        "section": new_evidence.get("section") or new_evidence.get("section_name") or old_evidence.get("section") or old_evidence.get("section_name") or item.statement,
        "old_section": old_evidence.get("section") or old_evidence.get("section_name") or item.statement,
        "new_section": new_evidence.get("section") or new_evidence.get("section_name") or item.statement,
        "old_line_text": old_evidence.get("raw_line") or old_evidence.get("raw_text"),
        "new_line_text": new_evidence.get("raw_line") or new_evidence.get("raw_text"),
        "old_raw_line": old_evidence.get("raw_line") or old_evidence.get("raw_text"),
        "new_raw_line": new_evidence.get("raw_line") or new_evidence.get("raw_text"),
        "old_bbox": old_evidence.get("bbox_value") or old_evidence.get("bbox_row") or old_evidence.get("bounding_box"),
        "new_bbox": new_evidence.get("bbox_value") or new_evidence.get("bbox_row") or new_evidence.get("bounding_box"),
        "confidence": item.confidence,
        "extraction_engine": new_engine if new_engine != "unknown" else old_engine,
        "evidence_type": evidence_type,
        "issue_classification": issue_classification,
        "issue_type": issue_type,
        "pollution_reasons": unique_polluted,
        "merged_row_suspected": _looks_like_merged_row(item),
        "matching_method": item.matching_method,
        "note": item.note,
        "old_document_id": old_document_id,
        "new_document_id": new_document_id,
        "old_evidence": old_evidence,
        "new_evidence": new_evidence,
        "duplicate_candidates": duplicate_candidates,
    }


def _explain(item: ComparisonResult, old_year: int | None, new_year: int | None) -> tuple[str, str, str, str, str, str]:
    status = item.status
    old_year_text = str(old_year or item.year)
    new_year_text = str(new_year or "the new")
    if status in OK_STATUSES:
        return (
            f"The {old_year_text} value in the old report matches the comparative {old_year_text} value carried into the {new_year_text} report.",
            "old_current_value equals new_previous_value within comparison tolerance.",
            "No carry-forward difference was detected for this account.",
            "No action required.",
            "matched_value",
            "carry_forward_ok",
        )
    if status in MISMATCH_STATUSES:
        return (
            f"The carried-forward amount does not match: {_fmt(item.old_value)} in the old report versus {_fmt(item.new_value)} in the new report. Difference: {_fmt(item.delta)}.",
            "old_current_value and new_previous_value differ after deterministic numeric comparison.",
            "This looks like a real comparative-value inconsistency unless one of the extracted source values is wrong.",
            "Open both report pages, confirm the source amounts, and verify whether the comparative column was carried forward correctly.",
            "financial_mismatch",
            "value_difference",
        )
    if status in MISSING_OLD_STATUSES:
        return (
            "The comparative account is visible in the new report, but the matching source account was not found in the old report extraction.",
            "new comparative key has no matching old current-year key.",
            "This usually points to extraction coverage, label mapping, or a section-detection issue rather than a confirmed accounting failure.",
            "Inspect the old report evidence and restore the missing source account before concluding on accounting consistency.",
            "missing_old_current",
            "missing_in_old",
        )
    if status in MISSING_NEW_STATUSES:
        return (
            "The old report contains the source account, but the matching comparative account was not found in the new report extraction.",
            "old current-year key has no matching new comparative key.",
            "This usually means the new report comparison column was not extracted, was renamed, or was merged into another row.",
            "Inspect the new report evidence and confirm whether the comparative amount is present under another account label.",
            "missing_new_comparative",
            "missing_in_new",
        )
    if status in DUPLICATE_STATUSES:
        return (
            "Several extracted rows collapsed into the same normalized account, so FinVerify quarantined them instead of guessing which one should be compared.",
            "duplicate canonical labels were preserved as evidence and excluded from deterministic comparison.",
            "This is a structural extraction problem, not an automatic accounting failure. It often happens when parent context such as subscription/redemption or opening/closing balance is missing.",
            "Review the duplicate candidates, recover the missing parent context, and then rerun comparison.",
            "duplicate_label",
            "duplicate_label",
        )
    if status == Status.PARSE_LOW_CONFIDENCE:
        return (
            "The row was extracted with low confidence and should be reviewed before relying on the comparison result.",
            "extraction confidence fell below the comparison threshold.",
            "The amount may still be correct, but the evidence is not strong enough for a clean audit conclusion.",
            "Inspect the raw line and page image, then confirm whether the row should be accepted or corrected.",
            "low_confidence_parse",
            "low_confidence_parse",
        )
    return (
        item.note or "This row requires review.",
        "status requires manual interpretation.",
        "Review the row evidence before drawing an accounting conclusion.",
        "Inspect old and new source rows side by side.",
        "review",
        "manual_review",
    )


def _risk_breakdown(**inputs: Any) -> dict[str, Any]:
    actual_mismatches = inputs["actual_mismatches"]
    critical_financial = inputs["critical_financial"]
    identity_failures = inputs["identity_failures"]
    missing_total = inputs["missing_total"]
    duplicate_labels = inputs["duplicate_labels"]
    polluted_labels = inputs["polluted_labels"]
    low_confidence = inputs["low_confidence"]
    merged_rows = inputs["merged_rows"]
    hierarchy_gaps = inputs["hierarchy_gaps"]
    extraction_coverage = inputs["extraction_coverage"]
    extraction_confidence = inputs["extraction_confidence"]
    if critical_financial or identity_failures:
        category, level, score, rationale = "HIGH_FINANCIAL_RISK", "HIGH", 85, "Critical carry-forward mismatch or accounting identity failure detected."
    elif actual_mismatches:
        category, level, score, rationale = "HIGH_FINANCIAL_RISK", "HIGH", 80, "Actual value differences were detected."
    elif extraction_coverage < 80 or extraction_confidence < 0.75 or missing_total >= 5:
        category, level, score, rationale = "HIGH_EXTRACTION_RISK", "HIGH", 60, "Compared values match, but extraction coverage or confidence needs review."
    elif missing_total or duplicate_labels or polluted_labels or low_confidence or merged_rows or hierarchy_gaps:
        category, level, score, rationale = "MEDIUM_STRUCTURAL_RISK", "MEDIUM", 35, "No financial mismatch found, but structural extraction or label issues require review."
    else:
        category, level, score, rationale = "LOW", "LOW", 5, "All compared values match and coverage is high."
    return {"category": category, "level": level, "score": score, "rationale": rationale, "inputs": inputs}


def _verdict(risk: dict[str, Any], actual_mismatches: int, critical_financial: int, identity_failures: int, missing_total: int, structural_issues: int, coverage: float, confidence: float) -> dict[str, str]:
    if actual_mismatches or critical_financial or identity_failures:
        return {"label": "FAIL", "reason": "Actual carry-forward mismatch or critical accounting identity issue detected."}
    if missing_total or structural_issues or coverage < 95 or confidence < 0.85:
        return {"label": "NEEDS REVIEW", "reason": "Financial values compared successfully, but some rows require extraction or label review."}
    return {"label": "PASS", "reason": "No financial mismatches, no critical anomalies, and extraction coverage and confidence are high."}


def _why_verdict(verdict: dict[str, str], mismatches: int, critical: int, missing: int, structural: int) -> dict[str, Any]:
    passed = []
    needs_review = []
    if mismatches == 0:
        passed.append("No actual carry-forward value differences were detected.")
    if critical == 0:
        passed.append("No critical accounting errors were detected.")
    if missing:
        needs_review.append(f"{missing} accounts are missing or unpaired and need extraction or label review.")
    if structural:
        needs_review.append(f"{structural} structural extraction issues were detected.")
    return {"verdict": verdict["label"], "reason": verdict["reason"], "passed": passed, "needs_review": needs_review, "issue_type": "financial" if mismatches or critical else ("extraction_structural" if needs_review else "none")}


def _side_evidence(
    evidence: Evidence | None,
    label: str | None,
    value: float | int | None,
    statement: str,
    engine: str,
    document_id: str | None,
    value_role: str,
) -> dict[str, Any]:
    if evidence is None:
        return {
            "document_id": document_id,
            "file_name": document_id,
            "page": None,
            "page_number": None,
            "statement": statement,
            "statement_name": statement,
            "section": statement,
            "section_name": statement,
            "raw_text": label or "",
            "raw_line": label or "",
            "bounding_box": None,
            "bbox_value": None,
            "value": value,
            "value_used": value,
            "value_role": value_role,
            "extraction_method": engine,
            "extraction_engine": engine,
        }
    payload = evidence.model_dump(mode="json")
    payload.setdefault("document_id", document_id)
    payload.setdefault("file_name", payload.get("document_id") or document_id)
    payload.setdefault("page_number", payload.get("page"))
    payload.setdefault("statement", payload.get("statement_name") or statement)
    payload.setdefault("statement_name", statement)
    payload.setdefault("section", payload.get("section_name") or statement)
    payload.setdefault("section_name", statement)
    payload.setdefault("raw_text", label or "")
    payload.setdefault("raw_line", payload.get("raw_text") or label or "")
    payload["value_role"] = value_role
    payload["value"] = value
    payload["value_used"] = value
    payload["bbox_value"] = payload.get("bbox_current") if value_role == "current" else payload.get("bbox_previous")
    payload.setdefault("bounding_box", payload.get("bbox_value") or payload.get("bbox_row") or payload.get("bbox_label"))
    payload.setdefault("extraction_engine", payload.get("extraction_method") or engine)
    return payload


def _unique_current_keys(document: FinancialDocument) -> set[tuple[str, str]]:
    return {(name, row.canonical_label) for name, statement in document.statements.items() for row in statement.rows if row.canonical_label and row.current_value is not None}


def _unique_previous_keys(document: FinancialDocument) -> set[tuple[str, str]]:
    return {(name, row.canonical_label) for name, statement in document.statements.items() for row in statement.rows if row.canonical_label and row.previous_value is not None}


def _polluted_label_count(comparisons: list[ComparisonResult]) -> int:
    labels = [item.old_label or "" for item in comparisons] + [item.new_label or "" for item in comparisons]
    return sum(1 for label in labels if pollution_reasons(label))


def _merged_row_count(comparisons: list[ComparisonResult]) -> int:
    return sum(1 for item in comparisons if _looks_like_merged_row(item))


def _hierarchy_gap_count(comparisons: list[ComparisonResult]) -> int:
    total = 0
    for item in comparisons:
        normalized = normalize_label(item.canonical_label)
        if item.status in DUPLICATE_STATUSES and "__" not in normalized and normalized in {"capital", "regularisation_sommes_distribuables", "regularisation_sommes_non_distribuables", "en_debut_exercice", "en_fin_exercice"}:
            total += 1
    return total


def _is_critical_financial_mismatch(item: ComparisonResult) -> bool:
    if item.status not in MISMATCH_STATUSES:
        return False
    normalized = normalize_label(item.canonical_label)
    return item.severity == Severity.CRITICAL or any(key in normalized for key in CRITICAL_KEYS)


def _average_confidence(documents: list[FinancialDocument]) -> float:
    values = [document.confidence for document in documents]
    return round(sum(values) / len(values), 4) if values else 0.0


def _accounting_health(financial_consistency: float, actual_mismatches: int, critical_accounting_errors: int) -> dict[str, Any]:
    if critical_accounting_errors:
        return {"label": "FAIL", "score": 0, "reason": "Critical accounting totals or identities failed deterministic verification."}
    if actual_mismatches or financial_consistency < 100:
        return {"label": "NEEDS_REVIEW", "score": round(financial_consistency, 2), "reason": "Compared values are not fully consistent and need accountant review."}
    return {"label": "PASS", "score": round(financial_consistency, 2), "reason": "Compared values and critical accounting checks passed."}


def _issue_classification(item: ComparisonResult, evidence_type: str, polluted: list[str]) -> str:
    if item.status in MISMATCH_STATUSES:
        return "accounting_issue"
    if item.status in DUPLICATE_STATUSES:
        return "structural_extraction_issue"
    if polluted:
        return "polluted_label"
    if evidence_type in {"missing_old_current", "missing_new_comparative", "low_confidence_parse", "review"}:
        return "extraction_issue"
    return "matched_value"


def _hierarchy_path(item: ComparisonResult) -> str:
    normalized = normalize_label(item.canonical_label)
    if "__" in normalized:
        statement, account = normalized.split("__", 1)
        return f"{statement}.{account.replace('_', '.')}"
    return f"{item.statement}.{normalized.replace('_', '.')}" if normalized else item.statement


def _looks_like_merged_row(item: ComparisonResult) -> bool:
    labels = [item.old_label or "", item.new_label or ""]
    return any(sum(1 for fragment in EMBEDDED_TITLE_KEYS if fragment in normalize_label(label)) >= 2 for label in labels if label)


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


def _issue_type(item: ComparisonResult, evidence_type: str, polluted: list[str]) -> str:
    if item.status in MISMATCH_STATUSES:
        return "financial_mismatch"
    if item.status in DUPLICATE_STATUSES:
        return "duplicate_label"
    if polluted:
        return "polluted_label"
    if evidence_type == "low_confidence_parse":
        return "low_confidence"
    if evidence_type in {"missing_old_current", "missing_new_comparative"}:
        return "extraction_missing"
    if item.severity == Severity.CRITICAL and item.status in STRUCTURAL_STATUSES:
        return "accounting_identity_failure"
    return "ok"


def _status_group(item: ComparisonResult, issue_type: str) -> str:
    if item.status in OK_STATUSES:
        return "matched"
    if issue_type == "financial_mismatch":
        return "financial"
    if issue_type in {"duplicate_label", "polluted_label", "accounting_identity_failure"}:
        return "structural"
    return "extraction"
