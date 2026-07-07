from __future__ import annotations

import json
from pathlib import Path

from sicav_checker.core.logging import logger
from sicav_checker.extraction.engines import (
    CamelotTableEngine,
    EngineResult,
    ExtractionEngine,
    OCREngine,
    PdfplumberLayoutEngine,
    PyMuPDFTextEngine,
)
from sicav_checker.extraction.quality import score_extraction
from sicav_checker.extraction.statement_extractor import build_document_from_sections
from sicav_checker.models import ExtractedDocument


class ExtractionManager:
    """Coordinates extraction engines and selects the highest-quality result."""

    def __init__(
        self,
        text_engine: ExtractionEngine | None = None,
        layout_engine: ExtractionEngine | None = None,
        camelot_engine: ExtractionEngine | None = None,
        ocr_engine: ExtractionEngine | None = None,
        good_threshold: float = 0.72,
    ) -> None:
        self.text_engine = text_engine or PyMuPDFTextEngine()
        self.layout_engine = layout_engine or PdfplumberLayoutEngine()
        self.camelot_engine = camelot_engine or CamelotTableEngine()
        self.ocr_engine = ocr_engine or OCREngine()
        self.good_threshold = good_threshold

    def extract(self, path: str | Path) -> ExtractedDocument:
        pdf_path = Path(path)
        results: list[EngineResult] = []

        text_result = self._run_engine(self.text_engine, pdf_path)
        results.append(text_result)
        if text_result.quality.score >= self.good_threshold:
            self._write_debug(pdf_path, results, text_result)
            return self._finalize(text_result)

        layout_result = self._run_engine(self.layout_engine, pdf_path)
        results.append(layout_result)
        if layout_result.quality.score >= self.good_threshold:
            self._write_debug(pdf_path, results, layout_result)
            return self._finalize(layout_result)

        camelot_result = self._run_engine(self.camelot_engine, pdf_path)
        results.append(camelot_result)

        if self._should_try_ocr(text_result, layout_result, camelot_result):
            results.append(self._run_engine(self.ocr_engine, pdf_path))

        winner = max(results, key=lambda result: result.quality.score)
        self._write_debug(pdf_path, results, winner)
        return self._finalize(winner)

    def _run_engine(self, engine: ExtractionEngine, path: Path) -> EngineResult:
        try:
            result = engine.extract(path)
            logger.info("Extraction engine result file={} engine={} score={:.3f}", path.name, result.engine_name, result.quality.score)
            return result
        except Exception as exc:
            engine_name = getattr(engine, "name", "unknown")
            logger.warning("Extraction engine failed file={} engine={} error={}", path.name, engine_name, exc)
            warnings = [f"engine_failed={engine_name}"]
            document = build_document_from_sections(path, {}, "", engine_name)
            quality = score_extraction(document, engine_name, warnings)
            document.confidence = quality.confidence
            if document.metadata:
                document.metadata.confidence = quality.confidence
            return EngineResult(document=document, engine_name=engine_name, quality=quality, warnings=warnings)

    @staticmethod
    def _should_try_ocr(*results: EngineResult) -> bool:
        best = max(results, key=lambda result: result.quality.score)
        return best.quality.required_statements_found == 0 or best.quality.total_rows == 0

    @staticmethod
    def _finalize(result: EngineResult) -> ExtractedDocument:
        document = result.document
        document.extraction_method = result.engine_name
        document.confidence = result.quality.confidence
        if document.metadata:
            document.metadata.extraction_method = result.engine_name
            document.metadata.confidence = result.quality.confidence
        return document

    def _write_debug(self, path: Path, results: list[EngineResult], winner: EngineResult) -> None:
        debug_dir = Path("logs") / "debug" / "extraction" / path.stem
        debug_dir.mkdir(parents=True, exist_ok=True)
        scores = [result.quality.to_dict() for result in results]
        (debug_dir / "engine_scores.json").write_text(json.dumps(scores, indent=2, ensure_ascii=False), encoding="utf-8")
        (debug_dir / "winning_engine.txt").write_text(winner.engine_name, encoding="utf-8")
        winner.quality.write_json(debug_dir / "extraction_quality.json")
        for result in results:
            (debug_dir / f"{result.engine_name}_debug.json").write_text(
                json.dumps(result.debug, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
