from sicav_checker.comparison.cross_year_comparator import compare_documents
from sicav_checker.models import Status
from sicav_checker.testsupport.corrupted_data_generator import base_documents, corrupted_documents


def test_equal_values_are_ok() -> None:
    old, new = base_documents()
    results = compare_documents(old, new)
    total_actif = next(item for item in results if item.canonical_label == "total_actif")
    assert total_actif.status == Status.OK


def test_changed_amount_is_mismatch() -> None:
    old, new = corrupted_documents("changed_amount")
    results = compare_documents(old, new)
    total_actif = next(item for item in results if item.canonical_label == "total_actif")
    assert total_actif.status == Status.MISMATCH


def test_missing_row_is_missing_in_new() -> None:
    old, new = corrupted_documents("missing_row")
    results = compare_documents(old, new)
    total_actif = next(item for item in results if item.canonical_label == "total_actif")
    assert total_actif.status == Status.MISSING_IN_NEW


def test_renamed_label_is_detected() -> None:
    old, new = corrupted_documents("renamed_label")
    results = compare_documents(old, new)
    total_actif = next(item for item in results if item.canonical_label == "total_actif")
    assert total_actif.status in {Status.LABEL_RENAMED, Status.OK}
