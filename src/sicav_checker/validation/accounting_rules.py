from __future__ import annotations

from sicav_checker.models import StatementRow


def value(rows: dict[str, StatementRow], label: str) -> float | int | None:
    row = rows.get(label)
    return row.current_value if row else None
