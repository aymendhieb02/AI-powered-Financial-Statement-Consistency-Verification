from __future__ import annotations

from pathlib import Path

from sicav_checker.extraction.engines.base import EngineResult
from sicav_checker.extraction.quality import score_extraction
from sicav_checker.extraction.section_detector import detect_sections
from sicav_checker.extraction.statement_extractor import build_document_from_sections


class CamelotTableEngine:
    name = "camelot_table"

    def extract(self, path: Path) -> EngineResult:
        warnings: list[str] = []
        text = ""
        try:
            import camelot  # type: ignore
        except Exception as exc:
            warnings.append(f"camelot_unavailable={exc.__class__.__name__}")
            return self._empty_result(path, warnings)

        try:
            tables = camelot.read_pdf(str(path), flavor="stream", pages="all")
            for table in tables:
                rows = table.df.fillna("").astype(str).values.tolist()
                text += "\n".join(" ".join(cell.strip() for cell in row if cell.strip()) for row in rows)
                text += "\n"
        except Exception as exc:
            warnings.append(f"camelot_failed={exc.__class__.__name__}")

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

    def _empty_result(self, path: Path, warnings: list[str]) -> EngineResult:
        document = build_document_from_sections(path, {}, "", self.name)
        quality = score_extraction(document, self.name, warnings)
        document.confidence = quality.confidence
        if document.metadata:
            document.metadata.confidence = quality.confidence
        return EngineResult(document=document, engine_name=self.name, quality=quality, warnings=warnings)
