from __future__ import annotations

import json
from pathlib import Path

from sicav_checker.models import ExtractedDocument, Statement, StatementRow


def base_documents() -> tuple[ExtractedDocument, ExtractedDocument]:
    old = ExtractedDocument(
        document_year=2024,
        source_file="2024.pdf",
        extraction_method="synthetic",
        statements={
            "bilan": Statement(
                name="bilan",
                rows=[
                    StatementRow(label="TOTAL ACTIF", canonical_label="total_actif", current_value=14339699, previous_value=12000000),
                    StatementRow(label="TOTAL PASSIF", canonical_label="total_passif", current_value=1000000, previous_value=800000),
                    StatementRow(label="ACTIF NET", canonical_label="actif_net", current_value=13339699, previous_value=11200000),
                    StatementRow(
                        label="TOTAL PASSIF ET ACTIF NET",
                        canonical_label="total_passif_et_actif_net",
                        current_value=14339699,
                        previous_value=12000000,
                    ),
                ],
            )
        },
    )
    new = ExtractedDocument(
        document_year=2025,
        source_file="2025.pdf",
        extraction_method="synthetic",
        statements={
            "bilan": Statement(
                name="bilan",
                rows=[
                    StatementRow(label="TOTAL ACTIF", canonical_label="total_actif", current_value=15000000, previous_value=14339699),
                    StatementRow(label="TOTAL PASSIF", canonical_label="total_passif", current_value=1100000, previous_value=1000000),
                    StatementRow(label="ACTIF NET", canonical_label="actif_net", current_value=13900000, previous_value=13339699),
                    StatementRow(
                        label="TOTAL PASSIF ET ACTIF NET",
                        canonical_label="total_passif_et_actif_net",
                        current_value=15000000,
                        previous_value=14339699,
                    ),
                ],
            )
        },
    )
    return old, new


def corrupted_documents(kind: str) -> tuple[ExtractedDocument, ExtractedDocument]:
    old, new = base_documents()
    rows = new.statements["bilan"].rows
    if kind == "changed_amount":
        rows[0].previous_value = 14339600
    elif kind == "missing_row":
        new.statements["bilan"].rows = [row for row in rows if row.canonical_label != "total_actif"]
    elif kind == "wrong_sign":
        rows[2].previous_value = -13339699
    elif kind == "swapped_columns":
        for row in rows:
            row.current_value, row.previous_value = row.previous_value, row.current_value
    elif kind == "renamed_label":
        rows[0].label = "TOTAL DES ACTIFS"
        rows[0].canonical_label = "total_actifs"
    elif kind == "wrong_total":
        old.statements["bilan"].rows[3].current_value = 14000000
    elif kind == "decimal_issue":
        rows[0].previous_value = 14339.699
    else:
        raise ValueError(f"Unknown corruption kind: {kind}")
    return old, new


def create_corrupted_json(output_dir: str | Path) -> list[Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for kind in ["changed_amount", "missing_row", "wrong_sign", "swapped_columns", "renamed_label", "wrong_total", "decimal_issue"]:
        old, new = corrupted_documents(kind)
        path = out / f"{kind}.json"
        path.write_text(json.dumps({"old": old.model_dump(mode="json"), "new": new.model_dump(mode="json")}, indent=2), encoding="utf-8")
        paths.append(path)
    return paths
