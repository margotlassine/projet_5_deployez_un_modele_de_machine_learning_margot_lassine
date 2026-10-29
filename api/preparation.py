from pathlib import Path

import pandas as pd

DOSSIER_DATA = Path(__file__).parent.parent / "data"


def preparer_donnees(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 1. Retirer le " %" de l'augmentation de salaire
    df["augementation_salaire_precedente"] = (
        df["augementation_salaire_precedente"].astype(str).str.replace(" %", "").astype(int)
    )

    # 2. Heures supplémentaires : Oui/Non -> 1/0
    df["heure_supplementaires"] = (df["heure_supplementaires"] == "Oui").astype(int)

    # 3. Fréquence de déplacement : texte -> 0/1/2
    df["frequence_deplacement"] = df["frequence_deplacement"].map(
        {"Aucun": 0, "Occasionnel": 1, "Frequent": 2}
    )

    # 4. Ancienneté sans promotion, rapportée à l'ancienneté
    df["evolution_promotion"] = (
        df["annees_depuis_la_derniere_promotion"] / (df["annees_dans_l_entreprise"] + 1)
    )

    # 5. Revenu rapporté au niveau hiérarchique
    df["revenus_vs_niveau"] = df["revenu_mensuel"] / df["niveau_hierarchique_poste"]

    # 6. Part de l'expérience passée chez TechNova
    df["xp_entreprise_vs_totale"] = (
        df["annees_dans_l_entreprise"] / (df["annee_experience_totale"] + 1)
    )

    # 7. Expérience acquise ailleurs
    df["experience_externe"] = (
        df["annee_experience_totale"] - df["annees_dans_l_entreprise"]
    )

    # 8. Surcharge : heures sup x mauvais équilibre vie pro/perso
    df["surcharge_ressentie"] = (
        df["heure_supplementaires"] * (5 - df["satisfaction_employee_equilibre_pro_perso"])
    )

    return df


def charger_dataset() -> pd.DataFrame:
    """Charge et fusionne les 3 fichiers CSV bruts (comme dans le notebook)."""
    df_eval = pd.read_csv(DOSSIER_DATA / "extrait_eval.csv").drop(columns=["eval_number"])
    df_sirh = pd.read_csv(DOSSIER_DATA / "extrait_sirh.csv").drop(
        columns=["nombre_heures_travailless", "id_employee"]
    )
    df_sondage = pd.read_csv(DOSSIER_DATA / "extrait_sondage.csv").drop(
        columns=["nombre_employee_sous_responsabilite", "ayant_enfants", "code_sondage"]
    )
    df = df_eval.merge(df_sirh, left_index=True, right_index=True)
    return df.merge(df_sondage, left_index=True, right_index=True)