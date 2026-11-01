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

## Gestion des données

### Parcours des données

```mermaid
flowchart LR
    C[3 fichiers CSV] -->|charger_dataset + nettoyage| E[(employes)]
    R[Requête /predict] -->|validation Pydantic| D[(demandes)]
    D -->|preparer_donnees| M[Modèle]
    M --> P[(predictions)]
    P -.->|demande_id| D
```

1. **Intégration du dataset** : `create_db.py` fusionne les 3 fichiers CSV (évaluations, SIRH, sondage), retire le « % » de l'augmentation de salaire, puis insère les 1 470 employés dans `employes`. L'insertion n'a lieu que si la table est vide, pour éviter les doublons.
2. **Réception d'une demande** : l'API valide les données avec Pydantic, puis les enregistre dans `demandes` **avant** d'appeler le modèle. Une demande reste ainsi tracée même si le modèle échoue.
3. **Prédiction** : les données sont transformées par `preparer_donnees` (la même fonction qu'à l'entraînement), puis envoyées au modèle.
4. **Stockage du résultat** : la probabilité, la décision, la version du modèle et la date sont enregistrées dans `predictions`, reliées à leur demande par `demande_id`.

### Stockage

| Table | Rôle | Alimentée par |
|---|---|---|
| `employes` | données d'origine, pour l'analyse et le réentraînement | `create_db.py` (une fois) |
| `demandes` | inputs reçus par l'API | chaque appel à `/predict` |
| `predictions` | outputs du modèle | chaque appel à `/predict` |

Les données ne sont jamais modifiées après enregistrement : on garde un historique complet et fidèle des échanges.

### Besoins analytiques

Les tables permettent aux RH et à l'équipe data de suivre :

| Besoin | Indicateur | Requête |
|---|---|---|
| Contrôler la traçabilité | chaque demande avec sa prédiction | `requetes.sql` n°1 |
| Repérer les incidents | demandes restées sans prédiction | `requetes.sql` n°2 |
| Surveiller le modèle | répartition des prédictions Oui / Non | `requetes.sql` n°3 |
| Comprendre l'attrition réelle | taux de départ par département | `requetes.sql` n°4 |
| Détecter une dérive | écart entre le taux de « Oui » prédits et le taux réel (~16 %) | comparaison des requêtes 3 et 4 |

**Tableau de bord envisagé** : taux de départs prédits par département et par mois, nombre de demandes par jour, probabilité moyenne, et alerte si la part de « Oui » s'éloigne fortement du taux réel. Ces indicateurs se calculent directement à partir des tables `demandes` et `predictions`.