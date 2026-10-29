# TechNova Partners – API de prédiction de l'attrition

API qui prédit si un employé de TechNova Partners risque de quitter l'entreprise (régression logistique). Chaque demande et chaque prédiction sont enregistrées dans PostgreSQL.

**Stack :** Python 3.13 · FastAPI · Pydantic · scikit-learn · PostgreSQL · SQLAlchemy · Pytest · GitHub Actions

## Architecture

```mermaid
flowchart LR
    U[Client] -->|POST /predict| A[API FastAPI + Pydantic]
    A -->|input| D[(PostgreSQL)]
    A --> M[Modèle .joblib]
    A -->|output| D
    A -->|réponse| U
```

| Dossier | Contenu |
|---|---|
| `api/` | API et préparation des données |
| `regression_logistique/` | entraînement et modèle sauvegardé |
| `memoires_demandes/` | base de données (tables, création, requêtes, [schéma](memoires_demandes/SCHEMA.md)) |
| `verifications/` | tests unitaires et fonctionnels |
| `docs/MODELE.md` | [documentation du modèle](docs/MODELE.md) |

## Installation

```bash
git clone https://github.com/margotlassine/projet_5_deployez_un_modele_de_machine_learning_margot_lassine.git
cd projet_5_deployez_un_modele_de_machine_learning_margot_lassine
pip install -r requirements.txt
```

Base de données (PostgreSQL 17) :
```bash
psql postgres -c "CREATE USER technova WITH PASSWORD 'votre_mot_de_passe';"
psql postgres -c "CREATE DATABASE attrition OWNER technova;"
echo "DATABASE_URL=postgresql://technova:votre_mot_de_passe@localhost:5432/attrition" > .env
python -m memoires_demandes.create_db
```

## Utilisation

```bash
uvicorn api.main:app --reload
```

Documentation Swagger : http://127.0.0.1:8000/docs

- `GET /health` : vérifie que l'API est en marche
- `POST /predict` : renvoie la probabilité de départ d'un employé

```bash
curl -X POST http://127.0.0.1:8000/predict -H