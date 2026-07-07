from __future__ import annotations

from sicav_checker.domain.models import ComparisonReport, ComparisonResult, DocumentMetadata, FinancialDocument, FinancialStatement, Severity, StatementRow, Status
from sicav_checker.reporting.report_generator import _report_tables


def test_report_generator_exports_detailed_evidence_sheets() -> None:
    old = FinancialDocument(metadata=DocumentMetadata(year=2024, source_file="old.pdf"), statements={"bilan": FinancialStatement(name="bilan", rows=[StatementRow(label="TOTAL ACTIF", canonical_label="total_actif", current_value=100)])})
    new = FinancialDocument(metadata=DocumentMetadata(year=2025, source_file="new.pdf"), statements={"bilan": FinancialStatement(name="bilan", rows=[StatementRow(label="TOTAL ACTIF", canonical_label="total_actif", previous_value=90)])})
    comparison = ComparisonResult(pair="2024->2025", year=2024, statement="bilan", old_label="TOTAL ACTIF", new_label="TOTAL ACTIF", canonical_label="total_actif", old_value=100, new_value=90, status=Status.CARRY_FORWARD_MISMATCH, severity=Severity.CRITICAL, delta=-10)
    tables = _report_tables(ComparisonReport(documents=[old, new], comparisons=[comparison]))

    assert "Metrics" in tables
    assert "Actual Mismatches" in tables
    assert "Detailed Evidence" in tables
    detail = tables["Detailed Evidence"][0]
    assert detail["explanation"]
    assert detail["expected_value"] == 100
    assert detail["actual_value"] == 90
    assert detail["recommended_action"]
