from __future__ import annotations

from sicav_checker.comparison.pair_builder import build_row_pairs, build_valid_pairs
from sicav_checker.models import StatementRow


def row(label: str, key: str) -> StatementRow:
    return StatementRow(label=label, canonical_label=key, current_value=1, previous_value=1)


def test_build_row_pairs_quarantines_duplicate_canonical_labels() -> None:
    old_rows = [
        row("Résultat d'exploitation", "etat_resultat__resultat_exploitation"),
        row("Régularisation du résultat d'exploitation", "etat_resultat__resultat_exploitation"),
    ]
    new_rows = [row("Résultat d'exploitation", "etat_resultat__resultat_exploitation")]

    matched, unmatched_old, unmatched_new = build_row_pairs(old_rows, new_rows)

    assert matched == []
    assert unmatched_old == old_rows
    assert unmatched_new == new_rows



def test_pair_builder_skips_missing_years() -> None:
    assert build_valid_pairs([2012, 2013, 2015, 2016]) == [(2012, 2013), (2015, 2016)]
