import joblib
import numpy as np
import pytest
from sklearn.metrics import average_precision_score

from api.preparation import charger_dataset, preparer_donnees
from regression_logistique.entrainer import CHEMIN_MODELE, construire_pipeline, separer


@pytest.fixture(scope="module")
def jeux():
    """Le vrai dataset, séparé exactement comme à l'entraînement."""
    return separer(preparer_donnees(charger_dataset()))


@pytest.fixture(scope="module")
def modele():
    return joblib.load(CHEMIN_MODELE)


def test_probabilites_valides(modele, jeux):
    _, X_test, _, _ = jeux
    proba = modele.predict_proba(X_test)
    assert proba.shape == (len(X_test), 2)
    assert np.all((proba >= 0) & (proba <= 1))
    assert np.allclose(proba.sum(axis=1), 1)


def test_performance_minimale(modele, jeux):
    _, X_test, _, y_test = jeux
    pr_auc = average_precision_score(y_test, modele.predict_proba(X_test)[:, 1])
    # Mesuré : 0.638. Un modèle au hasard obtiendrait environ le taux de départ (~0.16).
    assert pr_auc >= 0.55
    assert pr_auc > 2 * y_test.mean()


def test_entrainement_reproductible(jeux):
    X_train, X_test, y_train, _ = jeux
    p1 = construire_pipeline().fit(X_train, y_train).predict_proba(X_test)
    p2 = construire_pipeline().fit(X_train, y_train).predict_proba(X_test)
    np.testing.assert_array_equal(p1, p2)


def test_modele_sauvegarde_conforme_au_code(modele, jeux):
    X_train, X_test, y_train, _ = jeux
    reentraine = construire_pipeline().fit(X_train, y_train)
    np.testing.assert_allclose(modele.predict_proba(X_test), reentraine.predict_proba(X_test))