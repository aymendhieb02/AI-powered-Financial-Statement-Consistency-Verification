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
