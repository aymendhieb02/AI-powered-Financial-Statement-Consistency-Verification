from sicav_checker.normalization.number_normalizer import normalize_number


def test_parentheses_are_negative() -> None:
    assert normalize_number("(132 361)") == -132361


def test_space_grouped_integer() -> None:
    assert normalize_number("14 339 699") == 14339699


def test_decimal_comma_and_dot() -> None:
    assert normalize_number("104,867") == 104.867
    assert normalize_number("108.164") == 108.164


def test_dash_is_none() -> None:
    assert normalize_number("-") is None
