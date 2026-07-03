from __future__ import annotations

from typing import Protocol

from sicav_checker.models import Evidence, VerificationRun
from sicav_checker.rules.rule_registry import AccountingRule


class RuleRepository(Protocol):
    def list_rules(self) -> list[AccountingRule]: ...


class VerificationRepository(Protocol):
    def save_run(self, run: VerificationRun) -> None: ...
    def list_runs(self, project: str | None = None) -> list[VerificationRun]: ...
    def get_run(self, run_id: str) -> VerificationRun | None: ...


class ProjectRepository(Protocol):
    def list_projects(self) -> list[dict]: ...


class EvidenceRepository(Protocol):
    def save_evidence(self, evidence: Evidence) -> None: ...
    def get_evidence(self, line_id: str) -> Evidence | None: ...
