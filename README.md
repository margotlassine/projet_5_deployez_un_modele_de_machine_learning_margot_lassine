# TechNova Partners – API de prédiction de l'attrition

API qui prédit si un employé de TechNova Partners risque de quitter l'entreprise (via le modèle de la régression logistique).
Chaque demande et chaque prédiction sont enregistrées dans PostgreSQL.

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
| `database_postgresql/` | base de données (tables, création, requêtes, [schéma](database_postgresql/SCHEMA.md)) |
| `verifications/` | tests unitaires et fonctionnels |
| `docs/MODELE.md` | [documentation du modèle](docs/MODELE.md) |

## Choix techniques

- **FastAPI** : génère automatiquement la documentation Swagger et valide les données grâce à Pydantic.
- **Pydantic** : refuse les données absurdes avant l'appel au modèle (bornes, catégories inconnues, incohérences), avec une erreur 422 claire.
- **Une seule fonction de préparation** : la même est utilisée à l'entraînement et dans l'API, donc les transformations sont toujours identiques.
- **PostgreSQL + SQLAlchemy** : chaque demande et chaque prédiction sont reliées par une clé étrangère, pour une traçabilité complète.
- **Régression logistique** : meilleur PR-AUC (0,638) et meilleur recall parmi les 5 modèles testés, et modèle explicable (détails dans [docs/MODELE.md](docs/MODELE.md)).

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
python -m database_postgresql.create_db
```

## Utilisation

```bash
uvicorn api.main:app --reload
```

Documentation Swagger : http://127.0.0.1:8000/docs

- `GET /health` : vérifie que l'API est en marche
- `POST /predict` : renvoie la probabilité de départ d'un employé

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d @exemple_employe.json
```
Réponse : `{"demande_id": 12, "probabilite_depart": 0.858, "va_quitter": "Oui"}`

Les données invalides sont refusées avec une erreur 422.

## Tests

```bash
pytest
```
26 tests (unitaires et fonctionnels), 99 % de couverture. Le rapport HTML est généré dans `htmlcov/`.

## Déploiement

- **CI/CD** : à chaque push, GitHub Actions lance les tests (environnements dev → test → prod). La fusion dans `main` est bloquée si un test échoue.
- **API** : déployée en local avec `uvicorn`, comme l'autorise la mission.

## Authentification et sécurisation

- Base protégée par un utilisateur dédié et un mot de passe.
- Mot de passe stocké dans `.env`, ignoré par Git.
- Données d'entrée validées par Pydantic.
- Limite : l'API n'a pas d'authentification (POC local). En production, il faudrait ajouter une clé d'API et le HTTPS.

## Conventions

- Branches : `feature/…`, `fix/…`, `docs/…`
- Un tag de version par étape (`v0.1.0` → `v1.0.0`)