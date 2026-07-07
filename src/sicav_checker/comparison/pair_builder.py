from __future__ import annotations

from collections import Counter
from difflib import SequenceMatcher

from sicav_checker.models import StatementRow


def build_valid_pairs(years: list[int] | set[int]) -> list[tuple[int, int]]:
    available = sorted({year for year in years if isinstance(year, int)})
    return [(year, year + 1) for year in available if year + 1 in available]


def build_row_pairs(
    old_rows: list[StatementRow],
    new_rows: list[StatementRow],
    fuzzy_threshold: float = 0.86,
) -> tuple[list[tuple[StatementRow, StatementRow, float]], list[StatementRow], list[StatementRow]]:
    """
    Pair old and new statement rows by canonical label.

    Duplicate canonical labels are deliberately quarantined in the unmatched
    outputs so callers can preserve evidence and raise duplicate anomalies
    instead of silently comparing the first duplicate row.

    Returns:
        matched_pairs: [(old_row, new_row, confidence)]
        missing_old_rows: rows present in old but not matched in new
        added_new_rows: rows present in new but not matched in old
    """

    matched: list[tuple[StatementRow, StatementRow, float]] = []
    old_duplicate_keys = _duplicate_keys(old_rows)
    new_duplicate_keys = _duplicate_keys(new_rows)
    quarantined_old = [row for row in old_rows if row.canonical_label in old_duplicate_keys]
    quarantined_new = [row for row in new_rows if row.canonical_label in new_duplicate_keys]
    unmatched_old = [row for row in old_rows if row.canonical_label not in old_duplicate_keys]
    unmatched_new = [row for row in new_rows if row.canonical_label not in new_duplicate_keys]

    # 1. Exact canonical match
    new_by_label: dict[str, StatementRow] = {row.canonical_label: row for row in unmatched_new}
    still_old: list[StatementRow] = []

    for old_row in unmatched_old:
        new_row = new_by_label.get(old_row.canonical_label)
        if new_row:
            matched.append((old_row, new_row, 1.0))
            unmatched_new.remove(new_row)
        else:
            still_old.append(old_row)

    unmatched_old = still_old

    # 2. Fuzzy canonical match
    still_old = []

    for old_row in unmatched_old:
        best_row = None
        best_score = 0.0

        for new_row in unmatched_new:
            score = SequenceMatcher(
                None,
                old_row.canonical_label,
                new_row.canonical_label,
            ).ratio()

            if score > best_score:
                best_score = score
                best_row = new_row

        if best_row is not None and best_score >= fuzzy_threshold:
            matched.append((old_row, best_row, best_score))
            unmatched_new.remove(best_row)
        else:
            still_old.append(old_row)

    return matched, quarantined_old + still_old, quarantined_new + unmatched_new


def _duplicate_keys(rows: list[StatementRow]) -> set[str]:
    counts = Counter(row.canonical_label for row in rows if row.canonical_label)
    return {key for key, count in counts.items() if count > 1}
