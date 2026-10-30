# Schéma de la base de données `attrition`

```mermaid
erDiagram
    EMPLOYES {
        int id PK
        int age
        string poste
        string departement
        string a_quitte_l_entreprise
        string autres_colonnes "24 autres colonnes"
    }
    DEMANDES {
        int id PK
        datetime date_demande
        int age
        string poste
        string autres_colonnes "25 autres colonnes"
    }
    PREDICTIONS {
        int id PK
        int demande_id FK "unique"
        float probabilite_depart
        string va_quitter
        string version_modele
        datetime date_prediction
    }
    DEMANDES ||--|| PREDICTIONS : "produit"
```

- **employes** : le dataset d'origine (1 470 lignes), inséré par `create_db.py`.
- **demandes** : les inputs envoyés à l'API, enregistrés **avant** l'appel au modèle.
- **predictions** : les outputs du modèle, reliés à leur demande par la clé étrangère `demande_id`.