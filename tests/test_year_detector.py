from sicav_checker.normalization.year_detector import detect_document_year, detect_year_from_text


def test_year_from_filename() -> None:
    assert detect_document_year("2025_maxula_placement_sicav_efd311225.pdf") == 2025


def test_year_from_bilan_title() -> None:
    assert detect_year_from_text("BILAN ARRETE AU 31 DECEMBRE 2024") == 2024
