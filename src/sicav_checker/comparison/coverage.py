from __future__ import annotations

from sicav_checker.models import ComparisonResult, FinancialDocument, Status

OK_STATUSES = {Status.OK, Status.CARRY_FORWARD_OK, Status.LABEL_RENAMED}
MISMATCH_STATUSES = {Status.MISMATCH, Status.CARRY_FORWARD_MISMATCH}
MISSING_OLD_STATUSES = {Status.MISSING_IN_OLD, Status.MISSING_IN_OLD_CURRENT}
MISSING_NEW_STATUSES = {Status.MISSING_IN_NEW, Status.MISSING_IN_NEW_COMPARATIVE}
DUPLICATE_STATUSES = {Status.DUPLICATE_LABEL}


def is_ok_status(status: Status | str) -> bool:
    return status in OK_STATUSES or str(status) in {str(item) for item in OK_STATUSES}


def is_anomaly_status(status: Status | str) -> bool:
    return not is_ok_status(status)


def count_financial_lines(document: FinancialDocument) -> int:
    return sum(
        1
        for statement in document.statements.values()
        for row in statement.rows
        if row.current_value is not None or row.previous_value is not None
    )


def count_ignored_lines(document: FinancialDocument) -> int:
    return sum(
        1
        for statement in document.statements.values()
        for row in statement.rows
        if row.current_value is None and row.previous_value is None
    )


def comparison_coverage(old_document: FinancialDocument, new_document: FinancialDocument, comparisons: list[ComparisonResult]) -> dict[str, float | int]:
    old_keys = _unique_current_keys(old_document)
    new_keys = _unique_previous_keys(new_document)
    expected_keys = old_keys | new_keys
    matched_keys = {
        (item.statement, item.canonical_label)
        for item in comparisons
        if (item.old_label is not None and item.new_label is not None) or item.status in DUPLICATE_STATUSES
    }
    denominator = len(expected_keys)
    raw_matched_count = len(matched_keys)
    capped_matched_count = min(raw_matched_count, denominator) if denominator else 0
    extra_pairings = max(0, raw_matched_count - denominator)
    coverage = round((capped_matched_count / denominator) * 100, 2) if denominator else 0.0
    matched = sum(1 for item in comparisons if item.status in OK_STATUSES)
    mismatched = sum(1 for item in comparisons if item.status in MISMATCH_STATUSES)
    missing_old = sum(1 for item in comparisons if item.status in MISSING_OLD_STATUSES)
    missing_new = sum(1 for item in comparisons if item.status in MISSING_NEW_STATUSES)
    ignored = count_ignored_lines(old_document) + count_ignored_lines(new_document)
    return {
        "old_extracted_lines": count_financial_lines(old_document),
        "new_extracted_lines": count_financial_lines(new_document),
        "comparable_lines": denominator,
        "matched_lines": matched,
        "paired_unique_accounts": capped_matched_count,
        "paired_unique_accounts_raw": raw_matched_count,
        "extra_pairings": extra_pairings,
        "mismatched_lines": mismatched,
        "missing_in_old": missing_old,
        "missing_in_new": missing_new,
        "ignored_lines": ignored,
        "comparison_coverage_percentage": coverage,
    }


def _unique_current_keys(document: FinancialDocument) -> set[tuple[str, str]]:
    return {
        (statement_name, row.canonical_label)
        for statement_name, statement in document.statements.items()
        for row in statement.rows
        if row.canonical_label and row.current_value is not None
    }


def _unique_previous_keys(document: FinancialDocument) -> set[tuple[str, str]]:
    return {
        (statement_name, row.canonical_label)
        for statement_name, statement in document.statements.items()
        for row in statement.rows
        if row.canonical_label and row.previous_value is not None
    }
