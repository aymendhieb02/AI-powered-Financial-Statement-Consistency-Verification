import importlib.util

import pytest

pytestmark = pytest.mark.skipif(importlib.util.find_spec("fastapi") is None, reason="FastAPI is not installed")


def test_api_health() -> None:
    from fastapi.testclient import TestClient
    from sicav_checker.api.main import app

    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_project_upload_and_verification(tmp_path, monkeypatch) -> None:
    from fastapi.testclient import TestClient
    from sicav_checker.api import dependencies
    from sicav_checker.api.main import app
    from sicav_checker.services.project_service import ProjectService

    service = ProjectService(root_dir=tmp_path)
    app.dependency_overrides[dependencies.get_project_service] = lambda: service
    client = TestClient(app)

    project = client.post("/api/projects", json={"name": "MAXULA", "company": "MAXULA", "description": "Audit"}).json()
    upload = client.post(
        f"/api/projects/{project['id']}/documents/upload",
        files=[("files", ("2025_maxula.pdf", b"%PDF-1.4 synthetic", "application/pdf"))],
    )
    run = client.post(f"/api/projects/{project['id']}/verification/run").json()
    summary = client.get(f"/api/projects/{project['id']}/verification/{run['run_id']}")

    assert upload.status_code == 200
    assert run["status"] == "completed"
    assert summary.status_code == 200
    app.dependency_overrides.clear()


def test_api_get_project_and_pair_verification(tmp_path) -> None:
    from fastapi.testclient import TestClient
    from sicav_checker.api import dependencies
    from sicav_checker.api.main import app
    from sicav_checker.services.project_service import ProjectService

    service = ProjectService(root_dir=tmp_path)
    app.dependency_overrides[dependencies.get_project_service] = lambda: service
    client = TestClient(app)

    project = client.post("/api/projects", json={"name": "MAXULA", "company": "MAXULA", "description": "Audit"}).json()
    client.post(
        f"/api/projects/{project['id']}/documents/upload",
        files=[
            ("files", ("2024_maxula.pdf", b"%PDF-1.4 synthetic", "application/pdf")),
            ("files", ("2025_maxula.pdf", b"%PDF-1.4 synthetic", "application/pdf")),
        ],
    )
    detail = client.get(f"/api/projects/{project['id']}")
    run = client.post(
        f"/api/projects/{project['id']}/verification/run",
        json={"old_document_id": "2024_maxula.pdf", "new_document_id": "2025_maxula.pdf"},
    ).json()
    anomalies = client.get(f"/api/projects/{project['id']}/verification/{run['run_id']}/anomalies")

    assert detail.status_code == 200
    assert detail.json()["document_count"] == 2
    assert run["run_id"]
    assert anomalies.status_code == 200
    app.dependency_overrides.clear()


def test_api_evidence_routes_return_detail(tmp_path, monkeypatch) -> None:
    from fastapi.testclient import TestClient
    from sicav_checker.api import dependencies
    from sicav_checker.api.main import app
    from sicav_checker.services.project_service import ProjectService, VerificationRunRecord

    service = ProjectService(root_dir=tmp_path)
    project = service.create_project("MAXULA", "MAXULA", "Audit")
    service.save_upload(project.id, "2024_maxula.pdf", b"%PDF-1.4 synthetic")
    service.save_upload(project.id, "2025_maxula.pdf", b"%PDF-1.4 synthetic")
    run = VerificationRunRecord(
        project_id=project.id,
        anomalies=[],
        evidence_items=[
            {
                "id": "ev-1",
                "canonical_label": "bilan__total_actif",
                "status": "carry_forward_mismatch",
                "status_group": "financial",
                "severity": "CRITICAL",
                "statement_name": "bilan",
                "old_document_id": "2024_maxula.pdf",
                "new_document_id": "2025_maxula.pdf",
                "old_page": 4,
                "new_page": 5,
                "old_raw_line": "TOTAL ACTIF 100",
                "new_raw_line": "TOTAL ACTIF 90",
                "old_bbox": [10, 20, 110, 40],
                "new_bbox": [12, 22, 112, 42],
                "issue_type": "financial_mismatch",
                "duplicate_candidates": [
                    {"document_id": "2024_maxula.pdf", "page": 4, "section_name": "bilan", "raw_text": "TOTAL ACTIF 100"}
                ],
            }
        ],
    )
    service._write_run(run)
    monkeypatch.setattr(service, "get_document_page_dimensions", lambda *args, **kwargs: (595.0, 842.0))
    app.dependency_overrides[dependencies.get_project_service] = lambda: service
    client = TestClient(app)

    evidence_list = client.get(f"/api/projects/{project.id}/verification/{run.id}/evidence")
    evidence_detail = client.get(f"/api/projects/{project.id}/verification/{run.id}/evidence/ev-1")
    old_page = client.get(f"/api/projects/{project.id}/documents/2024_maxula.pdf/page/4", params={"run_id": run.id, "evidence_id": "ev-1"})

    assert evidence_list.status_code == 200
    assert evidence_list.json()["total"] == 1
    assert evidence_detail.status_code == 200
    assert evidence_detail.json()["old_raw_line"] == "TOTAL ACTIF 100"
    assert evidence_detail.json()["duplicate_candidates"][0]["raw_text"] == "TOTAL ACTIF 100"
    assert old_page.status_code == 200
    assert old_page.json()["raw_line"] == "TOTAL ACTIF 100"
    assert old_page.json()["page_width"] == 595.0
    app.dependency_overrides.clear()


def test_api_document_page_image_returns_png(tmp_path, monkeypatch) -> None:
    from fastapi.testclient import TestClient
    from sicav_checker.api import dependencies
    from sicav_checker.api.main import app
    from sicav_checker.services.project_service import ProjectService

    service = ProjectService(root_dir=tmp_path)
    project = service.create_project("MAXULA", "MAXULA", "Audit")
    service.save_upload(project.id, "2024_maxula.pdf", b"%PDF-1.4 synthetic")
    monkeypatch.setattr(service, "render_document_page_image", lambda *args, **kwargs: b"fake-png")
    app.dependency_overrides[dependencies.get_project_service] = lambda: service
    client = TestClient(app)

    response = client.get(f"/api/projects/{project.id}/documents/2024_maxula.pdf/pages/1/image")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == b"fake-png"
    app.dependency_overrides.clear()
