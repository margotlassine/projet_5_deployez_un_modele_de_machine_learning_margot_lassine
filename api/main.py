from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field, model_validator

from api.preparation import preparer_donnees
from memoires_demandes.modeles import Base, Demande, Prediction, SessionLocal, engine

# Chargement du modèle UNE seule fois, au démarrage de l'API
CHEMIN_MODELE = Path(__file__).parent.parent / "regression_logistique" / "modele_attrition.joblib"
modele = joblib.load(CHEMIN_MODELE)

SEUIL = 0.5  # seuil retenu dans le notebook (recall de 80 %)
VERSION_MODELE = "reglog-v1"

# Création des tables si elles n'existent pas encore
Base.metadata.create_all(engine)

DESCRIPTION_API = """
API de prédiction de l'**attrition** (départ volontaire) des employés de TechNova Partners.

* **Modèle** : régression logistique (scikit-learn), entraînée sur 1 470 employés.
* **Entrée** : les 27 caractéristiques d'un employé (évaluation, SIRH, sondage).
* **Sortie** : la probabilité de départ et la décision au seuil de 0,5.
* **Traçabilité** : chaque demande et chaque prédiction sont enregistrées dans PostgreSQL.
"""

app = FastAPI(
    title="API Attrition TechNova Partners",
    description=DESCRIPTION_API,
    version="1.0.0",
)


class Employe(BaseModel):
    """Les 27 caractéristiques d'un employé, telles qu'envoyées à l'API."""

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

    # Échelles de 1 à 4
    satisfaction_employee_environnement: int = Field(ge=1, le=4)
    note_evaluation_precedente: int = Field(ge=1, le=4)
    satisfaction_employee_nature_travail: int = Field(ge=1, le=4)
    satisfaction_employee_equipe: int = Field(ge=1, le=4)
    satisfaction_employee_equilibre_pro_perso: int = Field(ge=1, le=4)
    note_evaluation_actuelle: int = Field(ge=1, le=4)
    # Échelles de 1 à 5
    niveau_hierarchique_poste: int = Field(ge=1, le=5)
    niveau_education: int = Field(ge=1, le=5)
    # Valeurs numériques
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
    # Catégories : seules les valeurs connues du modèle sont acceptées
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

    # Règle de cohérence entre deux champs
    @model_validator(mode="after")
    def verifier_coherence(self):
        if self.annees_dans_l_entreprise > self.annee_experience_totale:
            raise ValueError(
                "annees_dans_l_entreprise ne peut pas dépasser annee_experience_totale"
            )
        return self


class ReponsePrediction(BaseModel):
    """La réponse renvoyée par /predict."""
    demande_id: int = Field(description="Identifiant de la demande dans la base (traçabilité)")
    probabilite_depart: float = Field(ge=0, le=1, description="Probabilité que l'employé quitte l'entreprise")
    va_quitter: Literal["Oui", "Non"] = Field(description="Décision au seuil de 0,5")


@app.get("/health", tags=["Supervision"], summary="Vérifier que l'API est en marche")
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
        # 1. Enregistrer l'INPUT avant d'appeler le modèle
        demande = Demande(**employe.model_dump())
        session.add(demande)
        session.commit()

        # 2. Appeler le modèle
        df = preparer_donnees(pd.DataFrame([employe.model_dump()]))
        probabilite = float(modele.predict_proba(df)[0, 1])

        # 3. Enregistrer l'OUTPUT, relié à sa demande
        prediction = Prediction(
            demande_id=demande.id,
            probabilite_depart=round(probabilite, 3),
            va_quitter="Oui" if probabilite >= SEUIL else "Non",
            version_modele=VERSION_MODELE,
        )
        session.add(prediction)
        session.commit()

        return {
            "demande_id": demande.id,
            "probabilite_depart": prediction.probabilite_depart,
            "va_quitter": prediction.va_quitter,
        }