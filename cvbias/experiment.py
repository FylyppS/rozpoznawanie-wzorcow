"""Przebieg badania: estymata CV kontra błąd na dużym teście, zapis surowych wyników.

Jednostką powtórzenia jest niezależny zbiór treningowy D_r. Dla każdego D_r
i modelu liczymy:

* e_test — błąd modelu dopasowanego na całym D_r i ocenionego na dużym,
  niezależnym zbiorze testowym T (ocena referencyjna),
* e_cv — średnią błędów foldów k-krotnej walidacji krzyżowej na D_r,
* diff = e_cv - e_test — różnicę, której średnia po r szacuje obciążenie,
  a odchylenie standardowe zmienność estymatora.

Te same podziały na foldy są używane dla obu modeli (jak u Kohaviego), a przy
porównaniu zwykłego i stratyfikowanego CV — ten sam zbiór D_r.
"""

from __future__ import annotations

import csv
import json
import platform
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np
import scipy
import sklearn
from sklearn.model_selection import KFold, StratifiedKFold

from . import protocol as P
from .generator import generate

# Licznik dopasowań — kontrola budżetu obliczeniowego z karty tematu.
FIT_COUNTER = {"fits": 0}

FOLD_COLUMNS = [
    "scenario", "rep", "model", "cv_type", "k", "fold",
    "n_train", "n_test", "n_train_class1", "n_test_class1",
    "missing_class_train", "missing_class_test",
    "n_errors", "error", "recall_1",
]
SUMMARY_COLUMNS = [
    "scenario", "rep", "model", "cv_type", "k",
    "n_class1_in_train_set", "e_cv", "e_cv_pooled", "e_test", "diff",
    "recall_1_cv", "recall_1_test", "folds_missing_class_test", "folds_missing_class_train",
]


def fit_and_predict(model_name: str, X_train, y_train, X_eval) -> np.ndarray:
    """Dopasowuje świeży model na (X_train, y_train) i zwraca predykcje dla X_eval."""
    model = P.make_model(model_name)
    model.fit(X_train, y_train)
    FIT_COUNTER["fits"] += 1
    return model.predict(X_eval)


def error_rate(y_true, y_pred) -> float:
    """Odsetek pomyłek (strata 0/1)."""
    return float(np.mean(y_pred != y_true))


def recall_class1(y_true, y_pred) -> float:
    """Czułość klasy 1; NaN, gdy w zbiorze oceny nie ma ani jednego obiektu klasy 1."""
    positives = y_true == 1
    if not positives.any():
        return float("nan")
    return float(np.mean(y_pred[positives] == 1))


def make_splitter(cv_type: str, k: int, seed: int):
    """Podział na k foldów: zwykły (KFold) albo stratyfikowany (StratifiedKFold)."""
    if cv_type == "kfold":
        return KFold(n_splits=k, shuffle=True, random_state=seed)
    if cv_type == "stratified":
        return StratifiedKFold(n_splits=k, shuffle=True, random_state=seed)
    raise ValueError(f"nieznany typ CV: {cv_type!r}")


def cross_validate(model_name: str, X, y, splitter) -> list[dict]:
    """k-krotna walidacja krzyżowa; zwraca wiersz z błędem i składem klas dla każdego foldu."""
    rows = []
    for j, (train_idx, test_idx) in enumerate(splitter.split(X, y), start=1):
        y_pred = fit_and_predict(model_name, X[train_idx], y[train_idx], X[test_idx])
        y_true = y[test_idx]
        rows.append({
            "fold": j,
            "n_train": len(train_idx),
            "n_test": len(test_idx),
            "n_train_class1": int(y[train_idx].sum()),
            "n_test_class1": int(y_true.sum()),
            "missing_class_train": int(len(np.unique(y[train_idx])) < 2),
            "missing_class_test": int(len(np.unique(y_true)) < 2),
            "n_errors": int(np.sum(y_pred != y_true)),
            "error": error_rate(y_true, y_pred),
            "recall_1": recall_class1(y_true, y_pred),
        })
    return rows


