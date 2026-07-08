from sicav_checker.comparison.cross_year_comparator import compare_documents
from sicav_checker.models import Status
from sicav_checker.testsupport.corrupted_data_generator import base_documents, corrupted_documents


def test_equal_values_are_carry_forward_ok() -> None:
    old, new = base_documents()
    results = compare_documents(old, new)
    total_actif = next(item for item in results if item.canonical_label == "total_actif")
    assert total_actif.status == Status.CARRY_FORWARD_OK


def test_changed_amount_is_carry_forward_mismatch() -> None:
    old, new = corrupted_documents("changed_amount")
    results = compare_documents(old, new)
    total_actif = next(item for item in results if item.canonical_label == "total_actif")
    assert total_actif.status == Status.CARRY_FORWARD_MISMATCH


def test_missing_row_is_missing_in_new_comparative() -> None:
    old, new = corrupted_documents("missing_row")
    results = compare_documents(old, new)
    total_actif = next(item for item in results if item.canonical_label == "total_actif")
    assert total_actif.status == Status.MISSING_IN_NEW_COMPARATIVE


def test_renamed_label_is_detected() -> None:
    old, new = corrupted_documents("renamed_label")
    results = compare_documents(old, new)
    total_actif = next(item for item in results if item.canonical_label == "total_actif")
    assert total_actif.status in {Status.LABEL_RENAMED, Status.CARRY_FORWARD_OK}


def test_carry_forward_uses_old_current_and_new_previous_only() -> None:
    from sicav_checker.domain.models import DocumentMetadata, FinancialDocument, FinancialStatement, StatementRow

    old = FinancialDocument(
        metadata=DocumentMetadata(year=2023, source_file="2023.pdf"),
        statements={"etat_resultat": FinancialStatement(name="etat_resultat", rows=[StatementRow(label="TOTAL DES REVENUS DES PLACEMENTS", canonical_label="total_revenus_placements", current_value=1013745, previous_value=474019)])},
    )
    new = FinancialDocument(
        metadata=DocumentMetadata(year=2024, source_file="2024.pdf"),
        statements={"etat_resultat": FinancialStatement(name="etat_resultat", rows=[StatementRow(label="TOTAL DES REVENUS DES PLACEMENTS", canonical_label="total_revenus_placements", current_value=1004266, previous_value=1013745)])},
    )

    results = compare_documents(old, new)
    item = next(result for result in results if result.canonical_label == "total_revenus_placements")

    assert item.old_value == 1013745
    assert item.new_value == 1013745
    assert item.status == Status.CARRY_FORWARD_OK
