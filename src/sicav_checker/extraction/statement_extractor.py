from __future__ import annotations

import re
from pathlib import Path

from sicav_checker.core.logging import logger
from sicav_checker.extraction.layout_section_extractor import extract_layout_sections
from sicav_checker.extraction.section_detector import SECTION_ORDER, candidate_heading_lines, detect_sections
from sicav_checker.extraction.text_extractor import extract_text
from sicav_checker.models import ExtractedDocument, Statement, StatementRow
from sicav_checker.normalization.label_normalizer import normalize_label
from sicav_checker.normalization.number_normalizer import normalize_number
from sicav_checker.normalization.year_detector import detect_document_year


COMPARABLE_STATEMENTS = ("bilan", "etat_resultat", "etat_variation_actif_net")


def extract_document(path: str | Path) -> ExtractedDocument:
    pdf_path = Path(path)
    sections, text, method = _extract_sections(pdf_path)
    _write_debug_outputs(pdf_path, text, sections)
    year = detect_document_year(pdf_path, text)
    _warn_missing_sections(pdf_path, text, sections)

    statements: dict[str, Statement] = {}
    for name in COMPARABLE_STATEMENTS:
        rows = extract_rows(sections.get(name, ""), statement_name=name)
        logger.info("Statement extraction: file={} section={} rows={}", pdf_path.name, name, len(rows))
        if rows:
            statements[name] = Statement(name=name, rows=rows)

    confidence = 0.9 if statements else 0.4
    return ExtractedDocument(
        document_year=year,
        source_file=str(pdf_path),
        extraction_method=method,
        statements=statements,
        pages=[],
        confidence=confidence,
    )


def _extract_sections(pdf_path: Path) -> tuple[dict[str, str], str, str]:
    layout_sections, layout_text = extract_layout_sections(pdf_path)
    if any(section in layout_sections for section in COMPARABLE_STATEMENTS):
        return layout_sections, layout_text, "pdfplumber_layout"

    text, method = extract_text(pdf_path)
    text_sections = detect_sections(text)
    return text_sections, text, method


def _write_debug_outputs(pdf_path: Path, text: str, sections: dict[str, str]) -> None:
    debug_dir = Path("logs") / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    (debug_dir / f"{pdf_path.stem}_raw_text.txt").write_text(text, encoding="utf-8")
    for section_name in SECTION_ORDER:
        if section_name in sections:
            (debug_dir / f"{pdf_path.stem}_section_{section_name}.txt").write_text(sections[section_name], encoding="utf-8")


def _warn_missing_sections(pdf_path: Path, text: str, sections: dict[str, str]) -> None:
    missing = [section for section in COMPARABLE_STATEMENTS if section not in sections]
    if not missing:
        return
    logger.warning(
        "Comparable sections missing file={} missing={} detected={} candidate_headings={}",
        pdf_path.name,
        missing,
        list(sections),
        candidate_heading_lines(text),
    )


def extract_rows(section_text: str, statement_name: str = "") -> list[StatementRow]:
    rows: list[StatementRow] = []
    statement_key = normalize_label(statement_name) or statement_name or "statement"

    pending_label = ""
    for raw_line in section_text.splitlines():
        clean = " ".join(raw_line.strip().split())
        if not clean:
            continue

        parsed = parse_financial_row(clean)
        if parsed is None:
            if _looks_like_label_continuation(clean):
                pending_label = f"{pending_label} {clean}".strip()
            continue

        label, current_raw, previous_raw = parsed
        if pending_label and len(label.split()) <= 3:
            label = f"{pending_label} {label}".strip()
        pending_label = ""

        if is_bad_label(label):
            continue

        canonical = normalize_label(label) or f"{statement_key}__unknown_line_{len(rows) + 1}"
        rows.append(
            StatementRow(
                label=label,
                canonical_label=canonical,
                current_value=normalize_number(current_raw),
                previous_value=normalize_number(previous_raw),
                confidence=0.85,
            )
        )

    return rows


def parse_financial_row(line: str) -> tuple[str, str, str] | None:
    tokens = line.split()
    if len(tokens) < 3:
        return None

    previous_tokens, index = take_number_from_right(tokens, len(tokens) - 1)
    if not previous_tokens:
        return None
    current_tokens, index = take_number_from_right(tokens, index)
    if not current_tokens:
        return None

    label_tokens = tokens[: index + 1]
    if label_tokens and re.fullmatch(r"\d{1,2}", label_tokens[-1]):
        label_tokens = label_tokens[:-1]

    label = " ".join(label_tokens).strip(" .:-")
    if not label or is_bad_label(label):
        return None
    return label, " ".join(current_tokens), " ".join(previous_tokens)


def take_number_from_right(tokens: list[str], start_index: int) -> tuple[list[str], int]:
    if start_index < 0:
        return [], start_index

    token = tokens[start_index].strip()
    if token == "-":
        return ["-"], start_index - 1
    if not is_number_piece(token):
        return [], start_index

    collected = [token]
    i = start_index - 1
    if _is_decimal_or_percent_piece(token) and not token.endswith(")"):
        return collected, i

    collected_group_count = 0
    while i >= 0 and len(collected) < 5:
        previous = tokens[i].strip()
        if not _is_integer_piece(previous):
            break
        digits = re.sub(r"\D", "", previous)
        if collected_group_count == 0:
            if len(digits) != 3:
                break
            collected.insert(0, previous)
            collected_group_count += 1
            i -= 1
            if previous.startswith("("):
                break
            continue

        collected.insert(0, previous)
        i -= 1
        if len(digits) < 3 or previous.startswith("("):
            break
        if i < 0 or not _is_integer_piece(tokens[i].strip()):
            break

    return collected, i


def is_number_piece(token: str) -> bool:
    token = token.strip()
    if token == "-":
        return True
    cleaned = token.strip("()").rstrip("%")
    return bool(re.fullmatch(r"-?\d[\d.,]*", cleaned))


def _is_integer_piece(token: str) -> bool:
    if _is_decimal_or_percent_piece(token):
        return False
    cleaned = token.strip("()")
    return bool(re.fullmatch(r"\d{1,3}", cleaned))


def _is_decimal_or_percent_piece(token: str) -> bool:
    return "." in token or "," in token or "%" in token


def _looks_like_label_continuation(line: str) -> bool:
    return bool(re.search(r"[A-Za-zÀ-ÿ]", line)) and not re.search(r"\d{3}", line)


def is_bad_label(label: str) -> bool:
    normalized = normalize_label(label) or ""
    if not re.search(r"[A-Za-zÀ-ÿ]", label):
        return True

    compact = re.sub(r"[^A-Za-zÀ-ÿ0-9]", "", label)
    if compact and sum(ch.isdigit() for ch in compact) > sum(ch.isalpha() for ch in compact):
        return True

    return normalized in {"note", "annee", "31_12_2024", "31_12_2025", "2024", "2025"}

