from __future__ import annotations

import re
from dataclasses import dataclass
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
PROTECTED_NOTE_LABELS = {
    "total_actif",
    "total_passif",
    "actif_net",
    "total_passif_actif_net",
    "total_passif_et_actif_net",
    "valeur_liquidative",
    "taux_rendement",
}
PURE_SECTION_LABELS = {
    "actif",
    "passif",
    "capitaux_propres",
    "etat_resultat",
    "etat_variation_actif_net",
    "montants_exprimes_en_dinars_tunisiens",
    "note_annee_2025_annee_2024",
    "note_annee_2024_annee_2023",
}
CATEGORY_PREFIXES = ("PASSIF ", "ACTIF NET ", "ACTIF ")


@dataclass(frozen=True)
class ParsedCandidate:
    label: str
    current_raw: str
    previous_raw: str
    score: int


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
        if not clean or _is_pure_section_line(clean):
            continue

        parsed = parse_financial_row(clean)
        if parsed is None:
            if _looks_like_label_continuation(clean):
                pending_label = f"{pending_label} {clean}".strip()
            continue

        label, current_raw, previous_raw = parsed
        if pending_label:
            label = f"{pending_label} {label}".strip()
            pending_label = ""
        label = _strip_category_prefix(label)
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

    candidates: list[ParsedCandidate] = []
    # Try every split of the numeric suffix into current and previous values.
    # This avoids greedy grouping such as "32 605 31 144" -> "3260531144".
    for current_start in range(1, len(tokens) - 1):
        for previous_start in range(current_start + 1, len(tokens)):
            label_tokens = tokens[:current_start]
            current_tokens = tokens[current_start:previous_start]
            previous_tokens = tokens[previous_start:]
            if not _valid_value_tokens(current_tokens) or not _valid_value_tokens(previous_tokens):
                continue

            label, note_removed, note_value = _strip_trailing_note(label_tokens)
            label = _strip_category_prefix(label)
            if not label or is_bad_label(label):
                continue
            score = _candidate_score(label, current_tokens, previous_tokens, note_removed, note_value)
            candidates.append(
                ParsedCandidate(
                    label=label,
                    current_raw=" ".join(current_tokens),
                    previous_raw=" ".join(previous_tokens),
                    score=score,
                )
            )

    if not candidates:
        return None
    best = max(candidates, key=lambda item: item.score)
    return best.label, best.current_raw, best.previous_raw


def _valid_value_tokens(tokens: list[str]) -> bool:
    if not tokens:
        return False
    if tokens == ["-"]:
        return True
    if len(tokens) == 1:
        token = tokens[0].strip()
        cleaned = token.strip("()").rstrip("%")
        if "%" in token or "." in token or "," in token:
            return bool(re.fullmatch(r"-?\d[\d.,]*", cleaned))
        return bool(re.fullmatch(r"-?\d+", cleaned))

    if not all(_is_integer_piece(token) for token in tokens):
        return False
    first = re.sub(r"\D", "", tokens[0])
    if not (1 <= len(first) <= 3):
        return False
    if len(first) > 1 and first.startswith("0"):
        return False
    for token in tokens[1:]:
        digits = re.sub(r"\D", "", token)
        if len(digits) != 3:
            return False
    if tokens[0].startswith("(") and not tokens[-1].endswith(")"):
        return False
    if tokens[-1].endswith(")") and not tokens[0].startswith("("):
        return False
    return True


def _strip_trailing_note(label_tokens: list[str]) -> tuple[str, bool, int | None]:
    if not label_tokens:
        return "", False, None
    last = label_tokens[-1].strip()
    if re.fullmatch(r"\d{1,2}", last):
        label = " ".join(label_tokens[:-1]).strip(" .:-")
        if label:
            return label, True, int(last)
    return " ".join(label_tokens).strip(" .:-"), False, None


def _candidate_score(label: str, current_tokens: list[str], previous_tokens: list[str], note_removed: bool, note_value: int | None) -> int:
    normalized = normalize_label(label)
    score = 1000
    score += len(label.split())
    score += (len(current_tokens) + len(previous_tokens)) * 12
    if len(current_tokens) == len(previous_tokens):
        score += 8
    if re.search(r"(?:^|\s)\(?\d{1,3}\)?(?:\s+\(?\d{3}\)?)+$", label):
        score -= 80
    if note_removed:
        # SICAV rows often contain a small note number before the current-year value.
        score += 40 if (note_value is not None and note_value <= 20) else -35
    if note_removed and normalized in PROTECTED_NOTE_LABELS:
        score -= 120
    if not note_removed and current_tokens and re.fullmatch(r"\d{1,2}", current_tokens[0]) and normalized not in PROTECTED_NOTE_LABELS:
        score -= 25
    if current_tokens == ["-"] or previous_tokens == ["-"]:
        score += 4
    return score


def _is_integer_piece(token: str) -> bool:
    cleaned = token.strip().strip("()")
    return bool(re.fullmatch(r"-?\d{1,3}", cleaned))


def _looks_like_label_continuation(line: str) -> bool:
    return _contains_alpha(line) and not _is_pure_section_line(line)


def _is_pure_section_line(line: str) -> bool:
    normalized = normalize_label(line)
    return normalized in PURE_SECTION_LABELS or normalized.startswith("montants_exprimes")


def _strip_category_prefix(label: str) -> str:
    upper = label.upper()
    normalized = normalize_label(label)
    if normalized in PROTECTED_NOTE_LABELS:
        return label
    for prefix in CATEGORY_PREFIXES:
        if upper.startswith(prefix) and len(label) > len(prefix):
            return label[len(prefix):].strip(" .:-")
    return label


def _contains_alpha(value: str) -> bool:
    return any(char.isalpha() for char in value)


def is_bad_label(label: str) -> bool:
    normalized = normalize_label(label) or ""
    if not _contains_alpha(label):
        return True
    if normalized in PURE_SECTION_LABELS:
        return True

    compact = "".join(char for char in label if char.isalnum())
    if compact and sum(char.isdigit() for char in compact) > sum(char.isalpha() for char in compact):
        return True

    return normalized in {"note", "annee", "31_12_2024", "31_12_2025", "2024", "2025"}

