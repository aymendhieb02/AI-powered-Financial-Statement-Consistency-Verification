from __future__ import annotations

from sicav_checker.models import Severity, Status


CRITICAL_CARRY_FORWARD_LABELS = {
    "total_actif",
    "actif_net",
    "total_passif_actif_net",
    "total_passif_et_actif_net",
}
MEDIUM_FRAGMENTS = {"capital", "revenus", "revenu", "charges", "sommes_distribuables", "total"}


def classify_severity(canonical_label: str, status: Status | str | None = None) -> Severity:
    status_value = str(status or "")
    if status_value in {Status.DUPLICATE_LABEL, Status.PARSE_LOW_CONFIDENCE, Status.LOW_CONFIDENCE_EXTRACTION}:
        return Severity.LOW
    if status_value in {
        Status.CARRY_FORWARD_MISMATCH,
        Status.MISSING_IN_NEW_COMPARATIVE,
        Status.MISSING_IN_OLD_CURRENT,
        Status.MISSING_IN_NEW,
        Status.MISSING_IN_OLD,
        Status.MISMATCH,
    } and canonical_label in CRITICAL_CARRY_FORWARD_LABELS:
        return Severity.CRITICAL
    if any(fragment in canonical_label for fragment in MEDIUM_FRAGMENTS):
        return Severity.MEDIUM
    return Severity.LOW
