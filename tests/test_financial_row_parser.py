from __future__ import annotations

import pytest

from sicav_checker.extraction.statement_extractor import extract_rows, parse_financial_row


@pytest.mark.parametrize(
    ("line", "label", "current", "previous"),
    [
        ("Créances d'exploitation 6 336 22 132", "Créances d'exploitation", 336, 22132),
        ("Opérateurs créditeurs 7 32 605 31 144", "Opérateurs créditeurs", 32605, 31144),
        ("Autres créditeurs divers 8 40 409 1 708", "Autres créditeurs divers", 40409, 1708),
        ("TOTAL PASSIF 73 014 32 852", "TOTAL PASSIF", 73014, 32852),
        ("Revenus des placements monétaires 11 38 475 38 521", "Revenus des placements monétaires", 38475, 38521),
        ("TOTAL DES REVENUS DES PLACEMENTS 1 004 266 1 013 745", "TOTAL DES REVENUS DES PLACEMENTS", 1004266, 1013745),
        ("Charges de gestion des placements 13 (132 361) (133 323)", "Charges de gestion des placements", -132361, -133323),
        ("Variation des plus (ou moins) values potentielles sur titres (26 901) (14 337)", "Variation des plus (ou moins) values potentielles sur titres", -26901, -14337),
        ("Plus (ou moins) values réalisées sur cession de titres 55 850 31 650", "Plus (ou moins) values réalisées sur cession de titres", 55850, 31650),
        ("VALEUR LIQUIDATIVE 108.164 107.635", "VALEUR LIQUIDATIVE", 108.164, 107.635),
        ("TAUX DE RENDEMENT 5.96% 5.70%", "TAUX DE RENDEMENT", 5.96, 5.70),
        ("Disponibilités - 10", "Disponibilités", None, 10),
        ("Disponibilités - -", "Disponibilités", None, None),
    ],
)
def test_financial_row_parser_examples(line: str, label: str, current: float | int | None, previous: float | int | None) -> None:
    parsed = parse_financial_row(line)
    assert parsed is not None
    assert parsed[0] == label

    rows = extract_rows(line, "bilan")
    assert len(rows) == 1
    assert rows[0].label == label
    assert rows[0].current_value == current
    assert rows[0].previous_value == previous


def test_parser_does_not_merge_adjacent_financial_columns() -> None:
    cases = {
        "Opérateurs créditeurs 7 32 605 31 144": 32605,
        "TOTAL PASSIF 73 014 32 852": 73014,
        "Revenus des placements monétaires 11 38 475 38 521": 38475,
    }

    for line, expected_current in cases.items():
        row = extract_rows(line, "bilan")[0]
        assert row.current_value == expected_current
        assert row.current_value not in {3260531, 7301432, 3847538}


def test_extract_rows_joins_multiline_labels() -> None:
    rows = extract_rows(
        """
        Tires des Organismes de Placement
        Collectif 711 001 708 899
        Sommes distribuables des exercices
        antérieurs 110 43
        """,
        "bilan",
    )

    assert rows[0].label == "Tires des Organismes de Placement Collectif"
    assert rows[0].current_value == 711001
    assert rows[0].previous_value == 708899
    assert rows[1].label == "Sommes distribuables des exercices antérieurs"
    assert rows[1].current_value == 110
    assert rows[1].previous_value == 43


def test_extract_rows_strips_category_prefix_without_losing_actif_net_account() -> None:
    rows = extract_rows(
        """
        PASSIF Opérateurs créditeurs 7 32 605 31 144
        ACTIF NET Capital 12 000 11 000
        ACTIF NET 14 266 685 12 170 616
        """,
        "bilan",
    )

    assert rows[0].label == "Opérateurs créditeurs"
    assert rows[1].label == "Capital"
    assert rows[2].label == "ACTIF NET"


def test_extract_rows_skips_section_headers_and_column_headers() -> None:
    rows = extract_rows(
        """
        (Montants exprimés en dinars tunisiens)
        ACTIF
        PASSIF
        Note Année 2025 Année 2024
        TOTAL ACTIF 14 339 699 12 170 616
        """,
        "bilan",
    )

    assert [row.label for row in rows] == ["TOTAL ACTIF"]

@pytest.mark.parametrize(
    ("line", "current", "previous", "bad_values"),
    [
        ("Portefeuille-titres 4 7 826 775 7 701 801", 7826775, 7701801, {117876}),
        ("Obligations et valeurs assimilÃ©es 7 117 876 7 665 954", 7117876, 7665954, {117876}),
        ("Placements monÃ©taires et disponibilitÃ©s 6 512 588 4 479 535", 6512588, 4479535, {512588}),
        ("CrÃ©ances d'exploitation 6 2 684 336", 2684, 336, {684336}),
        ("Revenus des titres des Organismes de Placement Collectif 6 663 -", 6663, None, set()),
        ("TRANSACTIONS SUR LE CAPITAL 1 907 089 1 635 943", 1907089, 1635943, {907089}),
        ("En dÃ©but de l'exercice 12 170 616 10 691 259", 12170616, 10691259, {170616}),
        ("En fin de l'exercice 14 266 685 12 170 616", 14266685, 12170616, set()),
        ("RÃ©gularisation des sommes distribuables 2 295 466 3 717 328", 2295466, 3717328, set()),
    ],
)
def test_parser_preserves_large_leading_amount_groups(line: str, current: int, previous: int | None, bad_values: set[int]) -> None:
    row = extract_rows(line, "etat_variation_actif_net")[0]
    assert row.current_value == current
    assert row.previous_value == previous
    assert row.current_value not in bad_values
    assert row.previous_value not in bad_values


def test_extract_rows_strips_glued_report_headers() -> None:
    rows = extract_rows(
        """
        BILAN ARRETE AU 31 DECEMBRE 2024 ACTIF Note 31/12/2024 31/12/2023 Portefeuille-titres 4 7 826 775 7 701 801
        ETAT DE VARIATION DE L'ACTIF NET AnnÃ©e 2024 AnnÃ©e 2023 VARIATION DE L'ACTIF NET RESULTANT 882 945 880 145
        DES OPERATIONS D'EXPLOITATION RÃ©sultat d'exploitation 196 809 178 906
        """,
        "etat_variation_actif_net",
    )

    assert rows[0].label == "Portefeuille-titres"
    assert rows[0].current_value == 7826775
    assert rows[1].label == "VARIATION DE L'ACTIF NET RESULTANT"
    assert rows[1].current_value == 882945
    assert rows[2].label == "RÃ©sultat d'exploitation"
    assert rows[2].current_value == 196809
    assert all(row.confidence < 0.85 for row in rows)


def test_variation_statement_duplicate_labels_include_parent_context() -> None:
    rows = extract_rows(
        """
        Souscriptions
        Capital 1 000 900
        RÃ©gularisation des sommes non distribuables 200 100
        Rachats
        Capital 800 700
        RÃ©gularisation des sommes distribuables 2 295 466 3 717 328
        """,
        "etat_variation_actif_net",
    )

    assert rows[0].canonical_label == "variation_actif_net__souscriptions_capital"
    assert rows[1].canonical_label == "variation_actif_net__souscriptions_regularisation_sommes_non_distribuables"
    assert rows[2].canonical_label == "variation_actif_net__rachats_capital"
    assert rows[3].canonical_label == "variation_actif_net__rachats_regularisation_sommes_distribuables"