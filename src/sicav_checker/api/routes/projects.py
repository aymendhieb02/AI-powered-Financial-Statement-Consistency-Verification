from __future__ import annotations

from fastapi import APIRouter, Depends

from sicav_checker.api.dependencies import get_project_service
from sicav_checker.api.schemas.api_models import ProjectCreate, ProjectResponse
from sicav_checker.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse)
def create_project(payload: ProjectCreate, service: ProjectService = Depends(get_project_service)) -> ProjectResponse:
    return ProjectResponse(**service.create_project(payload.name, payload.company, payload.description).model_dump())


@router.get("", response_model=list[ProjectResponse])
def list_projects(service: ProjectService = Depends(get_project_service)) -> list[ProjectResponse]:
    return [ProjectResponse(**project.model_dump()) for project in service.list_projects()]