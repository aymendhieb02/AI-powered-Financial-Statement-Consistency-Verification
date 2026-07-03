from sicav_checker.comparison.cross_year_comparator import compare_documents
from sicav_checker.models import Status
from sicav_checker.testsupport.corrupted_data_generator import corrupted_documents
from sicav_checker.validation.internal_validator import validate_document


def test_wrong_sign_detected() -> None:
    old, new = corrupted_documents("wrong_sign")
    results = compare_documents(old, new)
    assert any(item.canonical_label == "actif_net" and item.status == Status.MISMATCH for item in results)


def test_swapped_columns_detected() -> None:
    old, new = corrupted_documents("swapped_columns")
    results = compare_documents(old, new)
    assert any(item.status == Status.MISMATCH for item in results)


def test_decimal_issue_detected() -> None:
    old, new = corrupted_documents("decimal_issue")
    results = compare_documents(old, new)
    assert any(item.canonical_label == "total_actif" and item.status == Status.MISMATCH for item in results)


def test_wrong_total_detected_by_internal_validation() -> None:
    old, _ = corrupted_documents("wrong_total")
    assert any(item.status == Status.MISMATCH for item in validate_document(old))
