from api.preparation import charger_dataset
from database_postgresql.modeles import Base, EmployeBDD, SessionLocal, engine


def creer_base() -> int:
    """Construction des des tables,
     Lecture des 3 fichiers (+ on enlève le % à l'augmentation des salaires),
     Rangement des employés dans la table (seulement si vide pour ne pas les ranger 2 fois)"""
    Base.metadata.create_all(engine)

    df = charger_dataset()
    # Suppression du % pour l'augmentation du salaire 
    df["augementation_salaire_precedente"] = (
        df["augementation_salaire_precedente"].astype(str).str.replace(" %", "").astype(int)
    )

    with SessionLocal() as session:
        if session.query(EmployeBDD).count() == 0:
            session.add_all([EmployeBDD(**ligne) for ligne in df.to_dict(orient="records")])
            session.commit()
        return session.query(EmployeBDD).count()


if __name__ == "__main__":
    print("Tables créées =", list(Base.metadata.tables))
    print("Employés dans la base =", creer_base())