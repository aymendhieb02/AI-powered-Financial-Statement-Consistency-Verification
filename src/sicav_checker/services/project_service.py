from __future__ import annotations

import json
import shutil
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from sicav_checker.assessment.decision_engine import build_decision_summary
from sicav_checker.comparison.coverage import comparison_coverage
from sicav_checker.comparison.metrics import build_metric_breakdown, build_review_items, write_comparison_debug, write_metric_debug
from sicav_checker.config import Settings, settings
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
    evidence_items: list[dict] = Field(default_factory=list)


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

    def get_document(self, project_id: str, document_id: str) -> UploadedDocumentRecord:
        safe_name = Path(document_id).name
        for document in self.list_documents(project_id):
            if document.filename == safe_name:
                return document
        raise StorageError(f"Document not found: {safe_name}")

    def get_document_path(self, project_id: str, document_id: str) -> Path:
        document = self.get_document(project_id, document_id)
        path = Path(document.path)
        if not path.exists():
            raise StorageError(f"Document file not found: {document.filename}")
        return path

    def run_verification(
        self,
        project_id: str,
        old_document_id: str | None = None,
        new_document_id: str | None = None,
    ) -> VerificationRunRecord:
        self.get_project(project_id)
        storage = StorageService(extracted_dir=self.extracted_dir(project_id), backend=self.settings.storage_backend)
        orchestrator = PipelineOrchestrator(storage_service=storage, app_settings=self.settings)
        if old_document_id and new_document_id:
            result = self._run_pair_verification(project_id, old_document_id, new_document_id, orchestrator)
        else:
            result = orchestrator.run_all(self.raw_dir(project_id), reports_dir=self.reports_dir(project_id))
        run = self._run_from_pipeline(project_id, result)
        self._write_run(run)
        return run

    def get_project_detail(self, project_id: str) -> dict:
        project = self.get_project(project_id)
        documents = self.list_documents(project_id)
        runs = self.list_runs(project_id)
        latest = runs[0] if runs else None
        payload = project.model_dump(mode="json")
        payload.update(
            {
                "document_count": len(documents),
                "latest_run_id": latest.id if latest else None,
                "latest_run_status": latest.status if latest else None,
                "latest_risk_score": latest.summary.get("risk_score") if latest else None,
                "latest_confidence": latest.summary.get("overall_confidence") if latest else None,
                "updated_at": latest.created_at if latest else project.created_at,
            }
        )
        return payload

    def list_runs(self, project_id: str) -> list[VerificationRunRecord]:
        self.get_project(project_id)
        runs_dir = self.runs_dir(project_id)
        if not runs_dir.exists():
            return []
        runs: list[VerificationRunRecord] = []
        for path in sorted(runs_dir.glob("*.json"), reverse=True):
            runs.append(VerificationRunRecord(**json.loads(path.read_text(encoding="utf-8"))))
        return runs

    def _run_pair_verification(
        self,
        project_id: str,
        old_document_id: str,
        new_document_id: str,
        orchestrator: PipelineOrchestrator,
    ) -> PipelineResult:
        import tempfile

        old_name = Path(old_document_id).name
        new_name = Path(new_document_id).name
        old_path = self.raw_dir(project_id) / old_name
        new_path = self.raw_dir(project_id) / new_name
        if not old_path.exists():
            raise StorageError(f"Old document not found: {old_name}")
        if not new_path.exists():
            raise StorageError(f"New document not found: {new_name}")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            shutil.copy(old_path, tmp_dir / old_name)
            shutil.copy(new_path, tmp_dir / new_name)
            return orchestrator.run_pair(tmp_dir, old_name, new_name, reports_dir=self.reports_dir(project_id))

    def get_run(self, project_id: str, run_id: str) -> VerificationRunRecord:
        self.get_project(project_id)
        path = self.run_path(project_id, run_id)
        if not path.exists():
            raise StorageError(f"Verification run not found: {run_id}")
        return VerificationRunRecord(**json.loads(path.read_text(encoding="utf-8")))

    def list_evidence(self, project_id: str, run_id: str) -> list[dict]:
        run = self.get_run(project_id, run_id)
        if run.evidence_items:
            return run.evidence_items
        if run.anomalies:
            return run.anomalies
        return []

    def get_evidence(self, project_id: str, run_id: str, evidence_id: str) -> dict:
        for item in self.list_evidence(project_id, run_id):
            if item.get("id") == evidence_id:
                return item
        raise StorageError(f"Evidence item not found: {evidence_id}")

    def get_document_page(self, project_id: str, document_id: str, page_number: int, evidence: dict | None = None) -> dict:
        document = self.get_document(project_id, document_id)
        path = self.get_document_path(project_id, document_id)
        safe_document = urllib.parse.quote(document.filename)
        payload = {
            "document_id": document.filename,
            "page_number": page_number,
            "source_file": str(path),
            "file_url": f"/api/projects/{project_id}/documents/{safe_document}/file",
            "image_url": f"/api/projects/{project_id}/documents/{safe_document}/pages/{page_number}/image",
            "page_width": None,
            "page_height": None,
            "statement": None,
            "section": None,
            "raw_line": None,
            "bounding_box": None,
        }
        page_width, page_height = self.get_document_page_dimensions(project_id, document_id, page_number)
        payload["page_width"] = page_width
        payload["page_height"] = page_height
        if evidence:
            is_old = Path(document_id).name == Path(evidence.get("old_document_id") or "").name
            is_new = Path(document_id).name == Path(evidence.get("new_document_id") or "").name
            old_evidence = evidence.get("old_evidence") or {}
            new_evidence = evidence.get("new_evidence") or {}
            if is_old:
                payload.update(
                    {
                        "statement": evidence.get("statement_name") or evidence.get("statement") or old_evidence.get("statement") or old_evidence.get("statement_name"),
                        "section": evidence.get("old_section") or old_evidence.get("section") or old_evidence.get("section_name") or evidence.get("statement_name") or evidence.get("statement"),
                        "raw_line": evidence.get("old_raw_line") or old_evidence.get("raw_line") or old_evidence.get("raw_text"),
                        "bounding_box": evidence.get("old_bbox") or old_evidence.get("bbox_value") or old_evidence.get("bbox_row") or old_evidence.get("bounding_box"),
                    }
                )
            elif is_new:
                payload.update(
                    {
                        "statement": evidence.get("statement_name") or evidence.get("statement") or new_evidence.get("statement") or new_evidence.get("statement_name"),
                        "section": evidence.get("new_section") or new_evidence.get("section") or new_evidence.get("section_name") or evidence.get("statement_name") or evidence.get("statement"),
                        "raw_line": evidence.get("new_raw_line") or new_evidence.get("raw_line") or new_evidence.get("raw_text"),
                        "bounding_box": evidence.get("new_bbox") or new_evidence.get("bbox_value") or new_evidence.get("bbox_row") or new_evidence.get("bounding_box"),
                    }
                )
        return payload

    def get_document_page_dimensions(self, project_id: str, document_id: str, page_number: int) -> tuple[float, float]:
        path = self.get_document_path(project_id, document_id)
        try:
            import fitz
        except ImportError as exc:
            raise StorageError("PyMuPDF is required for document page preview.") from exc
        try:
            with fitz.open(path) as pdf:
                if page_number < 1 or page_number > len(pdf):
                    raise StorageError(f"Page {page_number} not found in {Path(document_id).name}")
                page = pdf[page_number - 1]
                rect = page.rect
                return float(rect.width), float(rect.height)
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError(f"Could not inspect page {page_number} in {Path(document_id).name}: {exc}") from exc

    def render_document_page_image(self, project_id: str, document_id: str, page_number: int, scale: float = 2.0) -> bytes:
        path = self.get_document_path(project_id, document_id)
        cache_dir = self.project_dir(project_id) / "cache" / "page_images"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_name = f"{Path(document_id).stem}_page_{page_number}_scale_{str(scale).replace('.', '_')}.png"
        cache_path = cache_dir / cache_name
        if cache_path.exists():
            return cache_path.read_bytes()
        try:
            import fitz
        except ImportError as exc:
            raise StorageError("PyMuPDF is required for page image rendering.") from exc
        try:
            with fitz.open(path) as pdf:
                if page_number < 1 or page_number > len(pdf):
                    raise StorageError(f"Page {page_number} not found in {Path(document_id).name}")
                page = pdf[page_number - 1]
                matrix = fitz.Matrix(scale, scale)
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                png = pix.tobytes("png")
                cache_path.write_bytes(png)
                return png
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError(f"Could not render page {page_number} in {Path(document_id).name}: {exc}") from exc

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
        docs = sorted(result.documents, key=lambda document: document.document_year or 0)
        old_document = docs[0] if docs else None
        new_document = docs[-1] if len(docs) > 1 else old_document
        metrics = build_metric_breakdown(old_document, new_document, comparisons, validations)
        review_items = build_review_items(comparisons, old_document, new_document)
        anomalous_review_items = [item for item in review_items if item["status"] not in {"OK", "carry_forward_ok", "LABEL_RENAMED"}]

        years = [doc.document_year for doc in result.documents if doc.document_year is not None]
        old_year = min(years) if years else None
        new_year = max(years) if years else None
        company = next((doc.company for doc in result.documents if doc.company), "")
        coverage = self._coverage_summary(result)
        risk = metrics["risk"]
        decisions = build_decision_summary(docs, metrics, validations)
        extraction = decisions["extraction"]
        comparison = decisions["comparison"]
        accounting = decisions["accounting"]
        overall = decisions["overall"]
        summary = {
            "company": company,
            "old_document_year": old_year,
            "new_document_year": new_year,
            "compared_year": old_year,
            "documents_analyzed": len(result.documents),
            "pairs_checked": len({item.pair for item in comparisons}),
            "values_checked": metrics["actually_compared_values"],
            "ok_count": metrics["carry_forward_ok"],
            "mismatch_count": metrics["actual_mismatches"],
            "missing_count": metrics["missing_accounts"],
            "critical_anomalies": metrics["critical_accounting_errors"],
            "medium_anomalies": sum(1 for item in anomalous_review_items if item["severity"] == "MEDIUM"),
            "low_anomalies": sum(1 for item in anomalous_review_items if item["severity"] == "LOW"),
            "overall_confidence": metrics["extraction_confidence"],
            "extraction_confidence": metrics["extraction_confidence"],
            "accounting_health": metrics["accounting_health"],
            "risk_score": risk["score"],
            "risk_level": risk["level"],
            "risk_category": risk["category"],
            "risk_rationale": risk["rationale"],
            "extraction_status": extraction["status"],
            "extraction_reason": extraction["reason"],
            "extraction_summary": extraction["summary"],
            "comparison_status": comparison["status"],
            "comparison_reason": comparison["reason"],
            "comparison_summary": comparison["summary"],
            "accounting_status": accounting["status"],
            "accounting_reason": accounting["reason"],
            "accounting_summary": accounting["summary"],
            "verdict": overall["status"],
            "verdict_reason": overall["reason"],
            "why_verdict": decisions["why_verdict"],
            "financial_consistency": metrics["financial_consistency"],
            "financial_consistency_numerator": metrics["financial_consistency_numerator"],
            "financial_consistency_denominator": metrics["financial_consistency_denominator"],
            "extraction_coverage": metrics["extraction_coverage"],
            "extraction_coverage_numerator": metrics["extraction_coverage_numerator"],
            "extraction_coverage_raw_numerator": metrics["extraction_coverage_raw_numerator"],
            "extra_pairings": metrics["extra_pairings"],
            "extraction_coverage_denominator": metrics["extraction_coverage_denominator"],
            "structural_quality": metrics["structural_quality"],
            "actual_mismatches": metrics["actual_mismatches"],
            "missing_in_old_current": metrics["missing_in_old_current"],
            "missing_in_new_comparative": metrics["missing_in_new_comparative"],
            "new_reporting_lines": metrics["new_reporting_lines"],
            "duplicate_labels": metrics["duplicate_labels"],
            "polluted_labels": metrics["polluted_labels"],
            "merged_rows": metrics["merged_rows"],
            "hierarchy_gaps": metrics["hierarchy_gaps"],
            "low_confidence_parse": metrics["low_confidence_parse"],
            "critical_accounting_errors": metrics["critical_accounting_errors"],
            "carry_forward_ok": metrics["carry_forward_ok"],
            "carry_forward_mismatch": metrics["carry_forward_mismatch"],
            "metric_debug": metrics["metric_debug"],
            "report_paths": [str(path) for path in result.report_paths],
            **coverage,
        }
        debug_dir = self.project_dir(project_id) / "debug"
        write_metric_debug(debug_dir / "metric_debug.json", metrics, review_items)
        write_comparison_debug(debug_dir / "comparison_debug.json", review_items)
        return VerificationRunRecord(
            project_id=project_id,
            summary=summary,
            report_paths=[str(path) for path in result.report_paths],
            anomalies=anomalous_review_items,
            evidence_items=review_items,
        )

    @staticmethod
    def _overall_extraction_confidence(documents: list) -> float:
        confidence_values = [document.confidence for document in documents]
        return round(sum(confidence_values) / len(confidence_values), 4) if confidence_values else 0

    @staticmethod
    def _coverage_summary(result: PipelineResult) -> dict:
        if len(result.documents) < 2:
            return {
                "old_extracted_lines": 0,
                "new_extracted_lines": 0,
                "comparable_lines": len(result.comparisons),
                "matched_lines": 0,
                "mismatched_lines": 0,
                "missing_in_old": 0,
                "missing_in_new": 0,
                "ignored_lines": 0,
                "comparison_coverage_percentage": 0.0,
            }
        docs = sorted(result.documents, key=lambda document: document.document_year or 0)
        return comparison_coverage(docs[0], docs[-1], result.comparisons)

    def _write_projects(self, projects: list[ProjectRecord]) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(json.dumps([item.model_dump(mode="json") for item in projects], indent=2), encoding="utf-8")

    def _write_run(self, run: VerificationRunRecord) -> None:
        self.runs_dir(run.project_id).mkdir(parents=True, exist_ok=True)
        self.run_path(run.project_id, run.id).write_text(json.dumps(run.model_dump(mode="json"), indent=2), encoding="utf-8")
