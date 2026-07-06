from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sicav_checker.core.logging import logger
from sicav_checker.extraction.section_detector import detect_sections


@dataclass(frozen=True)
class VisualLine:
    page: int
    top: float
    text: str


def extract_layout_sections(path: str | Path) -> tuple[dict[str, str], str]:
    pdf_path = Path(path)
    lines = extract_visual_lines(pdf_path)
    raw_text = "\n".join(line.text for line in lines)
    return detect_sections(raw_text), raw_text


def extract_visual_lines(path: str | Path, y_tolerance: float = 3.0) -> list[VisualLine]:
    pdf_path = Path(path)
    try:
        import pdfplumber
    except ImportError:
        logger.warning("pdfplumber is not installed; layout-aware extraction unavailable for {}", pdf_path)
        return []

    visual_lines: list[VisualLine] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_index, page in enumerate(pdf.pages, start=1):
                words = page.extract_words(x_tolerance=2, y_tolerance=3, keep_blank_chars=False, use_text_flow=False) or []
                visual_lines.extend(_group_words(page_index, words, y_tolerance=y_tolerance))
    except Exception as exc:
        logger.warning("Layout-aware extraction failed for {}: {}", pdf_path, exc)
        return []
    return visual_lines


def _group_words(page: int, words: list[dict], y_tolerance: float) -> list[VisualLine]:
    rows: list[list[dict]] = []
    for word in sorted(words, key=lambda item: (float(item.get("top", 0)), float(item.get("x0", 0)))):
        top = float(word.get("top", 0))
        if not rows or abs(float(rows[-1][0].get("top", 0)) - top) > y_tolerance:
            rows.append([word])
        else:
            rows[-1].append(word)

    lines: list[VisualLine] = []
    for row in rows:
        ordered = sorted(row, key=lambda item: float(item.get("x0", 0)))
        text = " ".join(str(item.get("text", "")).strip() for item in ordered if str(item.get("text", "")).strip())
        if text:
            lines.append(VisualLine(page=page, top=float(row[0].get("top", 0)), text=" ".join(text.split())))
    return lines
