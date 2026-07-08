from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from sicav_checker.core.logging import logger
from sicav_checker.domain.models import Evidence
from sicav_checker.extraction.layout_section_extractor import VisualLine, extract_layout_sections, extract_layout_sections_with_metadata
from sicav_checker.extraction.ocr_fallback import extract_with_ocr
from sicav_checker.extraction.section_detector import SECTION_ORDER, candidate_heading_lines, detect_sections
from sicav_checker.extraction.text_extractor import extract_text
from sicav_checker.models import ExtractedDocument, Statement, StatementRow
from sicav_checker.normalization.label_normalizer import normalize_label
from sicav_checker.normalization.number_normalizer import normalize_number
from sicav_checker.normalization.year_detector import detect_document_year


COMPARABLE_STATEMENTS = ("bilan", "etat_resultat", "etat_variation_actif_net")
EXPECTED_MIN_ROWS = {"bilan": 8, "etat_resultat": 8, "etat_variation_actif_net": 6}
NEAR_ZERO_TEXT_LENGTH = 200
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
PARENT_CONTEXTS = {
    "souscriptions": "souscriptions",
    "rachats": "rachats",
    "des_operations_exploitation": "operations_exploitation",
    "operations_exploitation": "operations_exploitation",
    "actif_net": "actif_net",
    "nombre_actions": "nombre_actions",
}
VARIATION_CONTEXT_LABELS = {
    "capital",
    "regularisation_sommes_non_distribuables",
    "regularisation_sommes_distribuables",
}
VARIATION_PERIOD_LABELS = {"en_debut_exercice", "en_fin_exercice"}
VARIATION_PERIOD_CONTEXTS = ("actif_net", "nombre_actions")
EMBEDDED_ROW_TITLE_PATTERNS = (
    re.compile(r"VARIATION\s+DE\s+L['\u2019]ACTIF\s+NET", re.IGNORECASE),
)
LIKELY_NOTE_LABELS = {
    "creances_exploitation",
    "operateurs_crediteurs",
    "autres_crediteurs_divers",
    "revenus_placements_monetaires",
    "charges_gestion_placements",
    "portefeuille_titres",
}
HEADER_PREFIX_PATTERNS = (
    re.compile(r"^\s*BILAN\s+(?:ARRETE\s+)?(?:AU\s+)?31\s+DECEMBRE\s+\d{4}\s*", re.IGNORECASE),
    re.compile(r"^\s*ETAT\s+(?:DE\s+)?RESULTAT\s*", re.IGNORECASE),
    re.compile(r"^\s*ETAT\s+DE\s+VARIATION\s+DE\s+L['\u2019]ACTIF\s+NET\s*", re.IGNORECASE),
    re.compile(r"^\s*(?:ACTIF|PASSIF)\s+Note\s+(?:(?:\d{1,2}/\d{1,2}/\d{2,4})\s*){1,4}", re.IGNORECASE),
    re.compile(r"^\s*Note\s+(?:Ann\S*e\s+\d{4}\s*){1,4}", re.IGNORECASE),
    re.compile(r"^\s*Ann\S*e\s+\d{4}(?:\s+Ann\S*e\s+\d{4})*\s*", re.IGNORECASE),
    re.compile(r"^\s*Page\s+\d+\s*", re.IGNORECASE),
    re.compile(r"^\s*DES\s+OPERATIONS\s+D['\u2019]?\s*EXPLOITATION\s*", re.IGNORECASE),
)


@dataclass(frozen=True)
class ParsedCandidate:
    label: str
    current_raw: str
    previous_raw: str
    score: int



def extract_document(path: str | Path) -> ExtractedDocument:
    pdf_path = Path(path)
    sections, text, method, section_lines = _extract_sections(pdf_path)
    return build_document_from_sections(pdf_path, sections, text, method, section_lines)


