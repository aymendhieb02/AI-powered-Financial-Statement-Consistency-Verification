from sicav_checker.normalization.label_normalizer import normalize_label


def test_label_examples() -> None:
    assert normalize_label("TOTAL ACTIF") == "total_actif"
    assert normalize_label("ACTIF NET") == "actif_net"
    assert normalize_label("RESULTAT D'EXPLOITATION") == "resultat_exploitation"
    assert normalize_label("SOMMES DISTRIBUABLES DE L'EXERCICE") == "sommes_distribuables_exercice"
