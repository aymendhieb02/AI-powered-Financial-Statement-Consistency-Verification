from __future__ import annotations

from pathlib import Path

from sicav_checker.comparison.cross_year_comparator import compare_documents
from sicav_checker.comparison.metrics import build_metric_breakdown, build_review_items, write_metric_debug
from sicav_checker.domain.models import DocumentMetadata, Evidence, FinancialDocument, FinancialStatement, Severity, StatementRow, Status


def row(label: str, key: str, current: float | int | None = None, previous: float | int | None = None, evidence: Evidence | None = None) -> StatementRow:
    return StatementRow(label=label, canonical_label=key, current_value=current, previous_value=previous, confidence=0.9, evidence=evidence)


def doc(year: int, rows: list[StatementRow]) -> FinancialDocument:
    return FinancialDocument(metadata=DocumentMetadata(year=year, source_file=f"{year}.pdf", confidence=0.96), statements={"bilan": FinancialStatement(name="bilan", rows=rows)})


def test_financial_consistency_is_100_when_compared_values_match_even_with_missing_rows() -> None:
    old = doc(2024, [row("TOTAL ACTIF", "total_actif", current=100), row("ACTIF NET", "actif_net", current=80)])
    new = doc(2025, [row("TOTAL ACTIF", "total_actif", current=110, previous=100)])
    results = compare_documents(old, new)

    metrics = build_metric_breakdown(old, new, results)

    assert metrics["financial_consistency"] == 100
    assert metrics["financial_consistency_denominator"] == 1
    assert metrics["extraction_coverage"] < 100
    assert metrics["missing_accounts"] == 1


def test_risk_is_extraction_not_financial_when_no_mismatches_but_missing_rows() -> None:
    old = doc(2024, [row("TOTAL ACTIF", "total_actif", current=100), row("ACTIF NET", "actif_net", current=80)])
    new = doc(2025, [row("TOTAL ACTIF", "total_actif", current=110, previous=100)])
    metrics = build_metric_breakdown(old, new, compare_documents(old, new))

    assert metrics["actual_mismatches"] == 0
    assert metrics["risk"]["category"] in {"MEDIUM_STRUCTURAL_RISK", "HIGH_EXTRACTION_RISK"}
    assert metrics["verdict"]["label"] == "NEEDS REVIEW"


def test_fail_only_for_actual_carry_forward_mismatch() -> None:
    old = doc(2024, [row("TOTAL ACTIF", "total_actif", current=100)])
    new = doc(2025, [row("TOTAL ACTIF", "total_actif", current=110, previous=90)])
    metrics = build_metric_breakdown(old, new, compare_documents(old, new))

    assert metrics["actual_mismatches"] == 1
    assert metrics["verdict"]["label"] == "FAIL"
    assert metrics["risk"]["category"] == "HIGH_FINANCIAL_RISK"
    assert metrics["accounting_health"]["label"] == "FAIL" or metrics["accounting_health"]["label"] == "NEEDS_REVIEW"


def test_duplicate_label_detail_recommends_parent_context() -> None:
    old = doc(2024, [row("Capital", "capital", current=1), row("Capital", "capital", current=2)])
    new = doc(2025, [row("Capital", "capital", previous=1)])
    results = compare_documents(old, new)
    details = build_review_items(results, old, new)

    duplicate = next(item for item in details if item["status"] == Status.DUPLICATE_LABEL.value)
    assert "parent context" in duplicate["recommended_action"].lower()
    assert duplicate["explanation"]
    assert duplicate["issue_classification"] == "structural_extraction_issue"
    assert duplicate["status_group"] == "structural"


def test_metric_debug_json_contains_formula_inputs(tmp_path: Path) -> None:
    old = doc(2024, [row("TOTAL ACTIF", "total_actif", current=100)])
    new = doc(2025, [row("TOTAL ACTIF", "total_actif", current=110, previous=100)])
    results = compare_documents(old, new)
    metrics = build_metric_breakdown(old, new, results)
    details = build_review_items(results, old, new)
    output = tmp_path / "metric_debug.json"

    write_metric_debug(output, metrics, details)

    content = output.read_text(encoding="utf-8")
    assert "financial_consistency" in content
    assert "exact_matches / actually_compared_values" in content


