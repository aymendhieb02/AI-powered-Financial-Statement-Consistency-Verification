from __future__ import annotations

from pathlib import Path

from sicav_checker.extraction.section_detector import detect_sections
from sicav_checker.extraction.statement_extractor import COMPARABLE_STATEMENTS, extract_document, extract_rows, parse_financial_row


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
