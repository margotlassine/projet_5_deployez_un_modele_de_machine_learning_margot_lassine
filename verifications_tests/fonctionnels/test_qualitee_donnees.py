"""Tests de qualité données: on vient vérifiee que le dataset soit bien inséré en base correctement."""
import pytest
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError

from database_postgresql.create_db import creer_base
from database_postgresql.modeles import EmployeBDD, SessionLocal, engine

# Les 29 colonnes attendues (dans l'ordre de la table)
COLONNES_ATTENDUES = [
    "id", 
    "a_quitte_l_entreprise", 
    "satisfaction_employee_environnement",
    "note_evaluation_precedente", 
    "niveau_hierarchique_poste",
    "satisfaction_employee_nature_travail", 
    "satisfaction_employee_equipe",
    "satisfaction_employee_equilibre_pro_perso", 
    "note_evaluation_actuelle",
    "heure_supplementaires", 
    "augementation_salaire_precedente", 
    "age", 
    "genre",
    "revenu_mensuel", 
    "statut_marital", 
    "departement", 
    "poste",
    "nombre_experiences_precedentes", 
    "annee_experience_totale",
    "annees_dans_l_entreprise", 
    "annees_dans_le_poste_actuel",
    "nombre_participation_pee", 
    "nb_formations_suivies", 
    "distance_domicile_travail",
    "niveau_education", 
    "domaine_etude", 
    "frequence_deplacement",
    "annees_depuis_la_derniere_promotion", 
    "annes_sous_responsable_actuel",
]

#Les colonnes types variables catégorielles
COLONNES_TEXTE = {
    "a_quitte_l_entreprise", 
    "heure_supplementaires", 
    "genre", 
    "statut_marital",
    "departement", "poste", "domaine_etude", "frequence_deplacement",
}


@pytest.fixture(scope="module", autouse=True)
def base_remplie():
    """Creation des tables et insertion du dataset avant les tests de ce fichier."""
    creer_base()


def colonnes_de_la_table():
    """Renvoie de la description des colonnes de la table 'employes'."""
    return inspect(engine).get_columns("employes")


# 1: Le bon nombre de lignes
def test_nombre_de_lignes():
    with SessionLocal() as session:
        nombre = session.scalar(select(func.count()).select_from(EmployeBDD))
    assert nombre == 1470


# 2: Les bonnes colonnes, dans le bon ordre
def test_colonnes_dans_le_bon_ordre():
    noms = [colonne["name"] for colonne in colonnes_de_la_table()]
    assert noms == COLONNES_ATTENDUES


# 3: Les bons types
def test_types_des_colonnes():
    for colonne in colonnes_de_la_table():
        type_attendu = str if colonne["name"] in COLONNES_TEXTE else int
        assert colonne["type"].python_type is type_attendu, colonne["name"]


# 4: Des valeurs cohérentes
@pytest.mark.parametrize("colonne", ["a_quitte_l_entreprise", "heure_supplementaires"])
def test_valeurs_oui_non(colonne):
    with SessionLocal() as session:
        valeurs = set(session.scalars(select(getattr(EmployeBDD, colonne)).distinct()))
    assert valeurs == {"Oui", "Non"}


def test_age_plausible():
    with SessionLocal() as session:
        mini, maxi = session.execute(
            select(func.min(EmployeBDD.age), func.max(EmployeBDD.age))
        ).one()
    assert 18 <= mini and maxi <= 65


@pytest.mark.parametrize("colonne", [
    "satisfaction_employee_environnement",
    "satisfaction_employee_nature_travail",
    "satisfaction_employee_equipe",
    "satisfaction_employee_equilibre_pro_perso",
])
def test_notes_satisfaction_entre_1_et_4(colonne):
    with SessionLocal() as session:
        mini, maxi = session.execute(
            select(func.min(getattr(EmployeBDD, colonne)), func.max(getattr(EmployeBDD, colonne)))
        ).one()
    assert 1 <= mini and maxi <= 4


# 5: Intégrité -> une ligne incomplète est refusée (contrainte NOT NULL)
def test_ligne_incomplete_refusee():
    with SessionLocal() as session:
        session.add(EmployeBDD(age=30))  # il manque toutes les autres colonnes
        with pytest.raises(IntegrityError):
            session.commit()