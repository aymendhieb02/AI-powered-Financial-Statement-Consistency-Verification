from __future__ import annotations

from pathlib import Path

from sicav_checker.extraction.section_detector import detect_sections
from sicav_checker.extraction.statement_extractor import COMPARABLE_STATEMENTS, calculate_extraction_quality, extract_document, extract_rows, parse_financial_row
from sicav_checker.models import Statement, StatementRow


MAXULA_LIKE_TEXT = """
MAXULA PLACEMENT SICAV
BILAN ARRETE AU 31 DECEMBRE 2024
ACTIF
Portefeuille-titres 4 7 826 775 7 701 801
Placements monétaires et disponibilités 6 5 123 450 5 001 200
TOTAL ACTIF 14 351 478 14 339 699
PASSIF
Opérateurs créditeurs 200 000 190 000
ACTIF NET 13 900 000 13 800 000

ETAT DE RESULTAT
Revenus du portefeuille-titres 900 000 870 000
Charges de gestion des placements 13 (141 328) (132 361)
VALEUR LIQUIDATIVE 107.508 108.164
TAUX DE RENDEMENT 5.14% 5.96%

ETAT DE VARIATION DE L'ACTIF NET
Variation de l'actif net 100 000 90 000
Actif net en début d'exercice 13 800 000 13 700 000
Actif net en fin d'exercice 13 900 000 13 800 000

NOTES AUX ETATS FINANCIERS
Note 1 Principes comptables

RAPPORT GENERAL
Opinion

RAPPORT SPECIAL
Conventions
"""


def test_section_detection_on_maxula_like_text() -> None:
    sections = detect_sections(MAXULA_LIKE_TEXT)

    assert list(sections) == [
        "bilan",
        "etat_resultat",
        "etat_variation_actif_net",
        "notes",
        "rapport_general",
        "rapport_special",
    ]
    assert "TOTAL ACTIF" in sections["bilan"]
    assert "Charges de gestion" in sections["etat_resultat"]


def test_parse_grouped_amount_row_right_to_left() -> None:
    parsed = parse_financial_row("Portefeuille-titres 4 7 826 775 7 701 801")

    assert parsed == ("Portefeuille-titres", "7 826 775", "7 701 801")
    rows = extract_rows("Portefeuille-titres 4 7 826 775 7 701 801", "bilan")
    assert rows[0].current_value == 7826775
    assert rows[0].previous_value == 7701801


def test_parse_negative_parentheses_row() -> None:
    rows = extract_rows("Charges de gestion des placements 13 (141 328) (132 361)", "etat_resultat")

    assert rows[0].label == "Charges de gestion des placements"
    assert rows[0].current_value == -141328
    assert rows[0].previous_value == -132361


def test_parse_percent_values() -> None:
    rows = extract_rows("TAUX DE RENDEMENT 5.14% 5.96%", "etat_variation_actif_net")

    assert rows[0].current_value == 5.14
    assert rows[0].previous_value == 5.96


def test_notes_are_detected_but_not_comparable() -> None:
    sections = detect_sections(MAXULA_LIKE_TEXT)

    assert "notes" in sections
    assert "notes" not in COMPARABLE_STATEMENTS


def test_extract_document_does_not_return_zero_rows_for_valid_text(monkeypatch, tmp_path: Path) -> None:
    pdf_path = tmp_path / "maxula_2024.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(
        "sicav_checker.extraction.statement_extractor.extract_layout_sections",
        lambda path: ({}, ""),
    )
    monkeypatch.setattr(
        "sicav_checker.extraction.statement_extractor.extract_text",
        lambda path: (MAXULA_LIKE_TEXT, "test_text"),
    )

    document = extract_document(pdf_path)

    assert document.document_year == 2024
    assert len(document.statements["bilan"].rows) > 0
    assert len(document.statements["etat_resultat"].rows) > 0
    assert len(document.statements["etat_variation_actif_net"].rows) > 0



def _rows(count: int, confidence: float = 0.85) -> list[StatementRow]:
    return [StatementRow(label=f"Line {index}", canonical_label=f"line_{index}", current_value=index, previous_value=index, confidence=confidence) for index in range(count)]


def test_document_extraction_quality_differentiates_empty_thin_and_complete() -> None:
    empty = calculate_extraction_quality({})
    thin = calculate_extraction_quality({"bilan": Statement(name="bilan", rows=_rows(1, 0.75))})
    complete = calculate_extraction_quality(
        {
            "bilan": Statement(name="bilan", rows=_rows(8, 0.9)),
            "etat_resultat": Statement(name="etat_resultat", rows=_rows(8, 0.9)),
            "etat_variation_actif_net": Statement(name="etat_variation_actif_net", rows=_rows(6, 0.9)),
        }
    )

    assert empty == 0.0
    assert 0 < thin < complete
    assert complete > 0.9


def test_extract_document_confidence_uses_quality_score_not_binary_switch(monkeypatch, tmp_path: Path) -> None:
    pdf_path = tmp_path / "thin_2024.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr("sicav_checker.extraction.statement_extractor.extract_layout_sections", lambda path: ({}, ""))
    monkeypatch.setattr(
        "sicav_checker.extraction.statement_extractor.extract_text",
        lambda path: ("BILAN\nTOTAL ACTIF 100 90\nNOTES AUX ETATS FINANCIERS\n", "test_text"),
    )
    monkeypatch.setattr("sicav_checker.extraction.statement_extractor.extract_with_ocr", lambda path: "")

    document = extract_document(pdf_path)

    assert list(document.statements) == ["bilan"]
    assert 0 < document.confidence < 0.9


def test_extract_document_uses_ocr_only_after_text_mode_finds_no_comparable_sections(monkeypatch, tmp_path: Path) -> None:
    pdf_path = tmp_path / "ocr_2024.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")
    calls = {"ocr": 0}

    monkeypatch.setattr("sicav_checker.extraction.statement_extractor.extract_layout_sections", lambda path: ({}, ""))
    monkeypatch.setattr("sicav_checker.extraction.statement_extractor.extract_text", lambda path: ("", "pymupdf_text"))

    def fake_ocr(path: Path) -> str:
        calls["ocr"] += 1
        return MAXULA_LIKE_TEXT

    monkeypatch.setattr("sicav_checker.extraction.statement_extractor.extract_with_ocr", fake_ocr)

    document = extract_document(pdf_path)

    assert calls["ocr"] == 1
    assert document.extraction_method == "ocr_fallback"
    assert set(COMPARABLE_STATEMENTS).issubset(document.statements)
