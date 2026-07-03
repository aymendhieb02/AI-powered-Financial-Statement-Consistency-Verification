from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from sicav_checker.config import Settings, settings
from sicav_checker.domain.models import ComparisonReport
from sicav_checker.exceptions import StorageError
from sicav_checker.normalization.year_detector import detect_year_from_filename
from sicav_checker.pipeline.orchestrator import PipelineOrchestrator, PipelineResult
from sicav_checker.services.storage_service import StorageService


class ProjectRecord(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str
    company: str
    description: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class UploadedDocumentRecord(BaseModel):
    filename: str
    size: int
    detected_year: int | None = None
    status: str = "uploaded"
    path: str


class VerificationRunRecord(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    project_id: str
    status: str = "completed"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    summary: dict = Field(default_factory=dict)
    report_paths: list[str] = Field(default_factory=list)
    anomalies: list[dict] = Field(default_factory=list)


class ProjectService:
    """Local project workspace service for API clients."""

    def __init__(self, root_dir: Path = Path("data/projects"), app_settings: Settings = settings) -> None:
        self.root_dir = root_dir
        self.settings = app_settings
        self.root_dir.mkdir(parents=True, exist_ok=True)

    @property
    def index_path(self) -> Path:
        return self.root_dir / "projects.json"

    def create_project(self, name: str, company: str, description: str = "") -> ProjectRecord:
        projects = self.list_projects()
        project = ProjectRecord(name=name, company=company, description=description)
        projects.append(project)
        self._write_projects(projects)
        self.project_dir(project.id).mkdir(parents=True, exist_ok=True)
        self.raw_dir(project.id).mkdir(parents=True, exist_ok=True)
        self.extracted_dir(project.id).mkdir(parents=True, exist_ok=True)
        self.reports_dir(project.id).mkdir(parents=True, exist_ok=True)
        return project

    def list_projects(self) -> list[ProjectRecord]:
        if not self.index_path.exists():
            return []
        return [ProjectRecord(**item) for item in json.loads(self.index_path.read_text(encoding="utf-8"))]

    def get_project(self, project_id: str) -> ProjectRecord:
        for project in self.list_projects():
            if project.id == project_id:
                return project
        raise StorageError(f"Project not found: {project_id}")

    def save_upload(self, project_id: str, filename: str, content: bytes) -> UploadedDocumentRecord:
        self.get_project(project_id)
        safe_name = Path(filename).name
        if not safe_name.lower().endswith(".pdf"):
            raise StorageError(f"Only PDF uploads are supported: {filename}")
        target = self.raw_dir(project_id) / safe_name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return UploadedDocumentRecord(
            filename=safe_name,
            size=len(content),
            detected_year=detect_year_from_filename(safe_name),
            path=str(target),
        )

    def list_documents(self, project_id: str) -> list[UploadedDocumentRecord]:
        self.get_project(project_id)
        documents: list[UploadedDocumentRecord] = []
        for path in sorted(self.raw_dir(project_id).glob("*.pdf")):
            documents.append(
                UploadedDocumentRecord(
                    filename=path.name,
                    size=path.stat().st_size,
                    detected_year=detect_year_from_filename(path.name),
                    path=str(path),
                )
            )
        return documents

    def run_verification(self, project_id: str) -> VerificationRunRecord:
        self.get_project(project_id)
        storage = StorageService(extracted_dir=self.extracted_dir(project_id), backend=self.settings.storage_backend)
        orchestrator = PipelineOrchestrator(storage_service=storage, app_settings=self.settings)
        result = orchestrator.run_all(self.raw_dir(project_id), reports_dir=self.reports_dir(project_id))
        run = self._run_from_pipeline(project_id, result)
        self._write_run(run)
        return run

    def get_run(self, project_id: str, run_id: str) -> VerificationRunRecord:
        self.get_project(project_id)
        path = self.run_path(project_id, run_id)
        if not path.exists():
            raise StorageError(f"Verification run not found: {run_id}")
        return VerificationRunRecord(**json.loads(path.read_text(encoding="utf-8")))

    def project_dir(self, project_id: str) -> Path:
        return self.root_dir / project_id

    def raw_dir(self, project_id: str) -> Path:
        return self.project_dir(project_id) / "raw_pdfs"

    def extracted_dir(self, project_id: str) -> Path:
        return self.project_dir(project_id) / "extracted_json"

    def reports_dir(self, project_id: str) -> Path:
        return self.project_dir(project_id) / "reports"

    def runs_dir(self, project_id: str) -> Path:
        return self.project_dir(project_id) / "runs"

    def run_path(self, project_id: str, run_id: str) -> Path:
        return self.runs_dir(project_id) / f"{run_id}.json"

    def report_file(self, project_id: str, run_id: str, kind: str) -> Path:
        run = self.get_run(project_id, run_id)
        suffix = ".xlsx" if kind == "excel" else ".json"
        for item in run.report_paths:
            path = Path(item)
            if path.suffix.lower() == suffix:
                return path
        raise StorageError(f"Report not found for run {run_id}: {kind}")

    def _run_from_pipeline(self, project_id: str, result: PipelineResult) -> VerificationRunRecord:
        comparisons = result.comparisons
        validations = result.validations
        non_ok = [item for item in comparisons if item.status != "OK"]
        critical = sum(1 for item in non_ok if item.severity == "CRITICAL")
        medium = sum(1 for item in non_ok if item.severity == "MEDIUM")
        low = sum(1 for item in non_ok if item.severity == "LOW")
        risk_score = min(100, critical * 25 + medium * 10 + low * 3)
        missing = sum(1 for item in comparisons if "MISSING" in str(item.status))
        summary = {
            "documents_analyzed": len(result.documents),
            "pairs_checked": len({item.pair for item in comparisons}),
            "values_checked": len(comparisons),
            "ok_count": sum(1 for item in comparisons if item.status == "OK"),
            "mismatch_count": sum(1 for item in comparisons if item.status == "MISMATCH"),
            "missing_count": missing,
            "critical_anomalies": critical,
            "medium_anomalies": medium,
            "low_anomalies": low,
            "risk_score": risk_score,
            "report_paths": [str(path) for path in result.report_paths],
        }
        return VerificationRunRecord(
            project_id=project_id,
            summary=summary,
            report_paths=[str(path) for path in result.report_paths],
            anomalies=[item.model_dump(mode="json") for item in non_ok],
        )

    def _write_projects(self, projects: list[ProjectRecord]) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(json.dumps([item.model_dump(mode="json") for item in projects], indent=2), encoding="utf-8")

    def _write_run(self, run: VerificationRunRecord) -> None:
        self.runs_dir(run.project_id).mkdir(parents=True, exist_ok=True)
        self.run_path(run.project_id, run.id).write_text(json.dumps(run.model_dump(mode="json"), indent=2), encoding="utf-8")