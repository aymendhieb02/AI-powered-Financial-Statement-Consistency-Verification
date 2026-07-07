from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sicav_checker.core.logging import logger
from sicav_checker.extraction.layout_section_extractor import extract_layout_sections
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
LIKELY_NOTE_LABELS = {
    "creances_exploitation",
    "operateurs_crediteurs",
    "autres_crediteurs_divers",
    "revenus_placements_monetaires",
    "charges_gestion_placements",
    "portefeuille_titres",
}
GLUED_ROW_PATTERNS = (
    re.compile(r"Portefeuille-titres", re.IGNORECASE),
    re.compile(r"VARIATION\s+DE\s+L['\u2019]ACTIF\s+NET\s+RESULTANT", re.IGNORECASE),
    re.compile(r"R\S*sultat\s+d['\u2019]exploitation", re.IGNORECASE),
)


@dataclass(frozen=True)
class ParsedCandidate:
    label: str
    current_raw: str
    previous_raw: str
    score: int


def extract_document(path: str | Path) -> ExtractedDocument:
    pdf_path = Path(path)
    sections, text, method = _extract_sections(pdf_path)
    return build_document_from_sections(pdf_path, sections, text, method)


def build_document_from_sections(
    pdf_path: str | Path,
    sections: dict[str, str],
    text: str,
    method: str,
) -> ExtractedDocument:
    pdf_path = Path(pdf_path)
    _write_debug_outputs(pdf_path, text, sections)
    year = detect_document_year(pdf_path, text)
    _warn_missing_sections(pdf_path, text, sections)

    statements: dict[str, Statement] = {}
    for name in COMPARABLE_STATEMENTS:
        rows = extract_rows(sections.get(name, ""), statement_name=name)
        logger.info("Statement extraction: file={} section={} rows={}", pdf_path.name, name, len(rows))
        if rows:
            statements[name] = Statement(name=name, rows=rows)

    confidence = calculate_extraction_quality(statements)
    return ExtractedDocument(
        document_year=year,
        source_file=str(pdf_path),
        extraction_method=method,
        statements=statements,
        pages=[],
        confidence=confidence,
    )


def calculate_extraction_quality(statements: dict[str, Statement]) -> float:
    """Compatibility wrapper around the shared extraction quality scorer."""
    from sicav_checker.extraction.quality import score_extraction

    document = ExtractedDocument(document_year=2000, source_file="quality-probe.pdf", extraction_method="quality", statements=statements)
    return score_extraction(document, "quality").confidence


def _extract_sections(pdf_path: Path) -> tuple[dict[str, str], str, str]:
    layout_sections, layout_text = extract_layout_sections(pdf_path)
    if any(section in layout_sections for section in COMPARABLE_STATEMENTS):
        return layout_sections, layout_text, "pdfplumber_layout"

    text, method = extract_text(pdf_path)
    text_sections = detect_sections(text)
    comparable_detected = any(section in text_sections for section in COMPARABLE_STATEMENTS)
    if comparable_detected and text.strip():
        return text_sections, text, method

    if len(text.strip()) < NEAR_ZERO_TEXT_LENGTH or not comparable_detected:
        ocr_text = extract_with_ocr(pdf_path)
        ocr_sections = detect_sections(ocr_text)
        if any(section in ocr_sections for section in COMPARABLE_STATEMENTS):
            return ocr_sections, ocr_text, "ocr_fallback"

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
    parent_context = ""

    for raw_line in section_text.splitlines():
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
        if label.startswith("- "):
            label = label[2:].strip()
        if is_bad_label(label):
            continue

        normalized = normalize_label(label)
        if not normalized:
            canonical = f"{statement_key}__unknown_line_{len(rows) + 1}"
        elif statement_key == "variation_actif_net" and parent_context and normalized in VARIATION_CONTEXT_LABELS:
            canonical = f"{statement_key}__{parent_context}_{normalized}"
        else:
            canonical = normalized
        rows.append(
            StatementRow(
                label=label,
                canonical_label=canonical,
                current_value=normalize_number(current_raw),
                previous_value=normalize_number(previous_raw),
                confidence=confidence,
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
    for pattern in GLUED_ROW_PATTERNS:
        match = pattern.search(line)
        if match and match.start() > 0:
            return line[match.start():].strip(), True

    normalized = normalize_label(line)
    if normalized.startswith("bilan_arrete_au"):
        return "", True
    if normalized in {"etat_resultat", "etat_variation_actif_net"}:
        return "", True
    if normalized.startswith("note_annee") or normalized.startswith("actif_note"):
        return "", True

    for prefix in (
        "DES OPERATIONS D'EXPLOITATION ",
        "DES OPERATIONS D EXPLOITATION ",
    ):
        if line.upper().startswith(prefix):
            return line[len(prefix):].strip(), True

    return line, False


def _parent_context_for_heading(line: str) -> str:
    return PARENT_CONTEXTS.get(normalize_label(line), "")

def _looks_like_label_continuation(line: str) -> bool:
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

