from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class Status(str, Enum):
    OK = "OK"
    MISMATCH = "MISMATCH"
    MISSING_IN_OLD = "MISSING_IN_OLD"
    MISSING_IN_NEW = "MISSING_IN_NEW"
    LABEL_RENAMED = "LABEL_RENAMED"
    LOW_CONFIDENCE_EXTRACTION = "LOW_CONFIDENCE_EXTRACTION"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class StatementRow(BaseModel):
    label: str
    canonical_label: str
    current_value: float | int | None = None
    previous_value: float | int | None = None
    page: int | None = None
    confidence: float = 1.0


class Statement(BaseModel):
    name: str
    rows: list[StatementRow] = Field(default_factory=list)


class ExtractedDocument(BaseModel):
    company: str = "MAXULA PLACEMENT SICAV"
    document_year: int
    source_file: str
    extraction_method: str
    statements: dict[str, Statement] = Field(default_factory=dict)
    pages: list[int] = Field(default_factory=list)
    confidence: float = 1.0

    @classmethod
    def from_path(cls, path: Path, year: int, statements: dict[str, Statement] | None = None) -> "ExtractedDocument":
        return cls(document_year=year, source_file=str(path), extraction_method="synthetic", statements=statements or {})


class ComparisonResult(BaseModel):
    pair: str
    year: int
    statement: str
    old_label: str | None
    new_label: str | None
    canonical_label: str
    old_value: float | int | None
    new_value: float | int | None
    status: Status
    severity: Severity
    delta: float | None = None
    confidence: float = 1.0
    note: str = ""


class InternalValidationResult(BaseModel):
    document_year: int
    statement: str
    rule: str
    status: Status
    severity: Severity
    expected: float | int | None = None
    actual: float | int | None = None
    delta: float | None = None
    note: str = ""


def model_dump_jsonable(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")
