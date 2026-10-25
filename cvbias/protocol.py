"""Utrwalony protokół badania — wszystkie stałe eksperymentu w jednym miejscu.

Etap 1 ustala generator, liczbę powtórzeń, ziarna losowań i niezależną ocenę
referencyjną. Każda późniejsza zmiana wartości w tym pliku jest zmianą
protokołu i musi zostać odnotowana w raporcie.
"""

from __future__ import annotations

from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier

from .generator import GeneratorConfig

N_TRAIN = 200        # rozmiar pojedynczego zbioru treningowego D_r
N_TEST = 10_000      # rozmiar dużego, niezależnego zbioru testowego T
N_REPS = 30          # liczba niezależnych zbiorów treningowych = jednostka powtórzenia
FOLDS = (2, 5, 10)   # liczby części CV w odtworzeniu
FOLDS_OWN = 5        # eksperyment własny: zwykłe vs stratyfikowane 5-foldowe CV
FIT_BUDGET = 2500    # budżet obliczeniowy z karty tematu (liczba dopasowań)

# Ziarna generatora liczb losowych. Zbiór treningowy r (r = 1..N_REPS) powstaje
# z ziarna train + r, podział na foldy dla zbioru r z ziarna split + r, a zbiór
# testowy z własnego ziarna — niezależnego od wszystkich zbiorów treningowych.
SEEDS = {
    "balanced": {"train": 1000, "split": 2000, "test": 90001},
    "imbalanced": {"train": 3000, "split": 4000, "test": 90002},
}

# Dwa scenariusze danych: odtworzenie (klasy 50/50) i eksperyment własny (klasa rzadka 10%).
GENERATORS = {
    "balanced": GeneratorConfig(n_features=10, n_informative=5, delta=2.0, prior_1=0.5),
    "imbalanced": GeneratorConfig(n_features=10, n_informative=5, delta=2.0, prior_1=0.1),
}

MODELS = ("gnb", "cart")
MODEL_LABELS = {"gnb": "GaussianNB", "cart": "CART (DecisionTreeClassifier)"}


def make_model(name: str):
    """Zwraca nową, niedopasowaną instancję modelu — jedno wywołanie = jedno dopasowanie."""
    if name == "gnb":
        return GaussianNB()
    if name == "cart":
        # CART bez przycinania (domyślne parametry sklearn); random_state tylko
        # rozstrzyga remisy między cechami, żeby przebieg był odtwarzalny.
        return DecisionTreeClassifier(random_state=0)
    raise ValueError(f"nieznany model: {name!r}")


def planned_fits(n_reps: int = N_REPS) -> dict[str, int]:
    """Planowana liczba dopasowań w każdej części badania (kontrola budżetu)."""
    n_models = len(MODELS)
    reproduction = n_reps * n_models * (sum(FOLDS) + 1)        # foldy + model referencyjny
    own = n_reps * n_models * (2 * FOLDS_OWN + 1)              # zwykłe + stratyfikowane + referencja
    size_reference = n_reps * n_models * len(FOLDS)            # etap 3: model na n(k-1)/k obiektach
    return {
        "reproduction": reproduction,
        "own_experiment": own,
        "train_size_reference": size_reference,
        "total": reproduction + own + size_reference,
        "budget": FIT_BUDGET,
    }
