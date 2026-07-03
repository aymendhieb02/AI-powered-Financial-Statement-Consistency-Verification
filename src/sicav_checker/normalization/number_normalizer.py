from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation


EMPTY_MARKERS = {"", "-", "\u2014", "\u2013", "na", "n/a", "neant", "neant"}


def normalize_number(value: object) -> int | float | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value

    text = str(value).strip().replace("\u00a0", " ")
    if text.lower() in EMPTY_MARKERS:
        return None

    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1]
    if text.startswith("-"):
        negative = True
        text = text[1:]

    text = re.sub(r"[^\d,.\s]", "", text).strip()
    text = re.sub(r"\s+", "", text)
    if not text:
        return None

    if "," in text and "." in text:
        decimal_sep = "," if text.rfind(",") > text.rfind(".") else "."
        thousands_sep = "." if decimal_sep == "," else ","
        text = text.replace(thousands_sep, "").replace(decimal_sep, ".")
    elif "," in text:
        parts = text.split(",")
        text = text.replace(",", "") if len(parts) > 2 else text.replace(",", ".")
    elif "." in text:
        parts = text.split(".")
        text = text.replace(".", "") if len(parts) > 2 else text

    try:
        number = Decimal(text)
    except InvalidOperation:
        return None

    if negative:
        number = -number
    if number == number.to_integral_value():
        return int(number)
    return float(number)