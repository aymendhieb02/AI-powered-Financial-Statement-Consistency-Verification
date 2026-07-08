from __future__ import annotations

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse, Response

from sicav_checker.api.dependencies import get_project_service
from sicav_checker.api.schemas.api_models import DocumentPageResponse, UploadResponse, UploadedDocument
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


@router.get("/{document_id}/file")
def get_document_file(project_id: str, document_id: str, service: ProjectService = Depends(get_project_service)) -> FileResponse:
    path = service.get_document_path(project_id, document_id)
    return FileResponse(path, media_type="application/pdf", filename=path.name)


@router.get("/{document_id}/page/{page_number}", response_model=DocumentPageResponse)
def get_document_page(
    project_id: str,
    document_id: str,
    page_number: int,
    run_id: str | None = None,
    evidence_id: str | None = None,
    service: ProjectService = Depends(get_project_service),
) -> DocumentPageResponse:
    evidence = service.get_evidence(project_id, run_id, evidence_id) if run_id and evidence_id else None
    return DocumentPageResponse(**service.get_document_page(project_id, document_id, page_number, evidence))


@router.get("/{document_id}/pages/{page_number}/image")
def get_document_page_image(
    project_id: str,
    document_id: str,
    page_number: int,
    scale: float = Query(2.0, ge=0.5, le=4.0),
    service: ProjectService = Depends(get_project_service),
) -> Response:
    png = service.render_document_page_image(project_id, document_id, page_number, scale=scale)
    return Response(content=png, media_type="image/png")
