from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation


EMPTY_MARKERS = {
    "",
    "-",
    "—",
    "–",
    "na",
    "n/a",
    "néant",
    "neant",
    "nil",
}


def normalize_number(value: object) -> int | float | None:
    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return value

    text = str(value).strip().replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)

    if text.lower() in EMPTY_MARKERS:
        return None

    negative = False

    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()

    if text.startswith("-"):
        negative = True
        text = text[1:].strip()

    # Keep digits and separators only.
    # Percent sign is ignored: "5.96%" -> 5.96
    text = re.sub(r"[^\d,.\s]", "", text).strip()
    text = re.sub(r"\s+", "", text)

    if not text:
        return None

    text = _normalize_separators(text)

    try:
        number = Decimal(text)
    except InvalidOperation:
        return None

    if negative:
        number = -number

    if number == number.to_integral_value():
        return int(number)

    return float(number)


def _normalize_separators(text: str) -> str:
    """
    Converts common formats into Decimal-compatible format.

    Examples:
    7 826 775 -> 7826775
    7.826.775 -> 7826775
    7,826,775 -> 7826775
    108.164 -> 108.164
    5.96% -> 5.96
    1,25 -> 1.25
    """

    if "," in text and "." in text:
        decimal_sep = "," if text.rfind(",") > text.rfind(".") else "."
        thousands_sep = "." if decimal_sep == "," else ","
        return text.replace(thousands_sep, "").replace(decimal_sep, ".")

    if "," in text:
        parts = text.split(",")

        if len(parts) > 2:
            return text.replace(",", "")

        # 1,25 -> decimal
        # 7,701 -> ambiguous, kept as decimal for now
        return text.replace(",", ".")

    if "." in text:
        parts = text.split(".")

        if len(parts) > 2:
            return text.replace(".", "")

        # 108.164 is treated as decimal.
        return text

    return text