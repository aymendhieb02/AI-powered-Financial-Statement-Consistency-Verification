from __future__ import annotations

import re
from pathlib import Path

from sicav_checker.extraction.section_detector import detect_sections
from sicav_checker.extraction.text_extractor import extract_text
from sicav_checker.models import ExtractedDocument, Statement, StatementRow
from sicav_checker.normalization.label_normalizer import normalize_label
from sicav_checker.normalization.number_normalizer import normalize_number
from sicav_checker.normalization.year_detector import detect_document_year


NUMBER_RE = r"[-(]?\d[\d\s.,]*\)?|-"
ROW_RE = re.compile(rf"^(?P<label>.+?)\s+(?P<current>{NUMBER_RE})\s+(?P<previous>{NUMBER_RE})\s*$")
COMPARABLE_STATEMENTS = ("bilan", "etat_resultat", "etat_variation_actif_net", "notes")


def extract_document(path: str | Path) -> ExtractedDocument:
    pdf_path = Path(path)
    text, method = extract_text(pdf_path)
    year = detect_document_year(pdf_path, text)
    sections = detect_sections(text)
    statements: dict[str, Statement] = {}
    for name in COMPARABLE_STATEMENTS:
        if name in sections:
            rows = extract_rows(sections[name], statement_name=name)
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


def extract_rows(section_text: str, statement_name: str = "") -> list[StatementRow]:
    rows: list[StatementRow] = []
    statement_key = normalize_label(statement_name) or statement_name or "statement"
    for line in section_text.splitlines():
        clean = " ".join(line.strip().split())
        match = ROW_RE.match(clean)
        if not match:
            continue
        label = match.group("label").strip(" .:-")
        canonical = normalize_label(label) or f"{statement_key}__unknown_line_{len(rows) + 1}"
        rows.append(
            StatementRow(
                label=label,
                canonical_label=canonical,
                current_value=normalize_number(match.group("current")),
                previous_value=normalize_number(match.group("previous")),
                confidence=0.85,
            )
        )
    return rows
