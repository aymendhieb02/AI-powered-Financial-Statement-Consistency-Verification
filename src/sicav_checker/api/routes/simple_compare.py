from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from sicav_checker.api.dependencies import get_project_service
from sicav_checker.services.project_service import ProjectService

router = APIRouter(tags=["simple-compare"])


@router.post("/compare-two-documents")
async def compare_two_documents(
    old_document: UploadFile = File(...),
    new_document: UploadFile = File(...),
    service: ProjectService = Depends(get_project_service),
) -> dict:
    """Upload two annual PDFs and run the existing pair-comparison pipeline."""
    project = service.create_project(
        name="Two-document comparison",
        company="SICAV",
        description="Created from the simplified compare workflow.",
    )
    old_content = await old_document.read()
    new_content = await new_document.read()
    old_record = service.save_upload(project.id, old_document.filename or "old_document.pdf", old_content)
    new_record = service.save_upload(project.id, new_document.filename or "new_document.pdf", new_content)
    run = service.run_verification(project.id, old_record.filename, new_record.filename)
    return {
        "project_id": project.id,
        "run_id": run.id,
        "summary": run.summary,
        "anomalies": run.anomalies,
        "report_paths": run.report_paths,
        "old_document": old_record.model_dump(mode="json"),
        "new_document": new_record.model_dump(mode="json"),
    }
