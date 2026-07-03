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