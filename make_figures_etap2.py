#!/usr/bin/env python3
"""Rysunki do etapu 2 (wstępne wyniki) z surowych wyników badania.

    python make_figures_etap2.py --results results/etap2 --out etap2/figures

Powstają:
  diff_strip.png     różnice Δ_r = ê_CV − e_test dla każdego zbioru D_r, k i modelu (wykres z karty tematu)
  cv_vs_test.png     wynik metody (ê_CV dla k = 2, 5, 10) i punktu odniesienia (e_test) dla każdego D_r
  bias_sd_vs_k.png   obciążenie (± błąd standardowy) i zmienność w funkcji k — odpowiednik Rys. 1 i 3 Kohaviego
  own_strip.png      eksperyment własny: Δ_r dla KFold i StratifiedKFold oraz skład klas w foldach
Styl (kolory, osie) jak w make_figures.py.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from cvbias import protocol as P  # noqa: E402
from cvbias.analysis import bias_variance_table, load  # noqa: E402
from make_figures import AXIS, GRID, INK, INK2, MUTED, SURFACE, style  # noqa: E402

MODEL_COLOR = {"gnb": "#2a78d6", "cart": "#eb6834"}
MODEL_NAME = {"gnb": "GaussianNB (stabilny)", "cart": "CART (niestabilny)"}
K_MARKER = {2: "o", 5: "^", 10: "D"}


def pp(v: float) -> str:
    """Liczba w punktach procentowych z przecinkiem dziesiętnym."""
    return f"{100 * v:+.1f}".replace(".", ",")


def fig_diff_strip(summary: pd.DataFrame, out: Path) -> Path:
    """Δ_r dla każdego zbioru: punkty per k, średnia (obciążenie) ± odchylenie standardowe (zmienność)."""
    rng = np.random.default_rng(0)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), dpi=200, sharey=True, gridspec_kw={"wspace": 0.08})
    fig.patch.set_facecolor(SURFACE)
    for ax, model in zip(axes, ("gnb", "cart")):
        style(ax)
        color = MODEL_COLOR[model]
        ax.axhline(0, color=INK2, lw=1.2, zorder=2)
        for i, k in enumerate(P.FOLDS):
            d = summary[(summary.model == model) & (summary.k == k)].sort_values("rep")["diff"].to_numpy()
            x = i + rng.uniform(-0.16, 0.16, size=len(d))
            ax.scatter(x, d, s=42, color=color, alpha=0.55, edgecolors=SURFACE, linewidths=0.8, zorder=3)
            m, s = d.mean(), d.std(ddof=1)
            ax.errorbar(i + 0.34, m, yerr=s, fmt="s", color=INK, ms=7, capsize=4, lw=1.6, zorder=4)
            ax.annotate(f"{pp(m)} ± {100 * s:.1f}".replace(".", ","), xy=(i + 0.34, m + s), xytext=(0, 4),
                        textcoords="offset points", ha="center", va="bottom", fontsize=9.5, color=INK2)
        ax.set_xticks(range(len(P.FOLDS)))
        ax.set_xticklabels([f"k = {k}" for k in P.FOLDS])
        ax.set_xlim(-0.5, len(P.FOLDS) - 0.2)
        ax.set_title(MODEL_NAME[model], loc="left")
    axes[0].set_ylabel("Δᵣ = ê_CV − e_test   (> 0: CV zawyża błąd)")
    axes[0].text(0.01, 0.98, "punkt = jeden zbiór Dᵣ;  ■ = średnia (obciążenie) ± sd (zmienność), w p.p.",
                 transform=axes[0].transAxes, fontsize=9.5, color=MUTED, va="top")
    path = out / "diff_strip.png"
    fig.savefig(path, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return path


def fig_cv_vs_test(summary: pd.DataFrame, out: Path) -> Path:
    """Dla każdego D_r: estymaty CV (k = 2, 5, 10) obok punktu odniesienia e_test."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), dpi=200, gridspec_kw={"wspace": 0.18})
    fig.patch.set_facecolor(SURFACE)
    reps = sorted(summary.rep.unique())
    for ax, model in zip(axes, ("gnb", "cart")):
        style(ax)
        color = MODEL_COLOR[model]
        sub = summary[summary.model == model]
        e_test = sub.drop_duplicates("rep").set_index("rep").loc[reps, "e_test"]
        ax.plot(reps, e_test, color=INK, lw=1.2, zorder=2)
        ax.scatter(reps, e_test, marker="s", s=52, color=INK, zorder=4, label="e_test (model na całym Dᵣ, test 10 000)")
        for k in P.FOLDS:
            e_cv = sub[sub.k == k].set_index("rep").loc[reps, "e_cv"]
            ax.scatter(np.array(reps) + {2: -0.2, 5: 0.0, 10: 0.2}[k], e_cv, marker=K_MARKER[k], s=40, color=color,
                       alpha=0.85, edgecolors=SURFACE, linewidths=0.6, zorder=3, label=f"ê_CV, k = {k}")
        bayes = P.GENERATORS["balanced"].bayes_error()
        ax.axhline(bayes, color=MUTED, lw=1, ls=(0, (3, 3)))
        ax.text(reps[-1] + 0.35, bayes, "błąd Bayesa", color=MUTED, fontsize=9, va="center", ha="right")
        ax.set_xticks(reps)
        ax.set_xticklabels([f"D{r}" for r in reps], fontsize=9.5)
        ax.set_xlabel("niezależny zbiór treningowy (powtórzenie)")
        ax.set_title(MODEL_NAME[model], loc="left")
        ax.legend(frameon=False, fontsize=9, loc="upper left", ncol=2, labelcolor=INK2)
    axes[0].set_ylabel("odsetek pomyłek")
    axes[0].set_ylim(0.08, 0.30)
    axes[1].set_ylim(0.15, 0.45)
    path = out / "cv_vs_test.png"
    fig.savefig(path, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return path


def fig_bias_sd_vs_k(table: pd.DataFrame, out: Path) -> Path:
    """Obciążenie ± błąd standardowy oraz zmienność w funkcji k (odpowiednik Rys. 1 i Rys. 3 Kohaviego)."""
    fig, (ax_b, ax_s) = plt.subplots(1, 2, figsize=(12, 4.3), dpi=200, gridspec_kw={"wspace": 0.22})
    fig.patch.set_facecolor(SURFACE)
    style(ax_b)
    style(ax_s)
    ax_b.axhline(0, color=INK2, lw=1.2)
    for model in ("gnb", "cart"):
        t = table[(table.model == model) & (table.cv_type == "kfold")].sort_values("k")
        color = MODEL_COLOR[model]
        off = -0.15 if model == "gnb" else 0.15
        ax_b.errorbar(t.k + off, t.bias, yerr=t.se_bias, fmt="o-", color=color, ms=7, lw=1.8, capsize=4,
                      label=MODEL_NAME[model])
        ax_s.plot(t.k, t.sd_diff, "o-", color=color, ms=7, lw=1.8, label=MODEL_NAME[model])
    for ax, ylabel, title in ((ax_b, "obciążenie = średnia Δᵣ  (± błąd standardowy)", "Obciążenie estymaty CV w funkcji k"),
                              (ax_s, "zmienność = sd Δᵣ", "Zmienność estymaty CV w funkcji k")):
        ax.set_xticks(list(P.FOLDS))
        ax.set_xlabel("liczba foldów k")
        ax.set_ylabel(ylabel)
        ax.set_title(title, loc="left")
        ax.legend(frameon=False, fontsize=10, labelcolor=INK2)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{100 * v:.1f} p.p.".replace(".", ",").replace("-", "−")))
    ax_s.set_ylim(0, None)
    ax_b.set_ylim(-0.02, 0.05)
    n = int(table.n.iloc[0])
    fig.text(0.5, -0.02, f"Pierwsze {n} z 30 niezależnych zbiorów treningowych; błąd standardowy obciążenia = sd/√{n}.",
             ha="center", fontsize=10, color=MUTED)
    path = out / "bias_sd_vs_k.png"
    fig.savefig(path, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return path


def fig_own(summary: pd.DataFrame, folds: pd.DataFrame, out: Path) -> Path:
    """Eksperyment własny: Δ_r dla zwykłego i stratyfikowanego CV oraz liczba obiektów klasy rzadkiej w foldach."""
    rng = np.random.default_rng(1)
    fig, (ax_d, ax_c) = plt.subplots(1, 2, figsize=(12, 4.4), dpi=200, gridspec_kw={"wspace": 0.2, "width_ratios": [1.25, 1]})
    fig.patch.set_facecolor(SURFACE)
    style(ax_d)
    ax_d.axhline(0, color=INK2, lw=1.2, zorder=2)
    labels = []
    for i, (model, cv_type) in enumerate([(m, c) for m in ("gnb", "cart") for c in ("kfold", "stratified")]):
        d = summary[(summary.model == model) & (summary.cv_type == cv_type)].sort_values("rep")["diff"].to_numpy()
        x = i + rng.uniform(-0.14, 0.14, size=len(d))
        ax_d.scatter(x, d, s=42, color=MODEL_COLOR[model], alpha=0.55, edgecolors=SURFACE, linewidths=0.8, zorder=3)
        m, s = d.mean(), d.std(ddof=1)
        ax_d.errorbar(i + 0.3, m, yerr=s, fmt="s", color=INK, ms=7, capsize=4, lw=1.6, zorder=4)
        ax_d.annotate(f"{pp(m)} ± {100 * s:.1f}".replace(".", ","), xy=(i + 0.3, m + s), xytext=(0, 4),
                      textcoords="offset points", ha="center", va="bottom", fontsize=9.5, color=INK2)
        labels.append(("GNB" if model == "gnb" else "CART") + ("\nKFold" if cv_type == "kfold" else "\nStratified"))
    ax_d.set_xticks(range(4))
    ax_d.set_xticklabels(labels)
    ax_d.set_xlim(-0.5, 3.8)
    ax_d.set_ylabel("Δᵣ = ê_CV − e_test  (5 foldów, klasa rzadka ≈ 10 %)")
    ax_d.set_title("KFold vs StratifiedKFold (5 foldów) na tych samych Dᵣ", loc="left")

    style(ax_c)
    one = folds[folds.model == "gnb"]  # skład foldów nie zależy od modelu (te same podziały)
    for i, cv_type in enumerate(("kfold", "stratified")):
        c = one[one.cv_type == cv_type]["n_test_class1"].to_numpy()
        values, counts = np.unique(c, return_counts=True)
        ax_c.bar(values + (-0.2 if i == 0 else 0.2), counts, width=0.38, color=MODEL_COLOR["gnb"] if i == 0 else "#1baf7a",
                 label="KFold" if i == 0 else "StratifiedKFold")
    ax_c.set_xlabel("obiektów klasy rzadkiej w foldzie testowym")
    ax_c.set_ylabel("liczba foldów (10 zbiorów × 5 foldów)")
    ax_c.set_xticks(range(0, int(one.n_test_class1.max()) + 1))
    ax_c.set_title("Skład klas w foldach", loc="left")
    ax_c.legend(frameon=False, fontsize=10, labelcolor=INK2)
    path = out / "own_strip.png"
    fig.savefig(path, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results", type=Path, default=Path("results/etap2"))
    parser.add_argument("--out", type=Path, default=Path("etap2/figures"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    folds, summary = load(args.results, "reproduction")
    own_folds, own_summary = load(args.results, "own")
    for path in (fig_diff_strip(summary, args.out), fig_cv_vs_test(summary, args.out),
                 fig_bias_sd_vs_k(bias_variance_table(summary), args.out), fig_own(own_summary, own_folds, args.out)):
        print(path)


if __name__ == "__main__":
    main()
