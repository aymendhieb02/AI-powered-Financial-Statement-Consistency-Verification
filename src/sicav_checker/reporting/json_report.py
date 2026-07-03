from __future__ import annotations

import json
from pathlib import Path

from sicav_checker.models import ComparisonResult, ExtractedDocument, InternalValidationResult


def write_json_report(
    path: str | Path,
    documents: list[ExtractedDocument],
    comparisons: list[ComparisonResult],
    validations: list[InternalValidationResult],
    missing_years: list[int],
) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": {
            "documents": len(documents),
            "cross_year_checks": len(comparisons),
            "internal_validation_checks": len(validations),
            "anomalies": sum(1 for item in comparisons + validations if item.status != "OK"),
            "missing_years": missing_years,
        },
        "documents": [doc.model_dump(mode="json") for doc in documents],
        "cross_year_checks": [item.model_dump(mode="json") for item in comparisons],
        "internal_validation": [item.model_dump(mode="json") for item in validations],
        "missing_years": missing_years,
    }
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return output
