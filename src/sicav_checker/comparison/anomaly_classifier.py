from __future__ import annotations

from sicav_checker.models import Severity


CRITICAL_LABELS = {
    "total_actif",
    "total_passif",
    "actif_net",
    "total_passif_et_actif_net",
    "resultat_exercice",
    "resultat_exploitation",
}
MEDIUM_FRAGMENTS = {"capital", "revenues", "revenue", "charges", "sommes_distribuables", "total"}


def classify_severity(canonical_label: str) -> Severity:
    if canonical_label in CRITICAL_LABELS:
        return Severity.CRITICAL
    if canonical_label in {"label_rename", "formatting_issue"}:
        return Severity.LOW
    if any(fragment in canonical_label for fragment in MEDIUM_FRAGMENTS):
        return Severity.MEDIUM
    return Severity.LOW
