from __future__ import annotations

from sicav_checker.assessment.decision_engine import build_decision_summary
from sicav_checker.domain.models import DocumentMetadata, FinancialDocument, FinancialStatement, Severity, StatementRow, ValidationResult, Status


def row(label: str, key: str, current: float | int | None = None, previous: float | int | None = None) -> StatementRow:
    return StatementRow(label=label, canonical_label=key, current_value=current, previous_value=previous, confidence=0.95)


def good_doc(year: int) -> FinancialDocument:
    bilan_rows = [row(f"Bilan {index}", f"bilan_{index}", current=index + 1, previous=index) for index in range(18)]
    resultat_rows = [row(f"Resultat {index}", f"resultat_{index}", current=index + 1, previous=index) for index in range(17)]
    variation_rows = [row(f"Variation {index}", f"variation_{index}", current=index + 1, previous=index) for index in range(17)]
    return FinancialDocument(
        metadata=DocumentMetadata(year=year, source_file=f"{year}.pdf", confidence=0.96),
        statements={
            "bilan": FinancialStatement(name="bilan", rows=bilan_rows),
            "etat_resultat": FinancialStatement(name="etat_resultat", rows=resultat_rows),
            "etat_variation_actif_net": FinancialStatement(name="etat_variation_actif_net", rows=variation_rows),
        },
    )


def partial_doc(year: int) -> FinancialDocument:
    bilan_rows = [row(f"Bilan {index}", f"bilan_{index}", current=index + 1, previous=index) for index in range(15)]
    return FinancialDocument(
        metadata=DocumentMetadata(year=year, source_file=f"{year}.pdf", confidence=0.64),
        statements={"bilan": FinancialStatement(name="bilan", rows=bilan_rows)},
    )


def metrics(**overrides):
    base = {
        "financial_consistency": 100.0,
        "financial_consistency_denominator": 47,
        "actual_mismatches": 0,
        "critical_accounting_errors": 0,
        "missing_accounts": 0,
        "duplicate_labels": 0,
        "extraction_coverage": 100.0,
        "extraction_coverage_numerator": 47,
        "extraction_coverage_denominator": 47,
    }
    base.update(overrides)
    return base


def test_scenario_a_is_good_complete_pass() -> None:
    decisions = build_decision_summary([good_doc(2024), good_doc(2025)], metrics())

    assert decisions["extraction"]["status"] == "GOOD"
    assert decisions["comparison"]["status"] == "COMPLETE"
    assert decisions["accounting"]["status"] == "PASS"
    assert decisions["overall"]["status"] == "PASS"


def test_scenario_b_partial_extraction_results_in_unknown_accounting() -> None:
    decisions = build_decision_summary(
        [partial_doc(2024), partial_doc(2025)],
        metrics(financial_consistency_denominator=15, extraction_coverage=31.91, extraction_coverage_numerator=15, extraction_coverage_denominator=47, missing_accounts=32),
    )

    assert decisions["extraction"]["status"] == "PARTIAL"
    assert decisions["comparison"]["status"] == "PARTIAL"
    assert decisions["accounting"]["status"] == "UNKNOWN"
    assert decisions["overall"]["status"] == "NEEDS REVIEW"


def test_scenario_c_real_mismatch_fails_accounting_and_overall() -> None:
    decisions = build_decision_summary(
        [good_doc(2024), good_doc(2025)],
        metrics(financial_consistency=97.87, actual_mismatches=1, critical_accounting_errors=1),
    )

    assert decisions["extraction"]["status"] == "GOOD"
    assert decisions["comparison"]["status"] == "COMPLETE"
    assert decisions["accounting"]["status"] == "FAIL"
    assert decisions["overall"]["status"] == "FAIL"


def test_scenario_d_clean_comparison_passes() -> None:
    decisions = build_decision_summary([good_doc(2024), good_doc(2025)], metrics())

    assert decisions["accounting"]["status"] == "PASS"
    assert decisions["overall"]["status"] == "PASS"


def test_critical_validation_failure_also_fails_accounting() -> None:
    validation = ValidationResult(document_year=2025, statement="bilan", rule="identity", status=Status.MISMATCH, severity=Severity.CRITICAL)
    decisions = build_decision_summary([good_doc(2024), good_doc(2025)], metrics(), [validation])

    assert decisions["accounting"]["status"] == "FAIL"
