import pandas as pd
import pytest

from api.preparation import preparer_donnees


@pytest.fixture
def employe_brut():
    """Un employé brut, tel qu'il arrive à l'API (avant transformation)."""
    return pd.DataFrame([{
        "augementation_salaire_precedente": "15 %",
        "heure_supplementaires": "Oui",
        "frequence_deplacement": "Occasionnel",
        "annees_depuis_la_derniere_promotion": 3,
        "annees_dans_l_entreprise": 5,
        "revenu_mensuel": 6000,
        "niveau_hierarchique_poste": 2,
        "annee_experience_totale": 9,
        "satisfaction_employee_equilibre_pro_perso": 1,
    }])


def test_augmentation_retire_le_pourcentage(employe_brut):
    resultat = preparer_donnees(employe_brut)
    assert resultat["augementation_salaire_precedente"][0] == 15


def test_augmentation_accepte_un_nombre(employe_brut):
    employe_brut["augementation_salaire_precedente"] = 15
    resultat = preparer_donnees(employe_brut)
    assert resultat["augementation_salaire_precedente"][0] == 15


@pytest.mark.parametrize("valeur, attendu", [("Oui", 1), ("Non", 0)])
def test_heures_supplementaires_en_binaire(employe_brut, valeur, attendu):
    employe_brut["heure_supplementaires"] = valeur
    assert preparer_donnees(employe_brut)["heure_supplementaires"][0] == attendu


@pytest.mark.parametrize("valeur, attendu", [("Aucun", 0), ("Occasionnel", 1), ("Frequent", 2)])
def test_frequence_deplacement_encodee(employe_brut, valeur, attendu):
    employe_brut["frequence_deplacement"] = valeur
    assert preparer_donnees(employe_brut)["frequence_deplacement"][0] == attendu


def test_variables_creees(employe_brut):
    r = preparer_donnees(employe_brut)
    assert r["evolution_promotion"][0] == pytest.approx(3 / (5 + 1))
    assert r["revenus_vs_niveau"][0] == pytest.approx(6000 / 2)
    assert r["xp_entreprise_vs_totale"][0] == pytest.approx(5 / (9 + 1))
    assert r["experience_externe"][0] == 9 - 5
    assert r["surcharge_ressentie"][0] == 1 * (5 - 1)


def test_sans_heures_sup_pas_de_surcharge(employe_brut):
    employe_brut["heure_supplementaires"] = "Non"
    assert preparer_donnees(employe_brut)["surcharge_ressentie"][0] == 0


def test_ne_modifie_pas_les_donnees_d_origine(employe_brut):
    copie = employe_brut.copy()
    preparer_donnees(employe_brut)
    pd.testing.assert_frame_equal(employe_brut, copie)