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