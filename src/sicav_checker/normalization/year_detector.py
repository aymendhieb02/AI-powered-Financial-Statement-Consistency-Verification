from __future__ import annotations

import re
from pathlib import Path


YEAR_RE = re.compile(r"(20\d{2})")
BILAN_RE = re.compile(r"BILAN\s+ARRETE\s+AU\s+31\s+DECEMBRE\s+(20\d{2})", re.IGNORECASE)


def detect_year_from_filename(path: str | Path) -> int | None:
    match = YEAR_RE.search(Path(path).name)
    return int(match.group(1)) if match else None


def detect_year_from_text(text: str) -> int | None:
    bilan_match = BILAN_RE.search(text)
    if bilan_match:
        return int(bilan_match.group(1))
    match = YEAR_RE.search(text)
    return int(match.group(1)) if match else None


def detect_document_year(path: str | Path, text: str = "") -> int:
    year = detect_year_from_filename(path) or detect_year_from_text(text)
    if year is None:
        raise ValueError(f"Unable to detect document year for {path}")
    return year
