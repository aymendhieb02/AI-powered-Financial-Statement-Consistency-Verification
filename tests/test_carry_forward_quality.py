from __future__ import annotations

from sicav_checker.comparison.coverage import comparison_coverage
from sicav_checker.comparison.cross_year_comparator import compare_documents
from sicav_checker.models import DocumentMetadata, FinancialDocument, FinancialStatement, Status, StatementRow
from sicav_checker.normalization.label_normalizer import normalize_label


def row(label: str, current: float | int | None = None, previous: float | int | None = None) -> StatementRow:
    return StatementRow(label=label, canonical_label=normalize_label(label), current_value=current, previous_value=previous)


def test_maxula_like_carry_forward_rows_are_ok() -> None:
    old = FinancialDocument(
        metadata=DocumentMetadata(year=2024, source_file="2024.pdf"),
        statements={
            "bilan": FinancialStatement(
                name="bilan",
                rows=[
                    row("Portefeuille-titres", current=7826775),
                    row("TOTAL ACTIF", current=14339699),
                    row("ACTIF NET", current=14266685),
                ],
            ),
            "etat_resultat": FinancialStatement(
                name="etat_resultat",
                rows=[row("Charges de gestion des placements", current=-132361)],
            ),
            "etat_variation_actif_net": FinancialStatement(
                name="etat_variation_actif_net",
                rows=[
                    row("Valeur liquidative", current=108.164),
                    row("Taux de rendement", current=5.96),
                ],
            ),
        },
    )
    new = FinancialDocument(
        metadata=DocumentMetadata(year=2025, source_file="2025.pdf"),
        statements={
            "bilan": FinancialStatement(
                name="bilan",
                rows=[
                    row("Portefeuille-titres", previous=7826775, current=9000000),
                    row("Total de l'actif", previous=14339699, current=15000000),
                    row("Total actif net", previous=14266685, current=15100000),
                ],
            ),
            "etat_resultat": FinancialStatement(
                name="etat_resultat",
                rows=[row("Charges de gestion des placements", previous=-132361, current=-140000)],
            ),
            "etat_variation_actif_net": FinancialStatement(
                name="etat_variation_actif_net",
                rows=[
                    row("Valeur liquidative", previous=108.164, current=110.0),
                    row("Taux de rendement", previous=5.96, current=6.1),
                ],
            ),
        },
    )

    results = compare_documents(old, new)

    assert len(results) == 6
    assert all(item.status in {Status.CARRY_FORWARD_OK, Status.LABEL_RENAMED} for item in results)
    assert comparison_coverage(old, new, results)["comparison_coverage_percentage"] == 100


def test_duplicate_labels_create_anomaly_without_inflating_coverage() -> None:
    old = FinancialDocument(
        metadata=DocumentMetadata(year=2024, source_file="2024.pdf"),
        statements={
            "bilan": FinancialStatement(
                name="bilan",
                rows=[row("TOTAL ACTIF", current=100), row("TOTAL ACTIF", current=100)],
            )
        },
    )
    new = FinancialDocument(
        metadata=DocumentMetadata(year=2025, source_file="2025.pdf"),
        statements={"bilan": FinancialStatement(name="bilan", rows=[row("TOTAL ACTIF", previous=100)])},
    )

    results = compare_documents(old, new)
    coverage = comparison_coverage(old, new, results)

    assert sum(1 for item in results if item.status == Status.DUPLICATE_LABEL) == 1
    assert coverage["comparison_coverage_percentage"] == 100
    assert coverage["comparable_lines"] == 1


def test_missing_labels_are_counted_once() -> None:
    old = FinancialDocument(
        metadata=DocumentMetadata(year=2024, source_file="2024.pdf"),
        statements={"bilan": FinancialStatement(name="bilan", rows=[row("TOTAL ACTIF", current=100)])},
    )
    new = FinancialDocument(
        metadata=DocumentMetadata(year=2025, source_file="2025.pdf"),
        statements={"bilan": FinancialStatement(name="bilan", rows=[])},
    )

    results = compare_documents(old, new)

    assert len(results) == 1
    assert results[0].status == Status.MISSING_IN_NEW_COMPARATIVE


def test_labels_only_pair_within_same_statement() -> None:
    old = FinancialDocument(
        metadata=DocumentMetadata(year=2024, source_file="2024.pdf"),
        statements={"bilan": FinancialStatement(name="bilan", rows=[row("TOTAL ACTIF", current=100)])},
    )
    new = FinancialDocument(
        metadata=DocumentMetadata(year=2025, source_file="2025.pdf"),
        statements={"etat_resultat": FinancialStatement(name="etat_resultat", rows=[row("TOTAL ACTIF", previous=100)])},
    )

    results = compare_documents(old, new)

    assert {item.statement for item in results} == {"bilan", "etat_resultat"}
    assert any(item.status == Status.MISSING_IN_NEW_COMPARATIVE for item in results)
    assert any(item.status == Status.MISSING_IN_OLD_CURRENT for item in results)
