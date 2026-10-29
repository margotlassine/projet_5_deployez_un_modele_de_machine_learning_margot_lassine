from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field, model_validator

from api.preparation import preparer_donnees

# Chargement du modèle UNE seule fois, au démarrage de l'API
CHEMIN_MODELE = Path(__file__).parent.parent / "regression_logistique" / "modele_attrition.joblib"
modele = joblib.load(CHEMIN_MODELE)

SEUIL = 0.5  # seuil retenu dans le notebook (recall de 80 %)

app = FastAPI(
    title="API Attrition TechNova Partners",
    description="Prédit si un employé risque de quitter l'entreprise.",
    version="0.3.0",
)


class Employe(BaseModel):
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


@app.get("/health")
def health():
    return {"statut": "ok"}


@app.post("/predict")
def predict(employe: Employe):
    df = pd.DataFrame([employe.model_dump()])
    df = preparer_donnees(df)
    probabilite = modele.predict_proba(df)[0, 1]
    return {
        "probabilite_depart": round(float(probabilite), 3),
        "va_quitter": "Oui" if probabilite >= SEUIL else "Non",
    }