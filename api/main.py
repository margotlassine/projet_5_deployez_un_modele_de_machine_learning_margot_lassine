from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field, model_validator

from api.preparation import preparer_donnees
from database_postgresql.modeles import Base, Demande, Prediction, SessionLocal, engine

# Chargement du modèle en démarrage de l'API (une seule fois)
CHEMIN_DU_MODEL = Path(__file__).parent.parent / "regression_logistique" / "modele_attrition.joblib"
modele = joblib.load(CHEMIN_DU_MODEL)

SEUIL = 0.5  # seuil de probabilité/ de décision gardé lors du projet 4 
VERSION_DU_MODELE = "reglog-v1"

# Création des tables si elles existent pas encore
Base.metadata.create_all(engine)

DESCRIPTION_DE_L_API = """
API de prédiction de l'attrition (= les départs volontaires) des employés de l'entreprise TechNova Partners.
* Modèle utilisé: La régression logistique entraînée sur 1 470 employés.
* Données d'entrée: Les 27 caractéristiques d'un employé (depuis les 3 fichiers de données "évaluation", "SIRH", "sondages").
* Données de sortie: La probabilité de départ et la décision au seuil de 0,5.
* La traçabilité: Chaque demande + chaque prédiction sont enregistrées dans PostgreSQL.
"""

app = FastAPI(
    title="API Départs volontaires chez TechNova",
    description=DESCRIPTION_DE_L_API,
    version="1.0.0",
)


class Employe(BaseModel):
    """Les 27 types de données d'un employé (comme envoyées à l'API)."""

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "satisfaction_employee_environnement": 1,
                "note_evaluation_precedente": 3,
                "niveau_hierarchique_poste": 1,
                "satisfaction_employee_nature_travail": 1,
                "satisfaction_employee_equipe": 2,
                "satisfaction_employee_equilibre_pro_perso": 1,
                "note_evaluation_actuelle": 3,
                "heure_supplementaires": "Oui",
                "augementation_salaire_precedente": 11,
                "age": 23,
                "genre": "M",
                "revenu_mensuel": 2100,
                "statut_marital": "Célibataire",
                "departement": "Commercial",
                "poste": "Représentant Commercial",
                "nombre_experiences_precedentes": 1,
                "annee_experience_totale": 2,
                "annees_dans_l_entreprise": 1,
                "annees_dans_le_poste_actuel": 1,
                "nombre_participation_pee": 0,
                "nb_formations_suivies": 1,
                "distance_domicile_travail": 22,
                "niveau_education": 2,
                "domaine_etude": "Marketing",
                "frequence_deplacement": "Frequent",
                "annees_depuis_la_derniere_promotion": 0,
                "annes_sous_responsable_actuel": 0,
            }]
        }
    }

    # Données aux notes de 1 à 4
    satisfaction_employee_environnement: int = Field(ge=1, le=4)
    note_evaluation_precedente: int = Field(ge=1, le=4)
    satisfaction_employee_nature_travail: int = Field(ge=1, le=4)
    satisfaction_employee_equipe: int = Field(ge=1, le=4)
    satisfaction_employee_equilibre_pro_perso: int = Field(ge=1, le=4)
    note_evaluation_actuelle: int = Field(ge=1, le=4)
    
    # Données aux notes de 1 à 5
    niveau_hierarchique_poste: int = Field(ge=1, le=5)
    niveau_education: int = Field(ge=1, le=5)
    
    # Données de type valeurs numériques
    age: int = Field(ge=18, le=70)
    revenu_mensuel: int = Field(gt=0)
    augementation_salaire_precedente: int = Field(ge=0, le=100, description="En %, sans le symbole")
    distance_domicile_travail: int = Field(ge=0)
    nombre_experiences_precedentes: int = Field(ge=0)
    annee_experience_totale: int = Field(ge=0, le=50)
    annees_dans_l_entreprise: int = Field(ge=0, le=50)
    annees_dans_le_poste_actuel: int = Field(ge=0, le=50)
    annees_depuis_la_derniere_promotion: int = Field(ge=0, le=50)
    annes_sous_responsable_actuel: int = Field(ge=0, le=50)
    nombre_participation_pee: int = Field(ge=0)
    nb_formations_suivies: int = Field(ge=0)
    
    # Données de type catégorielles: attention on accepte seulement les valeurs connues du modèle !
    heure_supplementaires: Literal["Oui", "Non"]
    frequence_deplacement: Literal["Aucun", "Occasionnel", "Frequent"]
    genre: Literal["F", "M"]
    statut_marital: Literal["Célibataire", "Marié(e)", "Divorcé(e)"]
    departement: Literal["Commercial", "Consulting", "Ressources Humaines"]
    poste: Literal[
        "Assistant de Direction", "Cadre Commercial", "Consultant",
        "Directeur Technique", "Manager", "Représentant Commercial",
        "Ressources Humaines", "Senior Manager", "Tech Lead",
    ]
    domaine_etude: Literal[
        "Autre", "Entrepreunariat", "Infra & Cloud", "Marketing",
        "Ressources Humaines", "Transformation Digitale",
    ]

    # Création d'une petite règle qui bloque si le nb d'annees dans l'entreprise n'est pas + grand que le nombre d'annees d'XP totale 
    @model_validator(mode="after")
    def regle_annees(self):
        if self.annees_dans_l_entreprise > self.annee_experience_totale:
            raise ValueError(
                "annees_dans_l_entreprise ne doit pas pouvoir dépasser annee_experience_totale"
            )
        return self


class ReponsePrediction(BaseModel):
    """La réponse renvoyée par '/predict'."""
    demande_id: int = Field(description="Identifiant de la demande dans la base (pour la traçabilité)")
    probabilite_de_depart: float = Field(ge=0, le=1, description="Probabilité que l'employé quitte l'entreprise")
    va_quitter: Literal["Oui", "Non"] = Field(description="Décision d'après le seuil de probabilité à 0,5")


@app.get("/health", tags=["Supervision"], summary="Vérifier que l'API fonctionne correctement")
def health():
    return {"statut": "ok"}


@app.post(
    "/predict",
    tags=["Prédiction"],
    summary="Prédire le risque de départ d'un employé",
    description=(
        "Enregistre la demande, calcule la probabilité de départ avec le modèle, "
        "enregistre la prédiction puis la renvoie. Renvoie une erreur 422 si les données "
        "sont invalides (champ manquant, valeur hors bornes, catégorie inconnue)."
    ),
    response_model=ReponsePrediction,
)
def predict(employe: Employe):
    with SessionLocal() as session:
        # step 1 = On enregistre l'INput avant d'appeler le modèle
        demande = Demande(**employe.model_dump())
        session.add(demande)
        session.commit()

        # step 2 = On appelle le modèle
        df = preparer_donnees(pd.DataFrame([employe.model_dump()]))
        probabilite = float(modele.predict_proba(df)[0, 1])

        # step 3 = On enregistre l'OUTput 
        prediction = Prediction(
            demande_id=demande.id,
            probabilite_depart=round(probabilite, 3),
            va_quitter="Oui" if probabilite >= SEUIL else "Non",
            version_modele=VERSION_DU_MODELE,
        )
        session.add(prediction)
        session.commit()

        return {
            "demande_id": demande.id,
            "probabilite_de_depart": prediction.probabilite_depart,
            "va_quitter": prediction.va_quitter,
        }