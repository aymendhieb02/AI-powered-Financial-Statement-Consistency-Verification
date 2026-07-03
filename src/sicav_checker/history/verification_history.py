from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sicav_checker.confidence.confidence_engine import ConfidenceEngine
from sicav_checker.models import ComparisonResult, FinancialDocument, ValidationResult, VerificationRun
from sicav_checker.repositories.json_repositories import JsonVerificationRepository


class VerificationHistoryService:
    def __init__(self, repository: JsonVerificationRepository | None = None) -> None:
        self.repository = repository or JsonVerificationRepository()

    def create_run(self, project: str, documents: list[FinancialDocument], comparisons: list[ComparisonResult], validations: list[ValidationResult], report_paths: list[str]) -> VerificationRun:
        confidence = ConfidenceEngine().aggregate(documents, comparisons, validations)
        previous = self.repository.list_runs(project)
        risk = sum(1 for item in comparisons if item.status != "OK")
        old_risk = previous[-1].results.get("risk_score", 0) if previous else 0
        old_conf = previous[-1].confidence.overall if previous and previous[-1].confidence else confidence.overall
        anomaly_keys = {f"{item.pair}:{item.canonical_label}:{item.status}" for item in comparisons if item.status != "OK"}
        previous_keys = set(previous[-1].results.get("anomaly_keys", [])) if previous else set()
        run = VerificationRun(
            run_id=uuid4().hex,
            timestamp=datetime.now(timezone.utc).isoformat(),
            project=project,
            documents=[doc.source_file for doc in documents],
            versions={"finverify": "0.1.0"},
            settings={},
            results={"comparisons": len(comparisons), "validations": len(validations), "risk_score": risk, "anomaly_keys": sorted(anomaly_keys)},
            report_paths=report_paths,
            confidence=confidence,
            new_anomalies=sorted(anomaly_keys - previous_keys),
            resolved_anomalies=sorted(previous_keys - anomaly_keys),
            changed_risk_score=risk - old_risk,
            changed_confidence=confidence.overall - old_conf,
        )
        self.repository.save_run(run)
        return run

    def list_runs(self, project: str | None = None) -> list[VerificationRun]:
        return self.repository.list_runs(project)

    def get_run(self, run_id: str) -> VerificationRun | None:
        return self.repository.get_run(run_id)
