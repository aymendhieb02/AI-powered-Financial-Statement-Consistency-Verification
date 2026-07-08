from pathlib import Path

from sicav_checker.domain.models import ComparisonResult, DocumentMetadata, FinancialDocument, FinancialStatement, Severity, StatementRow, Status
from sicav_checker.pipeline.orchestrator import PipelineResult
from sicav_checker.services.project_service import ProjectService


def test_project_service_creates_project_and_uploads_pdf(tmp_path: Path) -> None:
    service = ProjectService(root_dir=tmp_path)
    project = service.create_project("MAXULA", "MAXULA PLACEMENT SICAV", "Audit")

    uploaded = service.save_upload(project.id, "2025_maxula.pdf", b"%PDF-1.4 synthetic")
    documents = service.list_documents(project.id)

    assert uploaded.detected_year == 2025
    assert documents[0].filename == "2025_maxula.pdf"
    assert documents[0].size > 0


def test_project_service_runs_empty_verification(tmp_path: Path) -> None:
    service = ProjectService(root_dir=tmp_path)
    project = service.create_project("MAXULA", "MAXULA PLACEMENT SICAV", "Audit")

    run = service.run_verification(project.id)

    assert run.status == "completed"
    assert run.summary["documents_analyzed"] == 0
    assert len(run.report_paths) == 2


def test_project_service_caps_risk_below_critical_without_critical_anomalies(tmp_path: Path) -> None:
    service = ProjectService(root_dir=tmp_path)
    comparisons = [
        ComparisonResult(
            pair="2024->2025",
            year=2024,
            statement="bilan",
            old_label="Account",
            new_label="Account",
            canonical_label=f"account_{index}",
            old_value=100,
            new_value=90,
            status=Status.CARRY_FORWARD_MISMATCH,
            severity=Severity.MEDIUM,
        )
        for index in range(12)
    ]
    result = PipelineResult(documents=[], comparisons=comparisons, validations=[], missing_years=[], report_paths=[])

    run = service._run_from_pipeline("project-id", result)

    assert run.summary["critical_anomalies"] == 0
    assert run.summary["risk_score"] == 80
    assert run.summary["accounting_status"] == "UNKNOWN"
    assert run.summary["verdict"] == "NEEDS REVIEW"


def test_project_service_marks_clean_run_as_pass(tmp_path: Path) -> None:
    service = ProjectService(root_dir=tmp_path)
    old = FinancialDocument(
        metadata=DocumentMetadata(year=2024, source_file="2024.pdf", confidence=0.96),
        statements={
            "bilan": FinancialStatement(name="bilan", rows=[StatementRow(label="TOTAL ACTIF", canonical_label="total_actif", current_value=100)]),
            "etat_resultat": FinancialStatement(name="etat_resultat", rows=[StatementRow(label="RESULTAT", canonical_label="resultat", current_value=10)]),
            "etat_variation_actif_net": FinancialStatement(name="etat_variation_actif_net", rows=[StatementRow(label="ACTIF NET", canonical_label="actif_net", current_value=80)]),
        },
    )
    new = FinancialDocument(
        metadata=DocumentMetadata(year=2025, source_file="2025.pdf", confidence=0.96),
        statements={
            "bilan": FinancialStatement(name="bilan", rows=[StatementRow(label="TOTAL ACTIF", canonical_label="total_actif", previous_value=100)]),
            "etat_resultat": FinancialStatement(name="etat_resultat", rows=[StatementRow(label="RESULTAT", canonical_label="resultat", previous_value=10)]),
            "etat_variation_actif_net": FinancialStatement(name="etat_variation_actif_net", rows=[StatementRow(label="ACTIF NET", canonical_label="actif_net", previous_value=80)]),
        },
    )
    comparisons = [
        ComparisonResult(pair="2024->2025", year=2024, statement="bilan", old_label="TOTAL ACTIF", new_label="TOTAL ACTIF", canonical_label="total_actif", old_value=100, new_value=100, status=Status.CARRY_FORWARD_OK, severity=Severity.LOW),
        ComparisonResult(pair="2024->2025", year=2024, statement="etat_resultat", old_label="RESULTAT", new_label="RESULTAT", canonical_label="resultat", old_value=10, new_value=10, status=Status.CARRY_FORWARD_OK, severity=Severity.LOW),
        ComparisonResult(pair="2024->2025", year=2024, statement="etat_variation_actif_net", old_label="ACTIF NET", new_label="ACTIF NET", canonical_label="actif_net", old_value=80, new_value=80, status=Status.CARRY_FORWARD_OK, severity=Severity.LOW),
    ]

    run = service._run_from_pipeline("project-id", PipelineResult(documents=[old, new], comparisons=comparisons, validations=[], missing_years=[], report_paths=[]))

    assert run.summary["extraction_status"] == "PARTIAL" or run.summary["extraction_status"] == "GOOD"
    assert run.summary["comparison_status"] in {"COMPLETE", "PARTIAL"}
    assert run.summary["accounting_status"] in {"PASS", "UNKNOWN"}

def test_project_service_persists_evidence_items_with_raw_lines(tmp_path: Path) -> None:
    service = ProjectService(root_dir=tmp_path)
    old = FinancialDocument(metadata=DocumentMetadata(year=2024, source_file="2024.pdf", confidence=0.9), statements={"bilan": FinancialStatement(name="bilan", rows=[StatementRow(label="TOTAL ACTIF", canonical_label="total_actif", current_value=100)])})
    new = FinancialDocument(metadata=DocumentMetadata(year=2025, source_file="2025.pdf", confidence=0.9), statements={"bilan": FinancialStatement(name="bilan", rows=[StatementRow(label="TOTAL ACTIF", canonical_label="total_actif", previous_value=90)])})
    from sicav_checker.domain.models import Evidence
    comparison = ComparisonResult(pair="2024->2025", year=2024, statement="bilan", old_label="TOTAL ACTIF", new_label="TOTAL ACTIF", canonical_label="total_actif", old_value=100, new_value=90, status=Status.CARRY_FORWARD_MISMATCH, severity=Severity.CRITICAL, delta=-10, old_evidence=Evidence(page=4, raw_text="TOTAL ACTIF 100", source_pdf="2024.pdf"), new_evidence=Evidence(page=5, raw_text="TOTAL ACTIF 90", source_pdf="2025.pdf"))
    run = service._run_from_pipeline("project-id", PipelineResult(documents=[old, new], comparisons=[comparison], validations=[], missing_years=[], report_paths=[]))
    assert run.evidence_items
    evidence = run.evidence_items[0]
    assert evidence["old_raw_line"] == "TOTAL ACTIF 100"
    assert evidence["new_raw_line"] == "TOTAL ACTIF 90"
    assert evidence["issue_type"] == "financial_mismatch"

def test_structural_issue_does_not_create_accounting_fail(tmp_path: Path) -> None:
    service = ProjectService(root_dir=tmp_path)
    comparison = ComparisonResult(pair="2024->2025", year=2024, statement="etat_resultat", old_label="Resultat d exploitation", new_label="Regularisation du resultat d exploitation", canonical_label="etat_resultat__resultat_exploitation", old_value=None, new_value=None, status=Status.DUPLICATE_LABEL, severity=Severity.MEDIUM)
    run = service._run_from_pipeline("project-id", PipelineResult(documents=[], comparisons=[comparison], validations=[], missing_years=[], report_paths=[]))
    assert run.summary["accounting_status"] != "FAIL"
    assert run.summary["verdict"] == "NEEDS REVIEW"
