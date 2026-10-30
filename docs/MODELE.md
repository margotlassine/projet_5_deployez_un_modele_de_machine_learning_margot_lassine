# Documentation du modèle de prédiction de l'attrition

## 1. Objectif
Prédire si un employé de TechNova Partners risque de quitter l'entreprise, afin que les RH puissent agir **avant** son départ.

## 2. Données
- 3 fichiers fusionnés (évaluations, SIRH, sondage) : **1 470 employés**.
- Cible : `a_quitte_l_entreprise` (Oui / Non), avec environ **16 % de départs**. Les classes sont donc déséquilibrées.
- Colonnes supprimées : `nombre_heures_travailless`, `nombre_employee_sous_responsabilite` et `ayant_enfants` (valeurs constantes), ainsi que les identifiants.

**Variables créées** (dans `api/preparation.py`) :

| Variable | Calcul | Idée métier |
|---|---|---|
| `evolution_promotion` | années sans promotion / (ancienneté + 1) | stagnation de carrière |
| `revenus_vs_niveau` | revenu / niveau hiérarchique | rémunération par rapport au poste |
| `xp_entreprise_vs_totale` | ancienneté / (expérience totale + 1) | fidélité à l'entreprise |
| `experience_externe` | expérience totale − ancienneté | expérience acquise ailleurs |
| `surcharge_ressentie` | heures sup × (5 − équilibre vie pro/perso) | épuisement |

## 3. Choix du modèle
5 modèles comparés sur le même jeu de test (294 employés, dont 47 départs) :

| Modèle | Recall | Précision | F1 | PR-AUC | ROC-AUC |
|---|---|---|---|---|---|
| **Régression logistique** | **0,723** | 0,351 | 0,472 | **0,638** | **0,821** |
| SVC (noyau) | 0,681 | 0,400 | 0,504 | 0,554 | 0,820 |
| KNN | 0,064 | 0,750 | 0,118 | 0,467 | 0,784 |
| Random Forest | 0,128 | 0,500 | 0,203 | 0,434 | 0,784 |
| Dummy (référence) | 0,128 | 0,122 | 0,125 | 0,155 | 0,477 |

**Pourquoi la régression logistique :**
- c'est le meilleur **PR-AUC**, la métrique adaptée aux classes déséquilibrées ;
- c'est le meilleur **recall** : elle repère 72 % des départs réels ;
- c'est un modèle **explicable** : ses coefficients se lisent directement, ce qui compte pour justifier une action RH.

**Hyperparamètres** (GridSearchCV, validation croisée à 5 plis, score PR-AUC) : `C=0.01`, pénalité L2, solveur `liblinear`, `class_weight="balanced"`.

## 4. Seuil de décision
Le modèle renvoie une probabilité. Au-delà de **0,5**, l'API répond « Oui ».

On privilégie le **recall** : pour les RH, il vaut mieux s'entretenir avec un employé qui ne serait pas parti (faux positif) que de passer à côté d'un vrai départ (faux négatif). Un seuil de 0,64 maximiserait le F1 (précision 0,58, recall 0,60), mais il laisserait passer davantage de départs.

## 5. Limites connues
- **Précision de 35 %** : sur 3 employés signalés, environ 1 seul part réellement. La prédiction est une **alerte à vérifier**, pas une décision.
- **Corrélation, pas causalité** : le modèle repère des profils à risque, il n'explique pas à lui seul pourquoi un employé part.
- **Données fictives et datées** : le modèle doit être réentraîné sur des données réelles et récentes avant tout usage en production.
- **Catégories fermées** : un nouveau poste ou un nouveau département sera refusé par l'API (erreur 422). Il faut d'abord réentraîner le modèle.

## 6. Garanties (tests automatiques)
- `verifications/unitaires/test_modele.py` vérifie à chaque push que :
  - les probabilités sont valides ;
  - le PR-AUC reste **≥ 0,55** ;
  - l'entraînement est **reproductible** (`random_state=42`) ;
  - le fichier `.joblib` correspond bien au code actuel.
- Les versions des bibliothèques sont fixées dans `requirements.txt` : un modèle sauvegardé ne se recharge qu'avec la même version de scikit-learn.

## 7. Protocole de mise à jour
**Quand réentraîner :**
- tous les 6 mois, avec les nouvelles données RH ;
- immédiatement si un nouveau poste ou département apparaît ;
- si la part de « Oui » dans la table `predictions` s'écarte fortement du taux réel de départ (signe de dérive).

**Comment :**
1. Créer une branche : `git switch -c feature/reentrainement-AAAA-MM`.
2. Mettre à jour les fichiers dans `data/`.
3. Réentraîner : `python -m regression_logistique.entrainer`.
4. Vérifier que le PR-AUC affiché reste au moins égal à 0,55.
5. Incrémenter `VERSION_MODELE` dans `api/main.py` (par exemple `reglog-v2`). Les anciennes prédictions gardent ainsi leur version d'origine en base.
6. Lancer `pytest`, puis ouvrir une pull request. Le robot bloque la fusion si un test échoue.
7. Après la fusion, poser un tag de version.

**Surveillance :** les requêtes de `database_postgresql/requetes.sql` permettent de suivre la répartition des prédictions et de repérer les demandes restées sans réponse.