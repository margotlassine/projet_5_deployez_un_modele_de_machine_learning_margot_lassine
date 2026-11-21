import os
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

#Accès à la base de données:
#Les identifiants (user + mot de passe) ne sont pas écrits dans le code mais rangés dans le fichier .env qui sera ignoré par Git avec gitignore.
#load_dotenv() va charger ce fichier, puis on va lire la variable DATABASE_URL.
#dans le cas où elle est absente os.environ[...] va lever une erreur et le programme s'arrêtera sur .load_dotenv()
load_dotenv()
DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class ColonnesEmploye:
    """Les 27 caractéristiques d'un employé, partagées par "employes" et "demandes"."""
    satisfaction_employee_environnement: Mapped[int] = mapped_column(Integer)
    note_evaluation_precedente: Mapped[int] = mapped_column(Integer)
    niveau_hierarchique_poste: Mapped[int] = mapped_column(Integer)
    satisfaction_employee_nature_travail: Mapped[int] = mapped_column(Integer)
    satisfaction_employee_equipe: Mapped[int] = mapped_column(Integer)
    satisfaction_employee_equilibre_pro_perso: Mapped[int] = mapped_column(Integer)
    note_evaluation_actuelle: Mapped[int] = mapped_column(Integer)
    heure_supplementaires: Mapped[str] = mapped_column(String(3))
    augementation_salaire_precedente: Mapped[int] = mapped_column(Integer)
    age: Mapped[int] = mapped_column(Integer)
    genre: Mapped[str] = mapped_column(String(1))
    revenu_mensuel: Mapped[int] = mapped_column(Integer)
    statut_marital: Mapped[str] = mapped_column(String(20))
    departement: Mapped[str] = mapped_column(String(30))
    poste: Mapped[str] = mapped_column(String(40))
    nombre_experiences_precedentes: Mapped[int] = mapped_column(Integer)
    annee_experience_totale: Mapped[int] = mapped_column(Integer)
    annees_dans_l_entreprise: Mapped[int] = mapped_column(Integer)
    annees_dans_le_poste_actuel: Mapped[int] = mapped_column(Integer)
    nombre_participation_pee: Mapped[int] = mapped_column(Integer)
    nb_formations_suivies: Mapped[int] = mapped_column(Integer)
    distance_domicile_travail: Mapped[int] = mapped_column(Integer)
    niveau_education: Mapped[int] = mapped_column(Integer)
    domaine_etude: Mapped[str] = mapped_column(String(40))
    frequence_deplacement: Mapped[str] = mapped_column(String(20))
    annees_depuis_la_derniere_promotion: Mapped[int] = mapped_column(Integer)
    annes_sous_responsable_actuel: Mapped[int] = mapped_column(Integer)


class EmployeBDD(ColonnesEmploye, Base):
    """Le dataset de base des 1 470 employés."""
    __tablename__ = "employes"
    id: Mapped[int] = mapped_column(primary_key=True)
    a_quitte_l_entreprise: Mapped[str] = mapped_column(String(3))


class Demande(ColonnesEmploye, Base):
    """Les INputs = chaque employé est envoyé à l'API."""
    __tablename__ = "demandes"
    id: Mapped[int] = mapped_column(primary_key=True)
    date_demande: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    prediction: Mapped["Prediction"] = relationship(back_populates="demande")


class Prediction(Base):
    """Les OUTputs = la réponse du modèle avec sa demande initiale."""
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(primary_key=True)
    demande_id: Mapped[int] = mapped_column(ForeignKey("demandes.id"), unique=True)
    probabilite_depart: Mapped[float] = mapped_column(Float)
    va_quitter: Mapped[str] = mapped_column(String(3))
    version_modele: Mapped[str] = mapped_column(String(20))
    date_prediction: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    demande: Mapped["Demande"] = relationship(back_populates="prediction")