from __future__ import annotations

from enum import Enum
from typing import Any

from sicav_checker.comparison.coverage import count_financial_lines
from sicav_checker.domain.models import FinancialDocument, Severity, ValidationResult

REQUIRED_STATEMENTS = {"bilan", "etat_resultat", "etat_variation_actif_net"}


class ExtractionStatus(str, Enum):
    GOOD = "GOOD"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class ComparisonStatus(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class AccountingStatus(str, Enum):
    PASS = "PASS"
    NEEDS_REVIEW = "NEEDS REVIEW"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class OverallVerdict(str, Enum):
    PASS = "PASS"
    NEEDS_REVIEW = "NEEDS REVIEW"
    FAIL = "FAIL"


def build_decision_summary(
    documents: list[FinancialDocument],
    metrics: dict[str, Any],
    validations: list[ValidationResult] | None = None,
) -> dict[str, Any]:
    validations = validations or []
    extraction = assess_extraction(documents)
    comparison = assess_comparison(extraction, metrics)
    accounting = assess_accounting(comparison, metrics, validations)
    overall = assess_overall(extraction, comparison, accounting)
    why_verdict = build_verdict_explanation(extraction, comparison, accounting, overall)
    return {
        "extraction": extraction,
        "comparison": comparison,
        "accounting": accounting,
        "overall": overall,
        "why_verdict": why_verdict,
    }


def assess_extraction(documents: list[FinancialDocument]) -> dict[str, Any]:
    if not documents:
        return {
            "status": ExtractionStatus.FAILED.value,
            "reason": "No extracted documents are available.",
            "documents": [],
            "summary": {"documents": 0, "rows": 0, "required_statements_found": 0, "confidence": None},
        }

    per_document: list[dict[str, Any]] = []
    statuses: list[ExtractionStatus] = []
    for document in documents:
        statements_found = len(REQUIRED_STATEMENTS.intersection(document.statements.keys()))
        rows = count_financial_lines(document)
        confidence = float(document.confidence or 0.0)
        missing_statements = sorted(REQUIRED_STATEMENTS.difference(document.statements.keys()))
        if rows == 0 or statements_found == 0:
            status = ExtractionStatus.FAILED
            reason = "No comparable financial statements could be extracted."
        elif statements_found == len(REQUIRED_STATEMENTS) and rows >= 40 and confidence >= 0.85:
            status = ExtractionStatus.GOOD
            reason = "All required statements found with strong row coverage and confidence."
        else:
            status = ExtractionStatus.PARTIAL
            if statements_found < len(REQUIRED_STATEMENTS):
                reason = f"Only {statements_found} of {len(REQUIRED_STATEMENTS)} required statements were found."
            elif rows < 40:
                reason = f"Only {rows} financial rows were extracted, which is below the expected range."
            else:
                reason = f"Extraction confidence is {confidence * 100:.1f}%, so manual review is recommended."
        statuses.append(status)
        per_document.append(
            {
                "source_file": document.source_file,
                "year": document.document_year,
                "status": status.value,
                "reason": reason,
                "rows": rows,
                "required_statements_found": statements_found,
                "missing_statements": missing_statements,
                "confidence": round(confidence * 100, 2),
            }
        )

    if any(status == ExtractionStatus.FAILED for status in statuses):
        aggregate = ExtractionStatus.FAILED
        reason = "At least one document could not be extracted into comparable financial statements."
    elif any(status == ExtractionStatus.PARTIAL for status in statuses):
        aggregate = ExtractionStatus.PARTIAL
        reason = "Some documents were extracted only partially, so comparison completeness is limited."
    else:
        aggregate = ExtractionStatus.GOOD
        reason = "All required statements found across the uploaded documents."

    return {
        "status": aggregate.value,
        "reason": reason,
        "documents": per_document,
        "summary": {
            "documents": len(documents),
            "rows": sum(item["rows"] for item in per_document),
            "required_statements_found": min((item["required_statements_found"] for item in per_document), default=0),
            "confidence": round(sum(item["confidence"] for item in per_document) / len(per_document), 2) if per_document else None,
        },
    }


def assess_comparison(extraction: dict[str, Any], metrics: dict[str, Any]) -> dict[str, Any]:
    extraction_status = extraction["status"]
    expected_accounts = int(metrics.get("extraction_coverage_denominator", 0) or 0)
    paired_accounts = int(metrics.get("extraction_coverage_numerator", 0) or 0)
    compared_values = int(metrics.get("financial_consistency_denominator", 0) or 0)
    missing_accounts = int(metrics.get("missing_accounts", 0) or 0)
    duplicate_labels = int(metrics.get("duplicate_labels", 0) or 0)
    coverage = float(metrics.get("extraction_coverage", 0.0) or 0.0)

    if extraction_status == ExtractionStatus.FAILED.value or expected_accounts == 0 or compared_values == 0:
        status = ComparisonStatus.FAILED
        reason = "Comparison could not be completed because extraction did not produce enough comparable data."
    elif extraction_status == ExtractionStatus.GOOD.value and missing_accounts == 0 and duplicate_labels == 0 and coverage >= 95:
        status = ComparisonStatus.COMPLETE
        reason = f"{paired_accounts} of {expected_accounts} expected accounts were paired successfully."
    else:
        status = ComparisonStatus.PARTIAL
        reason = f"Only {paired_accounts} of {expected_accounts} expected accounts were paired, so comparison completeness is limited."

    return {
        "status": status.value,
        "reason": reason,
        "summary": {
            "expected_accounts": expected_accounts,
            "paired_accounts": paired_accounts,
            "compared_values": compared_values,
            "missing_accounts": missing_accounts,
            "duplicate_labels": duplicate_labels,
            "coverage": coverage,
        },
    }


def assess_accounting(comparison: dict[str, Any], metrics: dict[str, Any], validations: list[ValidationResult]) -> dict[str, Any]:
    comparison_status = comparison["status"]
    actual_mismatches = int(metrics.get("actual_mismatches", 0) or 0)
    critical_errors = int(metrics.get("critical_accounting_errors", 0) or 0)
    financial_consistency = float(metrics.get("financial_consistency", 0.0) or 0.0)
    identity_failures = [item for item in validations if item.severity == Severity.CRITICAL and getattr(item.status, "value", str(item.status)) not in {"OK", "carry_forward_ok"}]

    if comparison_status != ComparisonStatus.COMPLETE.value:
        status = AccountingStatus.UNKNOWN
        reason = "Comparison is incomplete, so accounting correctness cannot be concluded yet."
    elif actual_mismatches > 0 or critical_errors > 0 or identity_failures:
        status = AccountingStatus.FAIL
        reason = "A real financial inconsistency or critical accounting identity failure was detected."
    elif financial_consistency == 100.0:
        status = AccountingStatus.PASS
        reason = "All compared carry-forward values and critical accounting checks passed."
    else:
        status = AccountingStatus.NEEDS_REVIEW
        reason = "Accounting checks completed, but some deterministic results still require review."

    return {
        "status": status.value,
        "reason": reason,
        "summary": {
            "financial_consistency": financial_consistency,
            "actual_mismatches": actual_mismatches,
            "critical_accounting_errors": critical_errors,
            "identity_failures": len(identity_failures),
        },
    }


def assess_overall(extraction: dict[str, Any], comparison: dict[str, Any], accounting: dict[str, Any]) -> dict[str, Any]:
    if accounting["status"] == AccountingStatus.FAIL.value:
        verdict = OverallVerdict.FAIL
        reason = "Actual financial inconsistency detected."
    elif extraction["status"] == ExtractionStatus.GOOD.value and comparison["status"] == ComparisonStatus.COMPLETE.value and accounting["status"] == AccountingStatus.PASS.value:
        verdict = OverallVerdict.PASS
        reason = "Extraction, comparison, and accounting checks all completed successfully."
    else:
        verdict = OverallVerdict.NEEDS_REVIEW
        if extraction["status"] != ExtractionStatus.GOOD.value:
            reason = "Comparison cannot be completed reliably because extraction quality is insufficient."
        elif comparison["status"] != ComparisonStatus.COMPLETE.value:
            reason = "Comparison remains incomplete because too many accounts could not be paired."
        else:
            reason = "The result requires accountant review before a final conclusion."
    return {"status": verdict.value, "reason": reason}


def build_verdict_explanation(extraction: dict[str, Any], comparison: dict[str, Any], accounting: dict[str, Any], overall: dict[str, Any]) -> dict[str, Any]:
    return {
        "verdict": overall["status"],
        "reason": overall["reason"],
        "passed": [
            item
            for item in [
                f"Extraction: {extraction['reason']}" if extraction["status"] == ExtractionStatus.GOOD.value else "",
                f"Comparison: {comparison['reason']}" if comparison["status"] == ComparisonStatus.COMPLETE.value else "",
                f"Accounting: {accounting['reason']}" if accounting["status"] == AccountingStatus.PASS.value else "",
            ]
            if item
        ],
        "needs_review": [
            item
            for item in [
                f"Extraction: {extraction['reason']}" if extraction["status"] != ExtractionStatus.GOOD.value else "",
                f"Comparison: {comparison['reason']}" if comparison["status"] != ComparisonStatus.COMPLETE.value else "",
                f"Accounting: {accounting['reason']}" if accounting["status"] in {AccountingStatus.UNKNOWN.value, AccountingStatus.NEEDS_REVIEW.value, AccountingStatus.FAIL.value} else "",
            ]
            if item
        ],
        "issue_type": "financial" if accounting["status"] == AccountingStatus.FAIL.value else ("extraction_structural" if extraction["status"] != ExtractionStatus.GOOD.value or comparison["status"] != ComparisonStatus.COMPLETE.value else "none"),
        "engines": {
            "extraction": extraction,
            "comparison": comparison,
            "accounting": accounting,
        },
    }
