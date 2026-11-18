-- 1- Traçabilité complète = chaque demande + sa prédiction
SELECT d.id, d.date_demande, d.age, d.poste,
       p.probabilite_depart, p.va_quitter, p.version_modele
FROM demandes d
JOIN predictions p ON p.demande_id = d.id
ORDER BY d.id;

-- 2- Demandes restées sans prédiction (où échec du modèle)
SELECT d.id, d.date_demande
FROM demandes d
LEFT JOIN predictions p ON p.demande_id = d.id
WHERE p.id IS NULL;

-- 3- Nombre de prédictions de "Oui" et de "Non"
SELECT va_quitter, COUNT(*) AS nombre
FROM predictions
GROUP BY va_quitter;

-- 4- Dataset d'origine : taux de départ réel par département
SELECT departement,
       COUNT(*) AS effectif,
       ROUND(100.0 * SUM(CASE WHEN a_quitte_l_entreprise = 'Oui' THEN 1 ELSE 0 END) / COUNT(*), 1) AS taux_depart_pct
FROM employes
GROUP BY departement;

-- 5. Test d'insertion : on ajoute un faux employé (repérable grâce au poste 'TEST_INSERTION')
INSERT INTO employes (
    a_quitte_l_entreprise, satisfaction_employee_environnement, note_evaluation_precedente,
    niveau_hierarchique_poste, satisfaction_employee_nature_travail, satisfaction_employee_equipe,
    satisfaction_employee_equilibre_pro_perso, note_evaluation_actuelle, heure_supplementaires,
    augementation_salaire_precedente, age, genre, revenu_mensuel, statut_marital, departement,
    poste, nombre_experiences_precedentes, annee_experience_totale, annees_dans_l_entreprise,
    annees_dans_le_poste_actuel, nombre_participation_pee, nb_formations_suivies,
    distance_domicile_travail, niveau_education, domaine_etude, frequence_deplacement,
    annees_depuis_la_derniere_promotion, annes_sous_responsable_actuel
) VALUES (
    'Non', 3, 3,
    2, 3, 3,
    3, 3, 'Non',
    12, 35, 'F', 4000, 'Célibataire', 'Commercial',
    'TEST_INSERTION', 2, 10, 5,
    3, 1, 2,
    10, 3, 'Marketing', 'Occasionnel',
    1, 3
);

-- Vérification : le faux employé doit apparaître (1 ligne)
SELECT id, age, poste FROM employes WHERE poste = 'TEST_INSERTION';

-- 6. Test de suppression : on supprime le faux employé
DELETE FROM employes WHERE poste = 'TEST_INSERTION';

-- Vérification : il ne doit plus exister (résultat = 0)
SELECT COUNT(*) FROM employes WHERE poste = 'TEST_INSERTION';
