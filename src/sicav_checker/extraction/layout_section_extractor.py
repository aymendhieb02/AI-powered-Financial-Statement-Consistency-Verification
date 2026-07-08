from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field
from pathlib import Path

from sicav_checker.core.logging import logger
from sicav_checker.extraction.section_detector import detect_section_candidates, detect_sections


@dataclass(frozen=True)
class VisualWord:
    text: str
    x0: float
    top: float
    x1: float
    bottom: float


@dataclass(frozen=True)
class VisualLine:
    page: int
    top: float
    text: str
    x0: float
    x1: float
    bottom: float
    words: tuple[VisualWord, ...] = field(default_factory=tuple)

    @property
    def row_bbox(self) -> tuple[float, float, float, float]:
        return (self.x0, self.top, self.x1, self.bottom)


def extract_layout_sections(path: str | Path) -> tuple[dict[str, str], str]:
    sections, raw_text, _ = extract_layout_sections_with_metadata(path)
    return sections, raw_text


def extract_layout_sections_with_metadata(path: str | Path) -> tuple[dict[str, str], str, dict[str, list[VisualLine]]]:
    pdf_path = Path(path)
    lines = extract_visual_lines(pdf_path)
    raw_text = "\n".join(line.text for line in lines)
    sections = detect_sections(raw_text)
    section_lines = _section_lines(lines, raw_text)
    return sections, raw_text, section_lines


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
        visual_words = tuple(
            VisualWord(
                text=str(item.get("text", "")).strip(),
                x0=float(item.get("x0", 0)),
                top=float(item.get("top", 0)),
                x1=float(item.get("x1", 0)),
                bottom=float(item.get("bottom", 0)),
            )
            for item in ordered
            if str(item.get("text", "")).strip()
        )
        text = " ".join(word.text for word in visual_words if word.text)
        if not text:
            continue
        lines.append(
            VisualLine(
                page=page,
                top=float(row[0].get("top", 0)),
                text=" ".join(text.split()),
                x0=min(word.x0 for word in visual_words),
                x1=max(word.x1 for word in visual_words),
                bottom=max(word.bottom for word in visual_words),
                words=visual_words,
            )
        )
    return lines


def _section_lines(lines: list[VisualLine], raw_text: str) -> dict[str, list[VisualLine]]:
    if not lines or not raw_text:
        return {}
    candidates = detect_section_candidates(raw_text)
    if not candidates:
        return {}

    offsets: list[int] = []
    cursor = 0
    for line in lines:
        offsets.append(cursor)
        cursor += len(line.text) + 1

    section_map: dict[str, list[VisualLine]] = {}
    for index, candidate in enumerate(candidates):
        start_line = _offset_to_line(offsets, candidate.offset)
        end_offset = candidates[index + 1].offset if index + 1 < len(candidates) else len(raw_text)
        end_line = _offset_to_line(offsets, end_offset)
        slice_end = end_line if end_offset < len(raw_text) else len(lines)
        if candidate.key not in section_map:
            section_map[candidate.key] = lines[start_line:slice_end]
    return section_map


def _offset_to_line(offsets: list[int], offset: int) -> int:
    if not offsets:
        return 0
    return max(0, min(len(offsets) - 1, bisect_right(offsets, offset) - 1))
