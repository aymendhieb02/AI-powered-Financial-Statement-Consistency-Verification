from __future__ import annotations

from sicav_checker.comparison.coverage import comparison_coverage
from sicav_checker.comparison.cross_year_comparator import compare_documents
from sicav_checker.models import DocumentMetadata, FinancialDocument, FinancialStatement, StatementRow, Status
from sicav_checker.services.normalization_service import NormalizationService


def _statement(name: str, count: int, start: int = 1) -> FinancialStatement:
    return FinancialStatement(
        name=name,
        rows=[
            StatementRow(
                label=f"{name} financial line {index}",
                canonical_label=f"{name}__financial_line_{index}",
                current_value=start + index,
                previous_value=start + index - 1,
            )
            for index in range(count)
        ],
    )


def _document(year: int) -> FinancialDocument:
    return FinancialDocument(
        metadata=DocumentMetadata(year=year, source_file=f"{year}.pdf"),
        statements={
            "bilan": _statement("bilan", 30, 1000),
            "etat_resultat": _statement("etat_resultat", 25, 2000),
            "etat_variation_actif_net": _statement("etat_variation_actif_net", 25, 3000),
        },
    )


def _new_comparative_document() -> FinancialDocument:
    doc = _document(2025)
    for statement in doc.statements.values():
        for row in statement.rows:
            row.previous_value = row.current_value
            row.current_value = row.current_value + 100
    return doc


def test_deep_comparison_compares_all_80_statement_lines() -> None:
    old = _document(2024)
    new = _new_comparative_document()

    results = compare_documents(old, new)

    assert len(results) == 80
    assert sum(1 for item in results if item.status == Status.CARRY_FORWARD_OK) == 80
    assert comparison_coverage(old, new, results)["comparable_lines"] == 80


def test_deep_comparison_detects_mismatches_and_missing_lines() -> None:
    old = _document(2024)
    new = _new_comparative_document()
    new.statements["bilan"].rows[0].previous_value += 50
    new.statements["etat_resultat"].rows.pop(0)

    results = compare_documents(old, new)

    assert len(results) == 80
    assert sum(1 for item in results if item.status == Status.CARRY_FORWARD_MISMATCH) == 1
    assert sum(1 for item in results if item.status == Status.MISSING_IN_NEW_COMPARATIVE) == 1


def test_renamed_labels_can_still_match() -> None:
    old = FinancialDocument(
        metadata=DocumentMetadata(year=2024, source_file="2024.pdf"),
        statements={
            "bilan": FinancialStatement(
                name="bilan",
                rows=[StatementRow(label="Custom receivable account", canonical_label="bilan__custom_receivable_account", current_value=100)],
            )
        },
    )
    new = FinancialDocument(
        metadata=DocumentMetadata(year=2025, source_file="2025.pdf"),
        statements={
            "bilan": FinancialStatement(
                name="bilan",
                rows=[StatementRow(label="Custom receivables account", canonical_label="bilan__custom_receivables_account", previous_value=100)],
            )
        },
    )

    result = compare_documents(old, new)[0]

    assert result.status == Status.LABEL_RENAMED
    assert result.new_label == "Custom receivables account"


def test_unknown_labels_are_not_discarded_by_normalization() -> None:
    document = FinancialDocument(
        metadata=DocumentMetadata(year=2024, source_file="2024.pdf"),
        statements={
            "etat_resultat": FinancialStatement(
                name="etat_resultat",
                rows=[StatementRow(label="Unmapped semantic revenue bucket", canonical_label="", current_value=42, previous_value=41)],
            )
        },
    )

    normalized = NormalizationService().normalize_document(document)
    row = normalized.statements["etat_resultat"].rows[0]

    assert row.canonical_label == "etat_resultat__unmapped_semantic_revenue_bucket"
    assert row.match is not None
    assert row.match.method == "fallback_normalized_label"
