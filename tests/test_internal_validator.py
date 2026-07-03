from sicav_checker.models import Severity, Status
from sicav_checker.testsupport.corrupted_data_generator import base_documents, corrupted_documents
from sicav_checker.validation.internal_validator import validate_document


def test_valid_document_passes_internal_validation() -> None:
    old, _ = base_documents()
    results = validate_document(old)
    assert results
    assert all(item.status == Status.OK for item in results)


def test_wrong_total_is_critical() -> None:
    old, _ = corrupted_documents("wrong_total")
    results = validate_document(old)
    assert any(item.status == Status.MISMATCH and item.severity == Severity.CRITICAL for item in results)
