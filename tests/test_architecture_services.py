from pathlib import Path

from sicav_checker.domain.models import ComparisonReport, DocumentMetadata, FinancialDocument, FinancialStatement, StatementRow
from sicav_checker.pipeline.orchestrator import PipelineOrchestrator
from sicav_checker.services.comparison_service import ComparisonService
from sicav_checker.services.normalization_service import NormalizationService
from sicav_checker.services.validation_service import ValidationService
from sicav_checker.testsupport.corrupted_data_generator import base_documents


class MemoryStorage:
    def __init__(self, documents: list[FinancialDocument]) -> None:
        self.documents = documents
        self.saved: list[FinancialDocument] = []

    def save_documents(self, documents: list[FinancialDocument]) -> list[Path | None]:
        self.saved.extend(documents)
        return []

    def load_documents(self) -> list[FinancialDocument]:
        return self.documents


class NoopReporting:
    def __init__(self) -> None:
        self.received: ComparisonReport | None = None

    def generate(self, report: ComparisonReport, reports_dir: Path) -> list[Path]:
        self.received = report
        return [reports_dir / "report.json"]


def test_financial_document_is_the_canonical_contract() -> None:
    document = FinancialDocument(
        metadata=DocumentMetadata(year=2024, source_file="2024.pdf"),
        statements={
            "bilan": FinancialStatement(
                name="bilan",
                rows=[StatementRow(label="TOTAL ACTIF", canonical_label="total_actif", current_value=100, previous_value=90)],
            )
        },
    )

    assert document.document_year == 2024
    assert document.balance_sheet is not None
    assert document.statements["bilan"].rows[0].canonical_label == "total_actif"


def test_services_consume_financial_documents() -> None:
    old, new = base_documents()
    normalized = NormalizationService().normalize_documents([old, new])
    validations = ValidationService().validate_documents(normalized)
    comparisons = ComparisonService().compare_documents(normalized)

    assert all(isinstance(document, FinancialDocument) for document in normalized)
    assert validations
    assert comparisons


def test_orchestrator_coordinates_services_without_cli_logic(tmp_path: Path) -> None:
    old, new = base_documents()
    storage = MemoryStorage([old, new])
    reporting = NoopReporting()
    orchestrator = PipelineOrchestrator(storage_service=storage, reporting_service=reporting)

    result = orchestrator.report(reports_dir=tmp_path)

    assert result.report_paths == [tmp_path / "report.json"]
    assert reporting.received is not None
    assert reporting.received.documents == [old, new]
    assert result.comparisons
    assert result.validations