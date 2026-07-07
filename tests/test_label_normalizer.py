from sicav_checker.normalization.label_normalizer import normalize_label


def test_label_examples() -> None:
    assert normalize_label("TOTAL ACTIF") == "total_actif"
    assert normalize_label("ACTIF NET") == "actif_net"
    assert normalize_label("RESULTAT D'EXPLOITATION") == "resultat_exploitation"
    assert normalize_label("SOMMES DISTRIBUABLES DE L'EXERCICE") == "sommes_distribuables_exercice"



def test_report_titles_and_years_do_not_pollute_account_label() -> None:
    labels = [
        f"BILAN ARRETE AU 31 DECEMBRE {year} Portefeuille-titres"
        for year in range(2020, 2026)
    ]

    assert {normalize_label(label) for label in labels} == {"portefeuille_titres"}


def test_table_headers_and_page_headers_are_removed_before_normalization() -> None:
    assert normalize_label("ACTIF Note 31/12/2025 31/12/2024 Portefeuille-titres") == "portefeuille_titres"
    assert normalize_label("Année 2025 Année 2024 Revenus des obligations") == "revenus_obligations"
    assert normalize_label("Note Année 2025 Année 2024 Charges de gestion") == "charges_gestion"


def test_distinct_result_concepts_remain_distinct() -> None:
    labels = {
        normalize_label("Résultat d'exploitation"),
        normalize_label("Régularisation du résultat d'exploitation"),
        normalize_label("Annulation du résultat d'exploitation"),
        normalize_label("Résultat d'exploitation (annulation)"),
    }

    assert labels == {
        "resultat_exploitation",
        "regularisation_resultat_exploitation",
        "annulation_resultat_exploitation",
        "resultat_exploitation_annulation",
    }
