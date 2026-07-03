from __future__ import annotations

from fastapi import APIRouter, HTTPException

from sicav_checker.history.verification_history import VerificationHistoryService
from sicav_checker.repositories.json_repositories import JsonEvidenceRepository
from sicav_checker.rules.rule_engine import RuleEngine

router = APIRouter(tags=["enterprise"])


@router.get("/rules")
def list_rules() -> list[dict]:
    return [rule.model_dump(mode="json") for rule in RuleEngine().list_rules()]


@router.post("/rules/validate")
def validate_rules() -> dict:
    return {"status": "ok", "rules_loaded": len(RuleEngine().list_rules())}


@router.get("/verification/history")
def verification_history() -> list[dict]:
    return [run.model_dump(mode="json") for run in VerificationHistoryService().list_runs()]


@router.get("/verification/{run_id}")
def verification_run(run_id: str) -> dict:
    run = VerificationHistoryService().get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run.model_dump(mode="json")


@router.get("/verification/{run_id}/confidence")
def verification_confidence(run_id: str) -> dict:
    run = VerificationHistoryService().get_run(run_id)
    if run is None or run.confidence is None:
        raise HTTPException(status_code=404, detail="Confidence not found")
    return run.confidence.model_dump(mode="json")


@router.get("/verification/{run_id}/evidence/{line_id}")
def verification_evidence(run_id: str, line_id: str) -> dict:
    evidence = JsonEvidenceRepository().get_evidence(line_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence.model_dump(mode="json")
