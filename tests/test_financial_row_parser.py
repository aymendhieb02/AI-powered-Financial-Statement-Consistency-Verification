from __future__ import annotations

import pytest

from sicav_checker.extraction.statement_extractor import extract_rows, parse_financial_row


@pytest.mark.parametrize(
    ("line", "label", "current", "previous"),
    [
        ("CrÃ©ances d'exploitation 6 336 22 132", "CrÃ©ances d'exploitation", 336, 22132),
        ("OpÃ©rateurs crÃ©diteurs 7 32 605 31 144", "OpÃ©rateurs crÃ©diteurs", 32605, 31144),
        ("Autres crÃ©diteurs divers 8 40 409 1 708", "Autres crÃ©diteurs divers", 40409, 1708),
        ("TOTAL PASSIF 73 014 32 852", "TOTAL PASSIF", 73014, 32852),
        ("Revenus des placements monÃ©taires 11 38 475 38 521", "Revenus des placements monÃ©taires", 38475, 38521),
        ("TOTAL DES REVENUS DES PLACEMENTS 1 004 266 1 013 745", "TOTAL DES REVENUS DES PLACEMENTS", 1004266, 1013745),
        ("Charges de gestion des placements 13 (132 361) (133 323)", "Charges de gestion des placements", -132361, -133323),
        ("Variation des plus (ou moins) values potentielles sur titres (26 901) (14 337)", "Variation des plus (ou moins) values potentielles sur titres", -26901, -14337),
        ("Plus (ou moins) values rÃ©alisÃ©es sur cession de titres 55 850 31 650", "Plus (ou moins) values rÃ©alisÃ©es sur cession de titres", 55850, 31650),
        ("VALEUR LIQUIDATIVE 108.164 107.635", "VALEUR LIQUIDATIVE", 108.164, 107.635),
        ("TAUX DE RENDEMENT 5.96% 5.70%", "TAUX DE RENDEMENT", 5.96, 5.70),
        ("DisponibilitÃ©s - 10", "DisponibilitÃ©s", None, 10),
        ("DisponibilitÃ©s - -", "DisponibilitÃ©s", None, None),
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
        "OpÃ©rateurs crÃ©diteurs 7 32 605 31 144": 32605,
        "TOTAL PASSIF 73 014 32 852": 73014,
        "Revenus des placements monÃ©taires 11 38 475 38 521": 38475,
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
        antÃ©rieurs 110 43
        """,
        "bilan",
    )

    assert rows[0].label == "Tires des Organismes de Placement Collectif"
    assert rows[0].current_value == 711001
    assert rows[0].previous_value == 708899
    assert rows[1].label == "Sommes distribuables des exercices antÃ©rieurs"
    assert rows[1].current_value == 110
    assert rows[1].previous_value == 43


def test_extract_rows_strips_category_prefix_without_losing_actif_net_account() -> None:
    rows = extract_rows(
        """
        PASSIF OpÃ©rateurs crÃ©diteurs 7 32 605 31 144
        ACTIF NET Capital 12 000 11 000
        ACTIF NET 14 266 685 12 170 616
        """,
        "bilan",
    )

    assert rows[0].label == "OpÃ©rateurs crÃ©diteurs"
    assert rows[1].label == "Capital"
    assert rows[2].label == "ACTIF NET"


def test_extract_rows_skips_section_headers_and_column_headers() -> None:
    rows = extract_rows(
        """
        (Montants exprimÃ©s en dinars tunisiens)
        ACTIF
        PASSIF
        Note AnnÃ©e 2025 AnnÃ©e 2024
        TOTAL ACTIF 14 339 699 12 170 616
        """,
        "bilan",
    )

    assert [row.label for row in rows] == ["TOTAL ACTIF"]


@pytest.mark.parametrize(
    ("line", "current", "previous", "bad_values"),
    [
        ("Portefeuille-titres 4 7 826 775 7 701 801", 7826775, 7701801, {117876}),
        ("Obligations et valeurs assimilÃƒÂ©es 7 117 876 7 665 954", 7117876, 7665954, {117876}),
        ("Placements monÃƒÂ©taires et disponibilitÃƒÂ©s 6 512 588 4 479 535", 6512588, 4479535, {512588}),
        ("CrÃƒÂ©ances d'exploitation 6 2 684 336", 2684, 336, {684336}),
        ("Revenus des titres des Organismes de Placement Collectif 6 663 -", 6663, None, set()),
        ("TRANSACTIONS SUR LE CAPITAL 1 907 089 1 635 943", 1907089, 1635943, {907089}),
        ("En dÃƒÂ©but de l'exercice 12 170 616 10 691 259", 12170616, 10691259, {170616}),
        ("En fin de l'exercice 14 266 685 12 170 616", 14266685, 12170616, set()),
        ("RÃƒÂ©gularisation des sommes distribuables 2 295 466 3 717 328", 2295466, 3717328, set()),
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
        ETAT DE VARIATION DE L'ACTIF NET AnnÃƒÂ©e 2024 AnnÃƒÂ©e 2023 VARIATION DE L'ACTIF NET RESULTANT 882 945 880 145
        DES OPERATIONS D'EXPLOITATION RÃƒÂ©sultat d'exploitation 196 809 178 906
        """,
        "etat_variation_actif_net",
    )

    assert rows[0].label == "Portefeuille-titres"
    assert rows[0].current_value == 7826775
    assert rows[1].label == "VARIATION DE L'ACTIF NET RESULTANT"
    assert rows[1].current_value == 882945
    assert rows[2].label == "RÃƒÂ©sultat d'exploitation"
    assert rows[2].current_value == 196809
    assert all(row.confidence < 0.85 for row in rows)


def test_variation_statement_duplicate_labels_include_parent_context() -> None:
    rows = extract_rows(
        """
        Souscriptions
        Capital 1 000 900
        RÃƒÂ©gularisation des sommes non distribuables 200 100
        Rachats
        Capital 800 700
        RÃƒÂ©gularisation des sommes distribuables 2 295 466 3 717 328
        """,
        "etat_variation_actif_net",
    )

    assert rows[0].canonical_label == "variation_actif_net__souscriptions_capital"
    assert rows[1].canonical_label == "variation_actif_net__souscriptions_regularisation_sommes_non_distribuables"
    assert rows[2].canonical_label == "variation_actif_net__rachats_capital"
    assert rows[3].canonical_label == "variation_actif_net__rachats_regularisation_sommes_distribuables"


@pytest.mark.parametrize("year", range(2020, 2026))
def test_extract_rows_strips_year_specific_balance_headers_from_portefeuille_titres(year: int) -> None:
    previous_year = year - 1
    rows = extract_rows(
        f"BILAN ARRETE AU 31 DECEMBRE {year} ACTIF Note 31/12/{year} 31/12/{previous_year} "
        "Portefeuille-titres 4 7 826 775 7 701 801",
        "bilan",
    )

    assert len(rows) == 1
    assert rows[0].label == "Portefeuille-titres"
    assert rows[0].canonical_label == "portefeuille_titres"
    assert rows[0].current_value == 7826775


def test_extract_rows_discards_page_and_year_headers() -> None:
    rows = extract_rows(
        """
        BILAN ARRETE AU 31 DECEMBRE 2025
        ACTIF
        Note AnnÃ©e 2025 AnnÃ©e 2024
        AnnÃ©e 2025 AnnÃ©e 2024 Revenus des obligations 100 90
        """,
        "etat_resultat",
    )

    assert [row.label for row in rows] == ["Revenus des obligations"]
    assert rows[0].canonical_label == "revenus_obligations"


def test_extract_rows_does_not_collapse_result_regularisation_and_annulation() -> None:
    rows = extract_rows(
        """
        DES OPERATIONS D'EXPLOITATION RÃ©sultat d'exploitation 196 809 178 906
        RÃ©gularisation du rÃ©sultat d'exploitation 10 000 9 000
        Annulation du rÃ©sultat d'exploitation 5 000 4 000
        RÃ©sultat d'exploitation (annulation) 3 000 2 000
        """,
        "etat_resultat",
    )

    assert [row.label for row in rows] == [
        "RÃ©sultat d'exploitation",
        "RÃ©gularisation du rÃ©sultat d'exploitation",
        "Annulation du rÃ©sultat d'exploitation",
        "RÃ©sultat d'exploitation (annulation)",
    ]
    assert {row.canonical_label for row in rows} == {
        "resultat_exploitation",
        "regularisation_resultat_exploitation",
        "annulation_resultat_exploitation",
        "resultat_exploitation_annulation",
    }



def test_variation_statement_repeated_period_rows_are_contextualized() -> None:
    rows = extract_rows(
        """
        En dÃ©but de l'exercice 12 170 616 10 691 259
        En fin de l'exercice 14 266 685 12 170 616
        En dÃ©but de l'exercice 113 073 101 165
        En fin de l'exercice 131 899 113 073
        """,
        "etat_variation_actif_net",
    )

    assert [row.canonical_label for row in rows] == [
        "variation_actif_net__actif_net_en_debut_exercice",
        "variation_actif_net__actif_net_en_fin_exercice",
        "variation_actif_net__nombre_actions_en_debut_exercice",
        "variation_actif_net__nombre_actions_en_fin_exercice",
    ]


def test_variation_statement_embedded_title_wins_over_pending_label() -> None:
    rows = extract_rows(
        """
        Droits de sortie
        VARIATION DE L'ACTIF NET 2 096 069 1 479 357
        """,
        "etat_variation_actif_net",
    )

    assert rows[0].label == "VARIATION DE L'ACTIF NET"
    assert rows[0].canonical_label == "variation_actif_net"


def test_separator_rows_stop_multiline_merge_before_next_financial_row() -> None:
    rows = extract_rows(
        """
        Droits de sortie
        PASSIF
        VARIATION DE L'ACTIF NET 2 096 069 1 479 357
        """,
        "etat_variation_actif_net",
    )

    assert rows == [rows[0]]
    assert rows[0].label == "VARIATION DE L'ACTIF NET"


def test_pdfplumber_visual_line_evidence_preserves_page_and_bboxes() -> None:
    from sicav_checker.extraction.layout_section_extractor import VisualLine, VisualWord

    line = VisualLine(
        page=7,
        top=100.0,
        bottom=110.0,
        x0=20.0,
        x1=250.0,
        text="TOTAL DES REVENUS DES PLACEMENTS 1 013 745 474 019",
        words=(
            VisualWord("TOTAL", 20.0, 100.0, 50.0, 110.0),
            VisualWord("DES", 55.0, 100.0, 75.0, 110.0),
            VisualWord("REVENUS", 80.0, 100.0, 130.0, 110.0),
            VisualWord("DES", 135.0, 100.0, 155.0, 110.0),
            VisualWord("PLACEMENTS", 160.0, 100.0, 230.0, 110.0),
            VisualWord("1", 300.0, 100.0, 306.0, 110.0),
            VisualWord("013", 309.0, 100.0, 327.0, 110.0),
            VisualWord("745", 330.0, 100.0, 348.0, 110.0),
            VisualWord("474", 360.0, 100.0, 378.0, 110.0),
            VisualWord("019", 381.0, 100.0, 399.0, 110.0),
        ),
    )

    row = extract_rows("", "etat_resultat", visual_lines=[line], document_id="2024.pdf", source_file="2024.pdf", extraction_method="pdfplumber_layout")[0]

    assert row.page == 7
    assert row.current_value == 1013745
    assert row.previous_value == 474019
    assert row.evidence is not None
    assert row.evidence.page_number == 7
    assert row.evidence.section_name == "etat_resultat"
    assert row.evidence.bbox_row is not None
    assert row.evidence.bbox_current is not None
    assert row.evidence.bbox_previous is not None
    assert row.evidence.value_text_current == "1 013 745"
    assert row.evidence.value_text_previous == "474 019"


def test_page_headers_do_not_create_fake_accounts() -> None:
    rows = extract_rows(
        """
        Page 12
        31/12/2025 31/12/2024
        PASSIF
        Portefeuille-titres 7 826 775 7 701 801
        """,
        "bilan",
    )

    assert len(rows) == 1
    assert rows[0].label == "Portefeuille-titres"
