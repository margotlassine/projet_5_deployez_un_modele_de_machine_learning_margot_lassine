# Documentation du modèle de prédiction de l'attrition

## 1- OBJECTIF
Prédire si un employé de TechNova Partners risque de quitter l'entreprise pour que les RH puissent agir avant son départ.

## 2- DONNEES
- 3 fichiers fusionnés (évaluations, SIRH, sondage) soit 1 470 employés.
- La cible = `a_quitte_l_entreprise` (Oui / Non), avec environ 16 % de départs --> Autrement dit, les classes sont déséquilibrées.
- Nos colonnes supprimées = `nombre_heures_travailless`, `nombre_employee_sous_responsabilite` + `ayant_enfants` (valeurs constantes), ainsi que les identifiants.

**Les Variables créées** dans `api/preparation.py`:

| Variable | Calcul | Idée métier |
|---|---|---|
| `evolution_promotion` | années sans promotion / (ancienneté + 1) | stagnation de carrière |
| `revenus_vs_niveau` | revenu / niveau hiérarchique | rémunération par rapport au poste |
| `xp_entreprise_vs_totale` | ancienneté / (expérience totale + 1) | fidélité à l'entreprise |
| `experience_externe` | expérience totale − ancienneté | expérience acquise ailleurs |
| `surcharge_ressentie` | heures sup × (5 − équilibre vie pro/perso) | épuisement |

## 3- CHOIX DU MODELE 
5 modèles comparés sur le même jeu de test pour 294 employés, dont 47 départs:

| Modèle | Recall | Précision | F1 | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|
| **Régression logistique** | **0,723** | 0,351 | 0,472 | **0,638** | **0,821** |
| SVC (noyau) | 0,681 | 0,400 | 0,504 | 0,554 | 0,820 |
| KNN | 0,064 | 0,750 | 0,118 | 0,467 | 0,784 |
| Random Forest | 0,128 | 0,500 | 0,203 | 0,434 | 0,784 |
| Dummy (référence) | 0,128 | 0,122 | 0,125 | 0,155 | 0,477 |

**Explications du choix de la régression logistique:**
- c'est le meilleur **PR-AUC** et cette métrique est particulièrement adaptée aux classes déséquilibrées,
- c'est le meilleur **recall** qui repère 72 % des départs réels,
- c'est un modèle **explicable**, autrement dit, ses coefficients se lisent directement, ce qui compte pour justifier une action RH.

**Les hyperparamètres** (GridSearchCV, validation croisée à 5 plis, score PR-AUC): `C=0.01`, pénalité L2, solveur `liblinear`, `class_weight="balanced"`.

## 4- SEUIL DE PROBABILITE: DECISION METIER
Le modèle renvoie une probabilité. Au-delà du seuil de 0.5, l'API répond « Oui ».

On privilégie le recall: pour les RH, il vaut mieux s'entretenir avec un employé qui ne serait pas parti (donc un faux positif) que de passer à côté d'un vrai départ (un faux négatif). 
Un seuil de 0,64 maximiserait le F1 (précision 0,58, recall 0,60), mais il laisserait passer davantage de départs.

## 5- LES LIMITES CONNUES
- Précision de 35 %: sur 3 employés signalés, environ 1 seul part réellement. La prédiction est une alerte à vérifier, pas une décision.
- Corrélation, pas causalité: le modèle repère des profils à risque, il n'explique pas à lui seul pourquoi un employé part.
- Données fictives et datées: le modèle doit être réentraîné sur des données réelles et récentes avant tout usage en production.
- Catégories fermées: un nouveau poste ou un nouveau département sera refusé par l'API (erreur 422). Il faudra alors réentraîner le modèle.

## 6- LES GARANTIES AVEC LES TESTS AUTO 
- `verifications_tests/unitaires/test_modele.py` vérifie à chaque push que:
  - les probabilités sont valides,
  - le PR-AUC reste bien ≥ 0,55,
  - l'entraînement est reproductible(`random_state=42`),
  - le fichier `.joblib` correspond bien au code actuel,
- Les versions des bibliothèques sont fixées dans `requirements.txt`: un modèle sauvegardé ne se recharge qu'avec la même version de scikit-learn.

## 7- PROTOCOLE DE MAJ
**Savoir quand réentraîner**
- on peut se dire qu'il serait bon de réentraîner tous les 6 mois avec des nouvelles données RH, 
- sinon, on peut se dire qu'il faut le faire immédiatement lorsqu'un nouveau poste ou nouveau département apparaît,
- ou alors, on réentraîne si la part de « Oui » dans la table `predictions` s'écarte beaucoup du taux réel de départ,

**Comment réentraîner**
1. Créer une branche: `git switch -c feature/reentrainement-AAAA-MM`.
2. Mettre à jour les fichiers dans `data/`.
3. Réentraîner: `python -m regression_logistique.entrainer`.
4. Vérifier que le PR-AUC affiché reste au moins égal à 0,55.
5. Incrémenter `VERSION_DU_MODELE` dans `api/main.py` (par exemple `reglog-v2`). Les anciennes prédictions gardent ainsi leur version d'origine en base.
6. Lancer `pytest`, puis ouvrir une pull request. Le robot bloque la fusion si un test échoue.
7. Après la fusion, poser un tag de version.

**Comment surveiller:** 
Les requêtes de `database_postgresql/requetes.sql` permettent de suivre la répartition des prédictions et de repérer les demandes restées sans réponse.


## 8- ACCÈS AU MODÈLE
- Le modèle est enregistré dans le fichier `.joblib` il n'est chargé qu'une seule fois, lors du démarrage de l'API `api/main.py`.
- On n'y accès pas directement, il est utilisé uniquement avec l'endpoint `POST /predict`.
- Les données qui sont envoyées, sont d'abord validées par Pydantic
  - Une donnée incorrecte sera refusée avec l'erreur 422 avant d'atteindre le modèle. 
- Chaque demande ainsi que sa prédiction seront enregistrées dans PostgreSQL
  - avec la version du modèle (`version_modele`)
  - on pourra donc retrouver quel modèle a donné quel résultat
- L'accès à la base se fait avec les identifiants du fichier`.env` dans la section "Authentification et sécurisation" du fichier README.
 (voir la section « Authentification et sécurisation » du README).