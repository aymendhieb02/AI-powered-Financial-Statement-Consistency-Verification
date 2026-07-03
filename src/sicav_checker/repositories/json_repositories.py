from __future__ import annotations

import json
from pathlib import Path

from sicav_checker.models import Evidence, VerificationRun


class JsonVerificationRepository:
    def __init__(self, root: Path = Path("data/verification_history")) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def save_run(self, run: VerificationRun) -> None:
        (self.root / f"{run.run_id}.json").write_text(json.dumps(run.model_dump(mode="json"), indent=2), encoding="utf-8")

    def list_runs(self, project: str | None = None) -> list[VerificationRun]:
        runs = [VerificationRun(**json.loads(path.read_text(encoding="utf-8"))) for path in sorted(self.root.glob("*.json"))]
        return [run for run in runs if project is None or run.project == project]

    def get_run(self, run_id: str) -> VerificationRun | None:
        path = self.root / f"{run_id}.json"
        return VerificationRun(**json.loads(path.read_text(encoding="utf-8"))) if path.exists() else None


class JsonEvidenceRepository:
    def __init__(self, root: Path = Path("data/evidence")) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def save_evidence(self, evidence: Evidence) -> None:
        if evidence.line_id:
            (self.root / f"{evidence.line_id}.json").write_text(json.dumps(evidence.model_dump(mode="json"), indent=2), encoding="utf-8")

    def get_evidence(self, line_id: str) -> Evidence | None:
        path = self.root / f"{line_id}.json"
        return Evidence(**json.loads(path.read_text(encoding="utf-8"))) if path.exists() else None
