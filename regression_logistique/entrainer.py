import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from api.preparation import preparer_donnees

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

# 1. Charger et fusionner les 3 fichiers (comme dans le notebook)
df_eval = pd.read_csv("data/extrait_eval.csv").drop(columns=["eval_number"])
df_sirh = pd.read_csv("data/extrait_sirh.csv").drop(columns=["nombre_heures_travailless", "id_employee"])
df_sondage = pd.read_csv("data/extrait_sondage.csv").drop(
    columns=["nombre_employee_sous_responsabilite", "ayant_enfants", "code_sondage"]
)
df = df_eval.merge(df_sirh, left_index=True, right_index=True)
df = df.merge(df_sondage, left_index=True, right_index=True)

# 2. Préparer les données avec LA fonction partagée avec l'API
df = preparer_donnees(df)
X = df[VARIABLES_NUMERIQUES + VARIABLES_CATEGORIELLES]
y = (df["a_quitte_l_entreprise"] == "Oui").astype(int)

# 3. Pipeline avec les meilleurs hyperparamètres trouvés dans le notebook
pipeline = Pipeline([
    ("encodage", ColumnTransformer(transformers=[
        ("num", StandardScaler(), VARIABLES_NUMERIQUES),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), VARIABLES_CATEGORIELLES),
    ])),
    ("model", LogisticRegression(
        C=0.01, solver="liblinear",
        class_weight="balanced", max_iter=1000, random_state=42,
    )),
])

# 4. Entraîner et vérifier sur le jeu de test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)
pipeline.fit(X_train, y_train)
pr_auc = average_precision_score(y_test, pipeline.predict_proba(X_test)[:, 1])
print(f"PR-AUC sur le jeu de test : {pr_auc:.3f}")

# 5. Sauvegarder le modèle entraîné
joblib.dump(pipeline, "regression_logistique/modele_attrition.joblib")
print("Modèle sauvegardé dans regression_logistique/modele_attrition.joblib")