from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from sicav_checker.api.dependencies import get_project_service
from sicav_checker.api.schemas.api_models import UploadResponse, UploadedDocument
from sicav_checker.services.project_service import ProjectService

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])


@router.post("/upload", response_model=UploadResponse)
async def upload_documents(project_id: str, files: list[UploadFile] = File(...), service: ProjectService = Depends(get_project_service)) -> UploadResponse:
    uploaded: list[UploadedDocument] = []
    failed: list[dict] = []
    for file in files:
        try:
            content = await file.read()
            record = service.save_upload(project_id, file.filename or "document.pdf", content)
            uploaded.append(UploadedDocument(**record.model_dump()))
        except Exception as exc:
            failed.append({"filename": file.filename, "error": str(exc)})
    return UploadResponse(uploaded=uploaded, failed=failed)


@router.get("", response_model=list[UploadedDocument])
def list_documents(project_id: str, service: ProjectService = Depends(get_project_service)) -> list[UploadedDocument]:
    return [UploadedDocument(**document.model_dump()) for document in service.list_documents(project_id)]