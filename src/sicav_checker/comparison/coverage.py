from __future__ import annotations

from sicav_checker.models import ComparisonResult, FinancialDocument, Status


def count_financial_lines(document: FinancialDocument) -> int:
    """Count extracted rows that contain at least one financial value."""
    return sum(
        1
        for statement in document.statements.values()
        for row in statement.rows
        if row.current_value is not None or row.previous_value is not None
    )


def count_ignored_lines(document: FinancialDocument) -> int:
    """Count extracted rows that cannot participate in numeric carry-forward checks."""
    return sum(
        1
        for statement in document.statements.values()
        for row in statement.rows
        if row.current_value is None and row.previous_value is None
    )


def comparison_coverage(old_document: FinancialDocument, new_document: FinancialDocument, comparisons: list[ComparisonResult]) -> dict[str, float | int]:
    old_lines = count_financial_lines(old_document)
    new_lines = count_financial_lines(new_document)
    comparable_lines = len(comparisons)
    denominator = max(old_lines, new_lines)
    coverage = round((comparable_lines / denominator) * 100, 2) if denominator else 0.0
    matched = sum(1 for item in comparisons if item.status in {Status.OK, Status.LABEL_RENAMED})
    mismatched = sum(1 for item in comparisons if item.status == Status.MISMATCH)
    missing_old = sum(1 for item in comparisons if item.status == Status.MISSING_IN_OLD)
    missing_new = sum(1 for item in comparisons if item.status == Status.MISSING_IN_NEW)
    ignored = count_ignored_lines(old_document) + count_ignored_lines(new_document)
    return {
        "old_extracted_lines": old_lines,
        "new_extracted_lines": new_lines,
        "comparable_lines": comparable_lines,
        "matched_lines": matched,
        "mismatched_lines": mismatched,
        "missing_in_old": missing_old,
        "missing_in_new": missing_new,
        "ignored_lines": ignored,
        "comparison_coverage_percentage": coverage,
    }
