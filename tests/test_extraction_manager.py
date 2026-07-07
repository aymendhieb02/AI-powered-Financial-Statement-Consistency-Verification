from __future__ import annotations

from pathlib import Path

from sicav_checker.extraction.engines.base import EngineResult
from sicav_checker.extraction.extraction_manager import ExtractionManager
from sicav_checker.extraction.quality import score_extraction
from sicav_checker.models import ExtractedDocument, Statement, StatementRow


class FakeEngine:
    def __init__(self, name: str, document: ExtractedDocument, fail: bool = False) -> None:
        self.name = name
        self.document = document
        self.fail = fail
        self.calls = 0

    def extract(self, path: Path) -> EngineResult:
        self.calls += 1
        if self.fail:
            raise RuntimeError("boom")
        quality = score_extraction(self.document, self.name)
        self.document.confidence = quality.confidence
        if self.document.metadata:
            self.document.metadata.confidence = quality.confidence
        return EngineResult(document=self.document, engine_name=self.name, quality=quality)


def make_document(row_count: int, statements: tuple[str, ...] = ("bilan",)) -> ExtractedDocument:
    rows = [
        StatementRow(label=f"Line {index}", canonical_label=f"line_{index}", current_value=index, previous_value=index)
        for index in range(row_count)
    ]
    statement_map = {name: Statement(name=name, rows=list(rows)) for name in statements}
    return ExtractedDocument(document_year=2024, source_file="synthetic.pdf", extraction_method="fake", statements=statement_map)


def strong_document() -> ExtractedDocument:
    rows = [
        StatementRow(label="TOTAL ACTIF", canonical_label="total_actif", current_value=1000, previous_value=900),
        StatementRow(label="TOTAL PASSIF", canonical_label="total_passif", current_value=200, previous_value=180),
        StatementRow(label="ACTIF NET", canonical_label="actif_net", current_value=800, previous_value=720),
        StatementRow(label="TOTAL PASSIF ET ACTIF NET", canonical_label="total_passif_et_actif_net", current_value=1000, previous_value=900),
        *[
            StatementRow(label=f"Line {index}", canonical_label=f"line_{index}", current_value=index, previous_value=index)
            for index in range(50)
        ],
    ]
    return ExtractedDocument(
        document_year=2024,
        source_file="synthetic.pdf",
        extraction_method="fake",
        statements={
            "bilan": Statement(name="bilan", rows=list(rows)),
            "etat_resultat": Statement(name="etat_resultat", rows=list(rows)),
            "etat_variation_actif_net": Statement(name="etat_variation_actif_net", rows=list(rows)),
        },
    )


def test_extraction_manager_selects_better_layout_fallback(tmp_path: Path) -> None:
    weak_text = FakeEngine("pymupdf_text", make_document(2, ("bilan",)))
    strong_layout = FakeEngine("pdfplumber_layout", strong_document())
    manager = ExtractionManager(
        text_engine=weak_text,
        layout_engine=strong_layout,
        camelot_engine=FakeEngine("camelot", make_document(0, ())),
        ocr_engine=FakeEngine("ocr", make_document(0, ())),
    )

    result = manager.extract(tmp_path / "report_2024.pdf")

    assert result.extraction_method == "pdfplumber_layout"
    assert strong_layout.calls == 1
    assert result.confidence > weak_text.document.confidence


def test_optional_camelot_and_ocr_failures_do_not_crash(tmp_path: Path) -> None:
    manager = ExtractionManager(
        text_engine=FakeEngine("pymupdf_text", make_document(0, ())),
        layout_engine=FakeEngine("pdfplumber_layout", make_document(0, ())),
        camelot_engine=FakeEngine("camelot", make_document(0, ()), fail=True),
        ocr_engine=FakeEngine("ocr", make_document(0, ()), fail=True),
    )

    result = manager.extract(tmp_path / "scanned_2024.pdf")

    assert isinstance(result, ExtractedDocument)
    assert result.confidence < 0.5


def test_manager_sets_confidence_from_quality_score(tmp_path: Path) -> None:
    manager = ExtractionManager(
        text_engine=FakeEngine("pymupdf_text", strong_document()),
        layout_engine=FakeEngine("pdfplumber_layout", make_document(0, ())),
        camelot_engine=FakeEngine("camelot", make_document(0, ())),
        ocr_engine=FakeEngine("ocr", make_document(0, ())),
    )

    result = manager.extract(tmp_path / "good_2024.pdf")

    assert result.confidence != 0.9
    assert result.confidence > 0.72
