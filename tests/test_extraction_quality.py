from __future__ import annotations

from sicav_checker.extraction.quality import pollution_reasons, score_extraction
from sicav_checker.models import ExtractedDocument, Statement, StatementRow


def row(label: str, current: int | float | None = 100, previous: int | float | None = 90) -> StatementRow:
    return StatementRow(label=label, canonical_label=label.lower().replace(" ", "_"), current_value=current, previous_value=previous)


def document(statements: dict[str, Statement]) -> ExtractedDocument:
    return ExtractedDocument(document_year=2024, source_file="synthetic.pdf", extraction_method="test", statements=statements)


def test_extraction_quality_scores_complete_document_high() -> None:
    bilan_rows = [
        row("TOTAL ACTIF", 1000, 900),
        row("TOTAL PASSIF", 200, 180),
        row("ACTIF NET", 800, 720),
        row("TOTAL PASSIF ET ACTIF NET", 1000, 900),
        *[row(f"Asset {index}") for index in range(20)],
    ]
    resultat_rows = [
        row("TOTAL DES REVENUS DES PLACEMENTS"),
        row("RESULTAT DE L'EXERCICE"),
        row("VALEUR LIQUIDATIVE", 108.1, 107.8),
        row("TAUX DE RENDEMENT", 5.5, 5.1),
        *[row(f"Income {index}") for index in range(12)],
    ]
    variation_rows = [row(f"Variation {index}") for index in range(10)]
    report = score_extraction(
        document(
            {
                "bilan": Statement(name="bilan", rows=bilan_rows),
                "etat_resultat": Statement(name="etat_resultat", rows=resultat_rows),
                "etat_variation_actif_net": Statement(name="etat_variation_actif_net", rows=variation_rows),
            }
        ),
        "test",
    )

    assert report.required_statements_found == 3
    assert report.required_totals_found >= 7
    assert report.numeric_population_rate == 1.0
    assert report.score > 0.85


def test_extraction_quality_scores_thin_polluted_document_low() -> None:
    polluted_rows = [
        row("BILAN ARRETE AU 31 DECEMBRE 2022 Portefeuille-titres", None, None),
        row("ETAT DE RESULTAT Annee 2022 Revenus", None, 10),
        *[row(f"Line {index}", None, None) for index in range(13)],
    ]
    report = score_extraction(document({"bilan": Statement(name="bilan", rows=polluted_rows)}), "weak")

    assert report.total_rows == 15
    assert report.missing_required_statement_count == 2
    assert report.polluted_label_count >= 2
    assert report.numeric_population_rate < 0.2
    assert report.score < 0.45


def test_pollution_reasons_are_explicit() -> None:
    reasons = pollution_reasons("BILAN ARRETE AU 31 DECEMBRE 2025 Note Année 2025 Portefeuille-titres")

    assert "contains_header" in reasons
    assert "contains_year" in reasons
    assert "contains_note_title" in reasons
