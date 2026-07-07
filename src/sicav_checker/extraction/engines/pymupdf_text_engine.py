from __future__ import annotations

from pathlib import Path

from sicav_checker.extraction.engines.base import EngineResult
from sicav_checker.extraction.quality import score_extraction
from sicav_checker.extraction.section_detector import detect_sections
from sicav_checker.extraction.statement_extractor import build_document_from_sections
from sicav_checker.extraction.text_extractor import extract_text


class PyMuPDFTextEngine:
    name = "pymupdf_text"

    def extract(self, path: Path) -> EngineResult:
        text, method = extract_text(path)
        sections = detect_sections(text)
        document = build_document_from_sections(path, sections, text, method or self.name)
        warnings: list[str] = []
        if not text.strip():
            warnings.append("text_engine_returned_empty_text")
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
