from __future__ import annotations

from sicav_checker.domain.models import ComparisonReport, ComparisonResult, DocumentMetadata, FinancialDocument, FinancialStatement, Severity, StatementRow, Status
from sicav_checker.reporting.report_generator import _report_tables


def test_report_generator_exports_detailed_evidence_sheets() -> None:
    old = FinancialDocument(metadata=DocumentMetadata(year=2024, source_file="old.pdf", confidence=0.96), statements={"bilan": FinancialStatement(name="bilan", rows=[StatementRow(label="TOTAL ACTIF", canonical_label="total_actif", current_value=100)]), "etat_resultat": FinancialStatement(name="etat_resultat", rows=[StatementRow(label="RESULTAT", canonical_label="resultat", current_value=10)]), "etat_variation_actif_net": FinancialStatement(name="etat_variation_actif_net", rows=[StatementRow(label="ACTIF NET", canonical_label="actif_net", current_value=80)])})
    new = FinancialDocument(metadata=DocumentMetadata(year=2025, source_file="new.pdf", confidence=0.96), statements={"bilan": FinancialStatement(name="bilan", rows=[StatementRow(label="TOTAL ACTIF", canonical_label="total_actif", previous_value=90)]), "etat_resultat": FinancialStatement(name="etat_resultat", rows=[StatementRow(label="RESULTAT", canonical_label="resultat", previous_value=10)]), "etat_variation_actif_net": FinancialStatement(name="etat_variation_actif_net", rows=[StatementRow(label="ACTIF NET", canonical_label="actif_net", previous_value=80)])})
    comparison = ComparisonResult(pair="2024->2025", year=2024, statement="bilan", old_label="TOTAL ACTIF", new_label="TOTAL ACTIF", canonical_label="total_actif", old_value=100, new_value=90, status=Status.CARRY_FORWARD_MISMATCH, severity=Severity.CRITICAL, delta=-10)
    tables = _report_tables(ComparisonReport(documents=[old, new], comparisons=[comparison]))

    assert "Extraction Summary" in tables
    assert "Comparison Summary" in tables
    assert "Accounting Summary" in tables
    assert "Metrics" in tables
    assert "Accounting Issues" in tables
    assert "Detailed Evidence" in tables
    detail = tables["Detailed Evidence"][0]
    assert detail["explanation"]
    assert detail["expected_value"] == 100
    assert detail["actual_value"] == 90
    assert detail["recommended_action"]