def run_series(scenario: str, folds, cv_types, n_reps: int) -> tuple[list[dict], list[dict]]:
    """Seria badania dla jednego scenariusza danych.

    Zwraca (wiersze per fold, wiersze podsumowujące per zbiór × model × wariant CV).
    """
    cfg = P.GENERATORS[scenario]
    seeds = P.SEEDS[scenario]
    X_test, y_test = generate(cfg, P.N_TEST, seeds["test"])   # duży test — tylko do oceny
    fold_rows, summary_rows = [], []

    for r in range(1, n_reps + 1):
        X, y = generate(cfg, P.N_TRAIN, seeds["train"] + r)
        for model_name in P.MODELS:
            # Ocena referencyjna: model na całym D_r, błąd na dużym teście T.
            y_pred_test = fit_and_predict(model_name, X, y, X_test)
            e_test = error_rate(y_test, y_pred_test)
            recall_test = recall_class1(y_test, y_pred_test)

            for k in folds:
                for cv_type in cv_types:
                    # Ten sam seed podziału dla obu modeli i obu wariantów CV → te same próbki.
                    splitter = make_splitter(cv_type, k, seeds["split"] + r)
                    rows = cross_validate(model_name, X, y, splitter)
                    errors = np.array([row["error"] for row in rows])
                    e_cv = float(errors.mean())                                  # średnia błędów foldów
                    e_cv_pooled = sum(row["n_errors"] for row in rows) / len(y)  # pomyłki / n (wzór Kohaviego)
                    recalls = np.array([row["recall_1"] for row in rows])

                    base = {"scenario": scenario, "rep": r, "model": model_name,
                            "cv_type": cv_type, "k": k}
                    fold_rows.extend({**base, **row} for row in rows)
                    summary_rows.append({
                        **base,
                        "n_class1_in_train_set": int(y.sum()),
                        "e_cv": e_cv,
                        "e_cv_pooled": float(e_cv_pooled),
                        "e_test": e_test,
                        "diff": e_cv - e_test,
                        "recall_1_cv": float(np.nanmean(recalls)) if not np.all(np.isnan(recalls)) else float("nan"),
                        "recall_1_test": recall_test,
                        "folds_missing_class_test": int(sum(row["missing_class_test"] for row in rows)),
                        "folds_missing_class_train": int(sum(row["missing_class_train"] for row in rows)),
                    })
    return fold_rows, summary_rows


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_meta(n_reps: int, parts: list[str], elapsed_s: float) -> dict:
    """Metadane uruchomienia: wersje, protokół, liczba dopasowań, czas."""
    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "elapsed_seconds": round(elapsed_s, 2),
        "fits_performed": FIT_COUNTER["fits"],
        "fits_planned_full_series": P.planned_fits(),
        "n_reps": n_reps,
        "parts": parts,
        "protocol": {
            "n_train": P.N_TRAIN, "n_test": P.N_TEST, "n_reps_full": P.N_REPS,
            "folds": list(P.FOLDS), "folds_own": P.FOLDS_OWN,
            "seeds": P.SEEDS,
            "generators": {name: asdict(cfg) for name, cfg in P.GENERATORS.items()},
            "bayes_error": {name: cfg.bayes_error() for name, cfg in P.GENERATORS.items()},
            "models": {name: repr(P.make_model(name)) for name in P.MODELS},
        },
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "scikit-learn": sklearn.__version__,
            "platform": platform.platform(),
        },
    }


def run_all(out_dir: Path, n_reps: int, parts: tuple[str, ...] = ("reproduction", "own")) -> dict:
    """Uruchamia wskazane części badania i zapisuje surowe wyniki do ``out_dir``."""
    out_dir.mkdir(parents=True, exist_ok=True)
    FIT_COUNTER["fits"] = 0
    started = time.perf_counter()

    if "reproduction" in parts:
        folds, summary = run_series("balanced", P.FOLDS, ("kfold",), n_reps)
        write_csv(out_dir / "reproduction_folds.csv", folds, FOLD_COLUMNS)
        write_csv(out_dir / "reproduction_summary.csv", summary, SUMMARY_COLUMNS)
    if "own" in parts:
        folds, summary = run_series("imbalanced", (P.FOLDS_OWN,), ("kfold", "stratified"), n_reps)
        write_csv(out_dir / "own_folds.csv", folds, FOLD_COLUMNS)
        write_csv(out_dir / "own_summary.csv", summary, SUMMARY_COLUMNS)

    meta = run_meta(n_reps, list(parts), time.perf_counter() - started)
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return meta
