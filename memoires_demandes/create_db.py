import pandas as pd

from memoires_demandes.modeles import Base, EmployeBDD, SessionLocal, engine

# 1. Créer les 3 tables (sans effet si elles existent déjà)
Base.metadata.create_all(engine)
print("Tables créées :", list(Base.metadata.tables))

# 2. Charger et fusionner les 3 CSV (comme dans le notebook)
df_eval = pd.read_csv("data/extrait_eval.csv").drop(columns=["eval_number"])
df_sirh = pd.read_csv("data/extrait_sirh.csv").drop(columns=["nombre_heures_travailless", "id_employee"])
df_sondage = pd.read_csv("data/extrait_sondage.csv").drop(
    columns=["nombre_employee_sous_responsabilite", "ayant_enfants", "code_sondage"]
)
df = df_eval.merge(df_sirh, left_index=True, right_index=True)
df = df.merge(df_sondage, left_index=True, right_index=True)

# On stocke l'augmentation en nombre, sans le " %"
df["augementation_salaire_precedente"] = (
    df["augementation_salaire_precedente"].astype(str).str.replace(" %", "").astype(int)
)

# 3. Insérer le dataset, une seule fois
with SessionLocal() as session:
    if session.query(EmployeBDD).count() == 0:
        session.add_all([EmployeBDD(**ligne) for ligne in df.to_dict(orient="records")])
        session.commit()
    print("Employés dans la base :", session.query(EmployeBDD).count())