from __future__ import annotations

from pathlib import Path

from sicav_checker.extraction.engines.base import EngineResult
from sicav_checker.extraction.layout_section_extractor import extract_layout_sections
from sicav_checker.extraction.quality import score_extraction
from sicav_checker.extraction.statement_extractor import build_document_from_sections


class PdfplumberLayoutEngine:
    name = "pdfplumber_layout"

    def extract(self, path: Path) -> EngineResult:
        sections, text = extract_layout_sections(path)
        warnings: list[str] = []
        if not sections:
            warnings.append("layout_engine_detected_no_sections")
        document = build_document_from_sections(path, sections, text, self.name)
        quality = score_extraction(document, self.name, warnings)
        document.confidence = quality.confidence
        if document.metadata:
            document.metadata.confidence = quality.confidence
        return EngineResult(
            document=document,
            engine_name=self.name,
            quality=quality,
            warnings=warnings,
            debug={"text_length": len(text), "section_count": len(sections)},
        )
