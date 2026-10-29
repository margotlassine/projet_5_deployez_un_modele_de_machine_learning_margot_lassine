import os

# Les tests utilisent une petite base SQLite jetable, jamais la vraie base PostgreSQL.
# load_dotenv() ne remplace pas une variable déjà définie : le .env est donc ignoré ici.
os.environ["DATABASE_URL"] = "sqlite:///./test.db"