def build_document_from_sections(
    pdf_path: str | Path,
    sections: dict[str, str],
    text: str,
    method: str,
    section_lines: dict[str, list[VisualLine]] | None = None,
) -> ExtractedDocument:
    pdf_path = Path(pdf_path)
    section_lines = section_lines or {}
    _write_debug_outputs(pdf_path, text, sections)
    year = detect_document_year(pdf_path, text)
    _warn_missing_sections(pdf_path, text, sections)

    statements: dict[str, Statement] = {}
    for name in COMPARABLE_STATEMENTS:
        rows = extract_rows(
            sections.get(name, ""),
            statement_name=name,
            visual_lines=section_lines.get(name),
            document_id=pdf_path.name,
            source_file=str(pdf_path),
            extraction_method=method,
        )
        logger.info("Statement extraction: file={} section={} rows={}", pdf_path.name, name, len(rows))
        if rows:
            statements[name] = Statement(name=name, rows=rows)

    confidence = calculate_extraction_quality(statements)
    return ExtractedDocument(
        document_year=year,
        source_file=str(pdf_path),
        extraction_method=method,
        statements=statements,
        pages=sorted({row.page for statement in statements.values() for row in statement.rows if row.page is not None}),
        confidence=confidence,
    )


def calculate_extraction_quality(statements: dict[str, Statement]) -> float:
    """Compatibility wrapper around the shared extraction quality scorer."""
    from sicav_checker.extraction.quality import score_extraction

    document = ExtractedDocument(document_year=2000, source_file="quality-probe.pdf", extraction_method="quality", statements=statements)
    return score_extraction(document, "quality").confidence


def _extract_sections(pdf_path: Path) -> tuple[dict[str, str], str, str, dict[str, list[VisualLine]]]:
    layout_sections, layout_text, layout_lines = extract_layout_sections_with_metadata(pdf_path)
    if any(section in layout_sections for section in COMPARABLE_STATEMENTS):
        return layout_sections, layout_text, "pdfplumber_layout", layout_lines

    text, method = extract_text(pdf_path)
    text_sections = detect_sections(text)
    comparable_detected = any(section in text_sections for section in COMPARABLE_STATEMENTS)
    if comparable_detected and text.strip():
        return text_sections, text, method, {}

    if len(text.strip()) < NEAR_ZERO_TEXT_LENGTH or not comparable_detected:
        ocr_text = extract_with_ocr(pdf_path)
        ocr_sections = detect_sections(ocr_text)
        if any(section in ocr_sections for section in COMPARABLE_STATEMENTS):
            return ocr_sections, ocr_text, "ocr_fallback", {}

    return text_sections, text, method, {}


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



