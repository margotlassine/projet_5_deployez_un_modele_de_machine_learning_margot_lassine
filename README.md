# TechNova Partners: API de prédiction de l'attrition

## Présentation du projet
Mise en place d'une API qui permet de prédire si un employé de l'entreprise TechNova risque de partir ou non de l'entreprise.

## Structure du projet
- "api/": code de l'API (FastAPI)
- "regression_logistique/": notre modèle entraîné 
- "memoires_demandes/": base de données PostgreSQL
- "verifications/": tests (Pytest)
- ".github/workflows/": pipeline CI/CD

## Installation


## Utilisation


## Déploiement
  

## Authentification
        

## Sécurisation


## Base de données

PostgreSQL en local. Schéma détaillé : [memoires_demandes/SCHEMA.md](memoires_demandes/SCHEMA.md)

**Installation**
```bash
brew install postgresql@17
brew services start postgresql@17
psql postgres -c "CREATE USER technova WITH PASSWORD 'votre_mot_de_passe';"
psql postgres -c "CREATE DATABASE attrition OWNER technova;"
echo "DATABASE_URL=postgresql://technova:votre_mot_de_passe@localhost:5432/attrition" > .env
python -m memoires_demandes.create_db
```

**Sécurité**
- Un utilisateur dédié (`technova`), propriétaire de sa seule base.
- Le mot de passe est dans `.env`, ignoré par Git : il n'est jamais publié.
- Les tests utilisent une base SQLite jetable : ils ne touchent jamais la vraie base.

**Traçabilité** : chaque appel à `/predict` enregistre l'input dans `demandes`, puis l'output dans `predictions`. Requêtes d'exemple : `memoires_demandes/requetes.sql`. Exemples réels : `memoires_demandes/exemples_inputs_outputs.csv`.