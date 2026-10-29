import os
from pathlib import Path

# Les tests utilisent une petite base SQLite jetable, jamais la vraie base PostgreSQL.
# On la supprime à chaque lancement pour que les résultats soient reproductibles.
BASE_DE_TEST = Path("test.db")
if BASE_DE_TEST.exists():
    BASE_DE_TEST.unlink()

# load_dotenv() ne remplace pas une variable déjà définie : le .env est donc ignoré ici.
os.environ["DATABASE_URL"] = "sqlite:///./test.db"