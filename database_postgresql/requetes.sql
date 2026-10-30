-- 1. Traçabilité complète : chaque demande avec sa prédiction
SELECT d.id, d.date_demande, d.age, d.poste,
       p.probabilite_depart, p.va_quitter, p.version_modele
FROM demandes d
JOIN predictions p ON p.demande_id = d.id
ORDER BY d.id;

-- 2. Demandes restées sans prédiction (échec du modèle)
SELECT d.id, d.date_demande
FROM demandes d
LEFT JOIN predictions p ON p.demande_id = d.id
WHERE p.id IS NULL;

-- 3. Nombre de prédictions "Oui" / "Non"
SELECT va_quitter, COUNT(*) AS nombre
FROM predictions
GROUP BY va_quitter;

-- 4. Dataset d'origine : taux de départ réel par département
SELECT departement,
       COUNT(*) AS effectif,
       ROUND(100.0 * SUM(CASE WHEN a_quitte_l_entreprise = 'Oui' THEN 1 ELSE 0 END) / COUNT(*), 1) AS taux_depart_pct
FROM employes
GROUP BY departement;
