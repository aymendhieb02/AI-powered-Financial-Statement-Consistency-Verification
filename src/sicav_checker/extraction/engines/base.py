from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from sicav_checker.extraction.quality import ExtractionQualityReport
from sicav_checker.models import ExtractedDocument


@dataclass(slots=True)
class EngineResult:
    document: ExtractedDocument
    engine_name: str
    quality: ExtractionQualityReport
    warnings: list[str] = field(default_factory=list)
    debug: dict = field(default_factory=dict)


class ExtractionEngine(Protocol):
    name: str

    def extract(self, path: Path) -> EngineResult:
        ...
