from pathlib import Path

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
    from sicav_checker.domain.models import ComparisonResult, Severity, Status
    from sicav_checker.pipeline.orchestrator import PipelineResult

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
