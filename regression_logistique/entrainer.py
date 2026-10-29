from pathlib import Path

import joblib
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from api.preparation import charger_dataset, preparer_donnees

CHEMIN_MODELE = Path(__file__).parent / "modele_attrition.joblib"

VARIABLES_CATEGORIELLES = ["genre", "statut_marital", "departement", "poste", "domaine_etude"]
VARIABLES_NUMERIQUES = [
    "satisfaction_employee_environnement", "note_evaluation_precedente",
    "niveau_hierarchique_poste", "satisfaction_employee_nature_travail",
    "satisfaction_employee_equipe", "satisfaction_employee_equilibre_pro_perso",
    "note_evaluation_actuelle", "heure_supplementaires",
    "augementation_salaire_precedente", "age", "revenu_mensuel",
    "nombre_experiences_precedentes", "annee_experience_totale",
    "annees_dans_l_entreprise", "annees_dans_le_poste_actuel",
    "nombre_participation_pee", "nb_formations_suivies",
    "distance_domicile_travail", "niveau_education", "frequence_deplacement",
    "annees_depuis_la_derniere_promotion", "annes_sous_responsable_actuel",
    "evolution_promotion", "revenus_vs_niveau", "xp_entreprise_vs_totale",
    "experience_externe", "surcharge_ressentie",
]


def construire_pipeline() -> Pipeline:
    """Pipeline avec les meilleurs hyperparamètres trouvés dans le notebook."""
    return Pipeline([
        ("encodage", ColumnTransformer(transformers=[
            ("num", StandardScaler(), VARIABLES_NUMERIQUES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), VARIABLES_CATEGORIELLES),
        ])),
        ("model", LogisticRegression(
            C=0.01, solver="liblinear",
            class_weight="balanced", max_iter=1000, random_state=42,
        )),
    ])


def separer(df):
    """Sépare X/y puis train/test, toujours de la même façon (random_state fixé)."""
    X = df[VARIABLES_NUMERIQUES + VARIABLES_CATEGORIELLES]
    y = (df["a_quitte_l_entreprise"] == "Oui").astype(int)
    return train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)


if __name__ == "__main__":
    X_train, X_test, y_train, y_test = separer(preparer_donnees(charger_dataset()))
    pipeline = construire_pipeline().fit(X_train, y_train)
    pr_auc = average_precision_score(y_test, pipeline.predict_proba(X_test)[:, 1])
    print(f"PR-AUC sur le jeu de test : {pr_auc:.3f}")
    joblib.dump(pipeline, CHEMIN_MODELE)
    print(f"Modèle sauvegardé dans {CHEMIN_MODELE}")