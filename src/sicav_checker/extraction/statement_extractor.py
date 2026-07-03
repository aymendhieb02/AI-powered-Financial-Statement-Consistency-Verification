from __future__ import annotations

import re
from pathlib import Path

from sicav_checker.extraction.section_detector import detect_sections
from sicav_checker.extraction.text_extractor import extract_text
from sicav_checker.models import ExtractedDocument, Statement, StatementRow
from sicav_checker.normalization.label_normalizer import normalize_label
from sicav_checker.normalization.number_normalizer import normalize_number
from sicav_checker.normalization.year_detector import detect_document_year


ROW_RE = re.compile(r"^(?P<label>[A-Za-zÀ-ÿ0-9'’ /().,&-]{3,}?)\s+(?P<current>[-(]?\d[\d\s.,]*\)?|-)\s+(?P<previous>[-(]?\d[\d\s.,]*\)?|-)\s*$")


def extract_document(path: str | Path) -> ExtractedDocument:
    pdf_path = Path(path)
    text, method = extract_text(pdf_path)
    year = detect_document_year(pdf_path, text)
    sections = detect_sections(text)
    statements: dict[str, Statement] = {}
    for name in ("bilan", "etat_resultat", "etat_variation_actif_net"):
        if name in sections:
            statements[name] = Statement(name=name, rows=extract_rows(sections[name]))
    confidence = 0.9 if statements else 0.4
    return ExtractedDocument(
        document_year=year,
        source_file=str(pdf_path),
        extraction_method=method,
        statements=statements,
        pages=[],
        confidence=confidence,
    )


def extract_rows(section_text: str) -> list[StatementRow]:
    rows: list[StatementRow] = []
    for line in section_text.splitlines():
        clean = " ".join(line.strip().split())
        match = ROW_RE.match(clean)
        if not match:
            continue
        label = match.group("label").strip()
        canonical = normalize_label(label)
        if not canonical:
            continue
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
