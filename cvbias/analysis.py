"""Podsumowania surowych wyników: obciążenie, zmienność i „rachunek ręczny”."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import protocol as P


def load(results_dir: Path, part: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Wczytuje wiersze per fold i podsumowanie dla części ``part`` (reproduction / own)."""
    folds = pd.read_csv(results_dir / f"{part}_folds.csv")
    summary = pd.read_csv(results_dir / f"{part}_summary.csv")
    return folds, summary


def bias_variance_table(summary: pd.DataFrame) -> pd.DataFrame:
    """Obciążenie i zmienność estymatora CV dla każdej kombinacji model × wariant CV × k.

    bias     = średnia po zbiorach D_r różnicy e_cv - e_test,
    sd_diff  = odchylenie standardowe tej różnicy (zmienność),
    se_bias  = błąd standardowy średniej (sd_diff / sqrt(n)).
    """
    grouped = summary.groupby(["scenario", "model", "cv_type", "k"])
    table = grouped.agg(
        n=("rep", "count"),
        bias=("diff", "mean"),
        sd_diff=("diff", "std"),
        mean_e_cv=("e_cv", "mean"),
        sd_e_cv=("e_cv", "std"),
        mean_e_test=("e_test", "mean"),
        sd_e_test=("e_test", "std"),
        folds_missing_class_test=("folds_missing_class_test", "sum"),
    ).reset_index()
    table["se_bias"] = table["sd_diff"] / np.sqrt(table["n"])
    return table


def format_table(table: pd.DataFrame) -> str:
    return table.to_string(index=False, float_format=lambda v: f"{v:.4f}")


def manual_example(folds: pd.DataFrame, summary: pd.DataFrame, rep: int = 1,
                   model: str = "gnb", k: int = 5, cv_type: str = "kfold") -> str:
    """Rachunek ręczny: błędy foldów → ich średnia ê_CV → porównanie z e_test."""
    mask = (folds.rep == rep) & (folds.model == model) & (folds.k == k) & (folds.cv_type == cv_type)
    rows = folds[mask].sort_values("fold")
    smask = (summary.rep == rep) & (summary.model == model) & (summary.k == k) & (summary.cv_type == cv_type)
    s = summary[smask].iloc[0]

    lines = [f"Zbiór D_{rep} (n = {P.N_TRAIN}), model {P.MODEL_LABELS[model]}, {cv_type}, k = {k}:"]
    for _, row in rows.iterrows():
        lines.append(f"  fold {int(row.fold)}: {int(row.n_errors):3d} pomyłek / {int(row.n_test)} obiektów"
                     f"  →  e_{int(row.fold)} = {row.error:.4f}")
    terms = " + ".join(f"{e:.4f}" for e in rows["error"])
    lines.append(f"  ê_CV = ({terms}) / {k} = {s.e_cv:.4f}")
    lines.append(f"  e_test (model na całym D_{rep}, test N = {P.N_TEST}) = {s.e_test:.4f}")
    lines.append(f"  ê_CV − e_test = {s['diff']:+.4f}")
    return "\n".join(lines)
