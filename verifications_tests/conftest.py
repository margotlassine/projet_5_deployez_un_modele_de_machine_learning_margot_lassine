import os
from pathlib import Path

#Suppression à chaque lancement de la base de test SQLite version jetable (on évite de pouler la vraie base PostgreSQL)
# pour que les résultats soient reproductibles !
BASE_DE_TEST = Path("test.db")
if BASE_DE_TEST.exists():
    BASE_DE_TEST.unlink()

#load_dotenv() ne remplace pas une variable déjà définie -> le .env est donc ignoré.
os.environ["DATABASE_URL"] = "sqlite:///./test.db"