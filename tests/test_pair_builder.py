from sicav_checker.comparison.pair_builder import build_valid_pairs


def test_pair_builder_skips_missing_years() -> None:
    assert build_valid_pairs([2012, 2013, 2015, 2016]) == [(2012, 2013), (2015, 2016)]
