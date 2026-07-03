from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from sicav_checker.api.dependencies import get_project_service
from sicav_checker.api.schemas.api_models import PaginatedAnomalies, VerificationRunResponse, VerificationSummary
from sicav_checker.services.project_service import ProjectService

router = APIRouter(prefix="/projects/{project_id}/verification", tags=["verification"])


@router.post("/run", response_model=VerificationRunResponse)
def run_verification(project_id: str, service: ProjectService = Depends(get_project_service)) -> VerificationRunResponse:
    run = service.run_verification(project_id)
    return VerificationRunResponse(run_id=run.id, status=run.status)


@router.get("/{run_id}", response_model=VerificationSummary)
def get_verification(project_id: str, run_id: str, service: ProjectService = Depends(get_project_service)) -> VerificationSummary:
    run = service.get_run(project_id, run_id)
    return VerificationSummary(run_id=run.id, status=run.status, **run.summary)


@router.get("/{run_id}/anomalies", response_model=PaginatedAnomalies)
def get_anomalies(project_id: str, run_id: str, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=500), service: ProjectService = Depends(get_project_service)) -> PaginatedAnomalies:
    run = service.get_run(project_id, run_id)
    start = (page - 1) * page_size
    end = start + page_size
    return PaginatedAnomalies(items=run.anomalies[start:end], total=len(run.anomalies), page=page, page_size=page_size)