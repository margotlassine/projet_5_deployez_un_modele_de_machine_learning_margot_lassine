from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

# Un employé valide, réutilisé dans tous les tests
EMPLOYE_VALIDE = {
    "satisfaction_employee_environnement": 2,
    "note_evaluation_precedente": 3,
    "niveau_hierarchique_poste": 2,
    "satisfaction_employee_nature_travail": 4,
    "satisfaction_employee_equipe": 1,
    "satisfaction_employee_equilibre_pro_perso": 1,
    "note_evaluation_actuelle": 3,
    "heure_supplementaires": "Oui",
    "augementation_salaire_precedente": 11,
    "age": 41,
    "genre": "F",
    "revenu_mensuel": 5993,
    "statut_marital": "Célibataire",
    "departement": "Commercial",
    "poste": "Cadre Commercial",
    "nombre_experiences_precedentes": 8,
    "annee_experience_totale": 8,
    "annees_dans_l_entreprise": 6,
    "annees_dans_le_poste_actuel": 4,
    "nombre_participation_pee": 0,
    "nb_formations_suivies": 0,
    "distance_domicile_travail": 1,
    "niveau_education": 2,
    "domaine_etude": "Marketing",
    "frequence_deplacement": "Occasionnel",
    "annees_depuis_la_derniere_promotion": 0,
    "annes_sous_responsable_actuel": 5,
}


# ---------- Cas qui doivent fonctionner ----------

def test_health():
    reponse = client.get("/health")
    assert reponse.status_code == 200
    assert reponse.json() == {"statut": "ok"}


def test_predict_employe_valide():
    reponse = client.post("/predict", json=EMPLOYE_VALIDE)
    assert reponse.status_code == 200
    resultat = reponse.json()
    assert 0 <= resultat["probabilite_depart"] <= 1
    assert resultat["va_quitter"] in ["Oui", "Non"]


# ---------- Scénarios d'erreur : l'API doit refuser (422) ----------

def test_predict_poste_inconnu():
    employe = {**EMPLOYE_VALIDE, "poste": "Astronaute"}
    assert client.post("/predict", json=employe).status_code == 422


def test_predict_niveau_hierarchique_zero():
    employe = {**EMPLOYE_VALIDE, "niveau_hierarchique_poste": 0}
    assert client.post("/predict", json=employe).status_code == 422


def test_predict_champ_manquant():
    employe = {**EMPLOYE_VALIDE}
    del employe["age"]
    assert client.post("/predict", json=employe).status_code == 422


def test_predict_mauvais_type():
    employe = {**EMPLOYE_VALIDE, "age": "quarante"}
    assert client.post("/predict", json=employe).status_code == 422


def test_predict_annees_incoherentes():
    employe = {**EMPLOYE_VALIDE, "annees_dans_l_entreprise": 20, "annee_experience_totale": 8}
    assert client.post("/predict", json=employe).status_code == 422