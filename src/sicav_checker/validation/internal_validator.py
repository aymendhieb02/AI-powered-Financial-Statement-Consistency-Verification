from __future__ import annotations

from math import isclose

from sicav_checker.models import ExtractedDocument, InternalValidationResult, Severity, Status


def validate_document(doc: ExtractedDocument, tolerance: float = 0.001) -> list[InternalValidationResult]:
    results: list[InternalValidationResult] = []
    bilan = doc.statements.get("bilan")
    if not bilan:
        return results

    rows = {row.canonical_label: row for row in bilan.rows}
    total_actif = rows.get("total_actif")
    total_passif_actif_net = rows.get("total_passif_et_actif_net")
    total_passif = rows.get("total_passif")
    actif_net = rows.get("actif_net")

    if total_actif and total_passif_actif_net:
        _append_rule(results, doc.document_year, "bilan", "TOTAL ACTIF = TOTAL PASSIF ET ACTIF NET", total_passif_actif_net.current_value, total_actif.current_value, tolerance)

    if total_actif and total_passif and actif_net:
        expected = None
        if total_passif.current_value is not None and actif_net.current_value is not None:
            expected = float(total_passif.current_value) + float(actif_net.current_value)
        _append_rule(results, doc.document_year, "bilan", "TOTAL ACTIF = TOTAL PASSIF + ACTIF NET", expected, total_actif.current_value, tolerance)

    return results


def _append_rule(
    results: list[InternalValidationResult],
    year: int,
    statement: str,
    rule: str,
    expected: float | int | None,
    actual: float | int | None,
    tolerance: float,
) -> None:
    ok = expected is not None and actual is not None and isclose(float(expected), float(actual), abs_tol=tolerance)
    delta = None if expected is None or actual is None else float(actual) - float(expected)
    results.append(
        InternalValidationResult(
            document_year=year,
            statement=statement,
            rule=rule,
            status=Status.OK if ok else Status.MISMATCH,
            severity=Severity.CRITICAL,
            expected=expected,
            actual=actual,
            delta=delta,
        )
    )
