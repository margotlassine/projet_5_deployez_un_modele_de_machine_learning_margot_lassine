import pandas as pd


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