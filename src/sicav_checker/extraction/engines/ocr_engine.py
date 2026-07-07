from __future__ import annotations

from pathlib import Path

from sicav_checker.extraction.engines.base import EngineResult
from sicav_checker.extraction.ocr_fallback import extract_with_ocr
from sicav_checker.extraction.quality import score_extraction
from sicav_checker.extraction.section_detector import detect_sections
from sicav_checker.extraction.statement_extractor import build_document_from_sections


class OCREngine:
    name = "ocr"

    def extract(self, path: Path) -> EngineResult:
        warnings: list[str] = []
        text = extract_with_ocr(path)
        if not text.strip():
            warnings.append("ocr_returned_empty_text")
        sections = detect_sections(text)
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
