from api.preparation import charger_dataset
from database_postgresql.create_db import creer_base
from database_postgresql.modeles import EmployeBDD, SessionLocal


def test_creer_base_insere_tout_le_dataset():
    assert creer_base() == len(charger_dataset())


def test_creer_base_n_insere_pas_deux_fois():
    premier = creer_base()
    second = creer_base()
    assert premier == second


def test_donnees_inserees_correctement():
    creer_base()
    with SessionLocal() as session:
        employe = session.query(EmployeBDD).first()
        assert isinstance(employe.augementation_salaire_precedente, int)
        assert employe.a_quitte_l_entreprise in ("Oui", "Non")
        