def extract_rows(
    section_text: str,
    statement_name: str = "",
    visual_lines: list[VisualLine] | None = None,
    document_id: str = "",
    source_file: str = "",
    extraction_method: str = "unknown",
) -> list[StatementRow]:
    rows: list[StatementRow] = []
    statement_key = normalize_label(statement_name) or statement_name or "statement"
    pending_label = ""
    parent_context = ""
    variation_period_counts: dict[str, int] = {}
    line_sources = visual_lines if visual_lines is not None else section_text.splitlines()

    for source in line_sources:
        visual_line = source if isinstance(source, VisualLine) else None
        raw_line = visual_line.text if visual_line else str(source)
        clean, header_cleaned = _clean_extracted_line(raw_line)
        if not clean:
            continue

        context = _parent_context_for_heading(clean)
        if context:
            parent_context = context
            pending_label = ""
            continue
        if _is_pure_section_line(clean):
            continue

        parsed = parse_financial_row(clean)
        if parsed is None:
            if _looks_like_label_continuation(clean):
                pending_label = f"{pending_label} {clean}".strip()
            continue

        label, current_raw, previous_raw = parsed
        confidence = 0.75 if header_cleaned else 0.85
        if pending_label:
            label = f"{pending_label} {label}".strip()
            pending_label = ""
            confidence = min(confidence, 0.75)
        label = _strip_category_prefix(label)
        label = _strip_embedded_row_title(label)
        if label.startswith("- "):
            label = label[2:].strip()
        if is_bad_label(label):
            continue

        normalized = normalize_label(label)
        if not normalized:
            canonical = f"{statement_key}__unknown_line_{len(rows) + 1}"
        elif statement_key == "variation_actif_net" and normalized in VARIATION_PERIOD_LABELS:
            count = variation_period_counts.get(normalized, 0)
            context_name = VARIATION_PERIOD_CONTEXTS[count] if count < len(VARIATION_PERIOD_CONTEXTS) else f"occurrence_{count + 1}"
            variation_period_counts[normalized] = count + 1
            canonical = f"{statement_key}__{context_name}_{normalized}"
        elif statement_key == "variation_actif_net" and parent_context and normalized in VARIATION_CONTEXT_LABELS:
            canonical = f"{statement_key}__{parent_context}_{normalized}"
        else:
            canonical = normalized
        current_value = normalize_number(current_raw)
        previous_value = normalize_number(previous_raw)
        section_name = parent_context or statement_name
        rows.append(
            StatementRow(
                label=label,
                canonical_label=canonical,
                current_value=current_value,
                previous_value=previous_value,
                page=visual_line.page if visual_line else None,
                confidence=confidence,
                evidence=_build_row_evidence(
                    visual_line,
                    statement_name=statement_name,
                    section_name=section_name,
                    label=label,
                    current_raw=current_raw,
                    previous_raw=previous_raw,
                    current_value=current_value,
                    previous_value=previous_value,
                    extraction_method=extraction_method,
                    document_id=document_id,
                    source_file=source_file,
                    confidence=confidence,
                ),
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



def _build_row_evidence(
    visual_line: VisualLine | None,
    statement_name: str,
    section_name: str,
    label: str,
    current_raw: str,
    previous_raw: str,
    current_value: float | int | None,
    previous_value: float | int | None,
    extraction_method: str,
    document_id: str,
    source_file: str,
    confidence: float,
) -> Evidence:
    bbox_row = visual_line.row_bbox if visual_line else None
    bbox_label = None
    bbox_current = None
    bbox_previous = None
    bounding_box = bbox_row
    raw_text = visual_line.text if visual_line else f"{label} {current_raw} {previous_raw}".strip()

    if visual_line:
        current_count = len(current_raw.split()) if current_raw else 0
        previous_count = len(previous_raw.split()) if previous_raw else 0
        words = list(visual_line.words)
        tail_previous = words[-previous_count:] if previous_count and len(words) >= previous_count else []
        tail_current_start = max(len(words) - previous_count - current_count, 0)
        tail_current_end = len(words) - previous_count if previous_count else len(words)
        tail_current = words[tail_current_start:tail_current_end] if current_count else []
        label_words = words[:tail_current_start] if tail_current_start > 0 else words[: max(len(words) - current_count - previous_count, 0)]
        bbox_label = _bbox_from_words(label_words)
        bbox_current = _bbox_from_words(tail_current)
        bbox_previous = _bbox_from_words(tail_previous)
        bounding_box = bbox_current or bbox_previous or bbox_row

    return Evidence(
        line_id=uuid4().hex,
        document_id=document_id,
        source_pdf=source_file,
        page=visual_line.page if visual_line else None,
        statement_name=statement_name,
        section_name=section_name,
        bounding_box=bounding_box,
        bbox_label=bbox_label,
        bbox_current=bbox_current,
        bbox_previous=bbox_previous,
        bbox_row=bbox_row,
        extraction_method=extraction_method,
        raw_text=raw_text,
        normalized_line=normalize_label(raw_text),
        label_text=label,
        value_text_current=current_raw,
        value_text_previous=previous_raw,
        normalized_value=current_value if current_value is not None else previous_value,
        current_value=current_value,
        previous_value=previous_value,
        confidence=confidence,
    )


def _bbox_from_words(words: list) -> tuple[float, float, float, float] | None:
    if not words:
        return None
    return (
        min(word.x0 for word in words),
        min(word.top for word in words),
        max(word.x1 for word in words),
        max(word.bottom for word in words),
    )


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
    score += (len(current_tokens) + len(previous_tokens)) * 15
    current_len = len(current_tokens)
    previous_len = len(previous_tokens)
    if current_len == previous_len:
        score += 8
    if re.search(r"(?:^|\s)\(?\d{1,3}\)?(?:\s+\(?\d{3}\)?)+$", label):
        score -= 90
    if note_removed:
        # SICAV rows often contain a small note number before the current-year value.
        score += 36 if (note_value is not None and note_value <= 20) else -40
        if normalized in LIKELY_NOTE_LABELS:
            score += 90
            if current_len >= previous_len:
                score += 20
        elif previous_tokens == ["-"]:
            score -= 130
        elif previous_len > current_len:
            score -= 130
    if note_removed and normalized in PROTECTED_NOTE_LABELS:
        score -= 140
    if note_removed and previous_len - current_len >= 2 and previous_len >= 4:
        score -= 95
    if not note_removed and current_tokens and re.fullmatch(r"\d{1,2}", current_tokens[0]) and normalized not in PROTECTED_NOTE_LABELS:
        score -= 18
    if current_tokens == ["-"] or previous_tokens == ["-"]:
        score += 4
    return score


def _is_integer_piece(token: str) -> bool:
    cleaned = token.strip().strip("()")
    return bool(re.fullmatch(r"-?\d{1,3}", cleaned))

def _clean_extracted_line(raw_line: str) -> tuple[str, bool]:
    line = " ".join(raw_line.strip().split())
    if not line:
        return "", False

    line = re.sub(r"^\((?:Montants|Amounts).*?\)\s*", "", line, flags=re.IGNORECASE)
    line, header_cleaned = _strip_table_header_prefixes(line)
    if not line:
        return "", True

    normalized = normalize_label(line)
    if _is_standalone_header(normalized):
        return "", True

    return line, header_cleaned


def _strip_table_header_prefixes(line: str) -> tuple[str, bool]:
    changed = False
    previous = None
    date_prefix = re.compile(r"^\s*(?:\d{1,2}/\d{1,2}/\d{2,4}\s*){1,4}")
    while line != previous:
        previous = line
        for pattern in HEADER_PREFIX_PATTERNS:
            match = pattern.match(line)
            if match:
                line = " ".join(line[match.end():].strip(" .:-").split())
                changed = True
        match = date_prefix.match(line)
        if match:
            line = " ".join(line[match.end():].strip(" .:-").split())
            changed = True
    return line, changed


def _is_standalone_header(normalized: str) -> bool:
    if not normalized:
        return True
    if normalized.startswith(("bilan_arrete", "note_annee", "actif_note", "passif_note", "page_")):
        return True
    if normalized in {"etat_resultat", "etat_variation_actif_net", "annee", "note"}:
        return True
    return bool(re.fullmatch(r"(?:31_12_)?\d{4}(?:_(?:31_12_)?\d{4})*", normalized))

def _strip_embedded_row_title(label: str) -> str:
    for pattern in EMBEDDED_ROW_TITLE_PATTERNS:
        match = pattern.search(label)
        if match and match.start() > 0:
            return label[match.start():].strip(" .:-")
    return label

def _parent_context_for_heading(line: str) -> str:
    return PARENT_CONTEXTS.get(normalize_label(line), "")

def _looks_like_label_continuation(line: str) -> bool:
    normalized = normalize_label(line)
    if normalized.startswith("page_"):
        return False
    return _contains_alpha(line) and not _is_pure_section_line(line) and not _parent_context_for_heading(line)


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


