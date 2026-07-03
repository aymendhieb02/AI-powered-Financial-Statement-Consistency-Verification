from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from sicav_checker.api.dependencies import get_project_service
from sicav_checker.services.project_service import ProjectService

router = APIRouter(prefix="/projects/{project_id}/reports", tags=["reports"])


@router.get("/{run_id}/excel")
def download_excel(project_id: str, run_id: str, service: ProjectService = Depends(get_project_service)) -> FileResponse:
    path = service.report_file(project_id, run_id, "excel")
    return FileResponse(path, filename=path.name, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/{run_id}/json")
def download_json(project_id: str, run_id: str, service: ProjectService = Depends(get_project_service)) -> FileResponse:
    path = service.report_file(project_id, run_id, "json")
    return FileResponse(path, filename=path.name, media_type="application/json")