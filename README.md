# TechNova Partners – API de prédiction des départs volontaires
Création d'un API qui prédit si un employé de TechNova Partners risque de quitter l'entreprise (via le modèle de la régression logistique).
Chaque demande et chaque prédiction sont enregistrées dans PostgreSQL.

**Stack :** Python 3.13 · FastAPI · Pydantic · scikit-learn · PostgreSQL · SQLAlchemy · Pytest · GitHub Actions


## ARCHITECTURE
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
| `verifications_tests/` | tests unitaires et fonctionnels |
| `docs/MODELE.md` | [documentation du modèle](docs/MODELE.md) |


## LES CHOIX TECHNIQUES
- **FastAPI**: Permet de généree automatiquement la documentation *Swagger* + permet de valider les données grâce à *Pydantic*.
- **Pydantic**: refuse les données "éxagérées" avant d'appeler le modèle (bornes, catégories inconnues, incohérences), avec l'erreur 422.
- **Une seule fonction de préparation**: qui est utilisée à l'entraînement mais aussi dans l'API. Donc les transformations sont toujours identiques.
- **PostgreSQL + SQLAlchemy**: chaque demande et chaque prédiction sont reliées par une clé étrangère -> permet de garantir la traçabilité.
- **Régression logistique**: modèle gardé lors du projet 4 car meilleur PR-AUC (0,638) et meilleur recall parmi les modèles testés.


## L'INSTALLATION
```bash
git clone https://github.com/margotlassine/projet_5_deployez_un_modele_de_machine_learning_margot_lassine.git
cd projet_5_deployez_un_modele_de_machine_learning_margot_lassine
pip install -r requirements.txt
```

Base de données (PostgreSQL 17):
```bash
psql postgres -c "CREATE USER user_1 WITH PASSWORD 'mot_de_passe';"
psql postgres -c "CREATE DATABASE attrition OWNER user_1;"
echo "DATABASE_URL=postgresql://user_1:mot_de_passe@localhost:5432/attrition" > .env
python -m database_postgresql.create_db
```

## L'UTILISATION 
```bash
uvicorn api.main:app --reload
```

La documentation de Swagger = http://127.0.0.1:8000/docs

- `GET /health` -> vérifie que l'API soit bien en marche
- `POST /predict` > renvoie la probabilité de départ volontaire d'un employé

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d @exemple_employe.json
```
Réponse: `{"demande_id": 12, "probabilite_depart": 0.858, "va_quitter": "Oui"}`

Les données invalides sont refusées avec une erreur "**422**".


## LES TESTS UNITAIRES ET FONCTIONNELS
```bash
pytest
```
26 tests (unitaires et fonctionnels), 99 % de couverture --> le rapport HTML est généré dans `htmlcov/`.


## LE DÉPLOIEMENT
- **La pipeline CI/CD**: à chaque push, GitHub Actions lance les tests (environnements dev vers test puis vers prod). On bloque la fusion dans `main` si un test échoue.
- **L'API**: elle est déployée en local via `uvicorn`.


## L'AUTHENTIFICATION ET LA SÉCURISATION 
- La base PostgreSQL `attrition` est accessible avec un utilisateur dédié, `user_1`, protégé par un mot de passe.
- Le mot de passe stocké dans `.env`, ignoré par Git.
- Les données d'entrée doivent être validées par Pydantic.
- Notre limite -> l'API n'a pas d'authentification puisqu'il s'agit d'un POC local. Donc dans la prod, il faudrait ajouter une clé de l'API et le HTTPS.


## LES CONVENTIONS RESPECTÉES 
- Les branches = `feature/…`, `fix/…`, `docs/…`
- Un tag de version par étape (`v0.1.0` → `v1.0.0`)


## LA GESTION DES DONNÉES

### LE PARCOURS DES DONNÉES
```mermaid
flowchart LR
    C[3 fichiers CSV] -->|charger_dataset + nettoyage| E[(employes)]
    R[Requête /predict] -->|validation Pydantic| D[(demandes)]
    D -->|preparer_donnees| M[Modèle]
    M --> P[(predictions)]
    P -.->|demande_id| D
```

1. **Intégration des 3 fichiers en un dataset**
    - `create_db.py` vient construire les tables en fusionnant les 3 fichiers CSV (évaluations, SIRH, sondage),
    - retire le « % » de l'augmentation de salaire pour que toutes les données soient similaires,
    - insère et range les 1 470 employés dans `employes` --> Attention, intégration uniquement si la table est vide, pour éviter les doublons.

2. **Réception d'une demande** 
    - l'API valide les données avec Pydantic, 
    - elle les enregistre dans `demandes` avant d'appeler le modèle --> permet de tracée les demandes même si le modèle échoue !

3. **Prédiction** 
    - les données sont transformées par `preparer_donnees` 
    - elles sont envoyées au modèle.

4. **Stockage du résultat** 
    - la probabilité la décision, 
    - la version du modèle 
    - la date 
    --> sont enregistrées dans `predictions` & reliées à leur demande par `demande_id`.


### LE STOCKAGE
| Table | Rôle | Alimentée par |
|---|---|---|
| `employes` | les données d'origine, pour l'analyse et le réentraînement | `create_db.py` (une fois) |
| `demandes` | INputs reçus par l'API | chaque appel à `/predict` |
| `predictions` | OUTputs du modèle | chaque appel à `/predict` |

--> On ne modifie pas les données après l'enregistrement, on va garder un historisque complet des échanges. 


### LES BESOINS ANALYTIQUES
Les tables vont permettent aux RH et à l'équipe data de suivre:

| Besoin | Indicateur | Requête |
|---|---|---|
| Contrôler la traçabilité | chaque demande avec sa prédiction | `requetes.sql` n°1 |
| Repérer les incidents | demandes restées sans prédiction | `requetes.sql` n°2 |
| Surveiller le modèle | répartition des prédictions Oui / Non | `requetes.sql` n°3 |
| Comprendre l'attrition réelle | taux de départ par département | `requetes.sql` n°4 |
| Détecter une dérive | écart entre le taux de « Oui » prédits et le taux réel (~16 %) | comparaison des requêtes 3 et 4 |

**Tableau de bord envisagé** avec: 
- le taux de départs prédits par département et par mois, 
- le nombre de demandes par jour, 
- la probabilité moyenne, 
- une alerte si la part de « Oui » s'éloigne fortement du taux réel. 
--> Ces indicateurs se calculent directement à partir des tables `demandes` et `predictions`.