def test_anomaly_detail_contains_values_explanation_and_action() -> None:
    old = doc(2024, [row("TOTAL ACTIF", "total_actif", current=100)])
    new = doc(2025, [row("TOTAL ACTIF", "total_actif", current=110, previous=90)])
    details = build_review_items(compare_documents(old, new), old, new)

    item = details[0]
    assert item["expected_value"] == 100
    assert item["actual_value"] == 90
    assert item["difference"] == -10
    assert item["explanation"]
    assert item["recommended_action"]
    assert item["reason"] == "value_difference"
    assert item["issue_classification"] == "accounting_issue"
    assert item["status_group"] == "financial"


def test_polluted_label_detail_exposes_explicit_reasons() -> None:
    old = doc(2024, [row("BILAN ARRETE AU 31 DECEMBRE 2024 Portefeuille-titres", "portefeuille_titres", current=100)])
    new = doc(2025, [row("Portefeuille-titres", "portefeuille_titres", previous=100)])
    details = build_review_items(compare_documents(old, new), old, new)

    item = details[0]
    assert "contains_header" in item["pollution_reasons"]
    assert item["issue_classification"] == "polluted_label"


def test_duplicate_review_item_preserves_candidate_evidence() -> None:
    old = doc(
        2024,
        [
            row("Capital", "capital", current=1, evidence=Evidence(page=4, raw_text="Capital 1", section_name="bilan")),
            row("Capital", "capital", current=2, evidence=Evidence(page=4, raw_text="Capital 2", section_name="bilan")),
        ],
    )
    new = doc(2025, [row("Capital", "capital", previous=1, evidence=Evidence(page=5, raw_text="Capital 1", section_name="bilan"))])

    details = build_review_items(compare_documents(old, new), old, new)
    duplicate = next(item for item in details if item["status"] == Status.DUPLICATE_LABEL.value)

    assert len(duplicate["duplicate_candidates"]) >= 2
    assert duplicate["duplicate_candidates"][0]["raw_text"]
    assert duplicate["old_section"] == "bilan"


def test_new_only_line_is_classified_as_presentation_review_not_accounting_failure() -> None:
    old = doc(2024, [row("TOTAL ACTIF", "total_actif", current=100)])
    new = doc(2025, [row("TOTAL ACTIF", "total_actif", previous=100), row("New fee line", "new_fee_line", previous=12)])
    results = compare_documents(old, new)
    details = build_review_items(results, old, new)

    new_only = next(item for item in details if item["canonical_label"] == "new_fee_line")
    metrics = build_metric_breakdown(old, new, results)

    assert new_only["issue_type"] == "new_reporting_line"
    assert new_only["issue_classification"] == "presentation_change"
    assert metrics["actual_mismatches"] == 0
    assert metrics["verdict"]["label"] == "NEEDS REVIEW"


def test_extraction_coverage_is_capped_and_extra_pairings_are_reported() -> None:
    old = doc(2024, [row("A", "a", current=1)])
    new = doc(2025, [row("A", "a", previous=1)])
    from sicav_checker.domain.models import ComparisonResult, Severity, Status

    comparisons = [
        ComparisonResult(pair="2024->2025", year=2024, statement="bilan", old_label="A", new_label="A", canonical_label="a", old_value=1, new_value=1, status=Status.CARRY_FORWARD_OK, severity=Severity.LOW),
        ComparisonResult(pair="2024->2025", year=2024, statement="bilan", old_label="B", new_label="B", canonical_label="b", old_value=2, new_value=2, status=Status.CARRY_FORWARD_OK, severity=Severity.LOW),
    ]

    metrics = build_metric_breakdown(old, new, comparisons)

    assert metrics["extraction_coverage"] == 100
    assert metrics["extraction_coverage_raw_numerator"] == 2
    assert metrics["extra_pairings"] == 1
