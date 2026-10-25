#!/usr/bin/env python3
"""Rysunki do slajdów i raportu.

    python make_figures.py --out etap1/figures

Kolory i proporcje znaczników wg jednej, sprawdzonej palety (klasa 0 — niebieski,
klasa 1 — pomarańczowy; siatka i osie recesywne, tekst w odcieniach szarości).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy.stats import norm  # noqa: E402

from cvbias import protocol as P  # noqa: E402
from cvbias.generator import generate  # noqa: E402

INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURFACE = "#e1e0d9", "#c3c2b7", "#ffffff"
CLASS0, CLASS1 = "#2a78d6", "#eb6834"

plt.rcParams.update({
    "font.family": "Liberation Sans",
    "font.size": 12,
    "axes.titlesize": 14,
    "axes.labelcolor": INK2,
    "text.color": INK,
})


def style(ax) -> None:
    """Recesywne osie i siatka: hairline, bez znaczników osi."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelsize=11, length=0)
    ax.grid(True, color=GRID, linewidth=1)
    ax.set_axisbelow(True)
    ax.set_facecolor(SURFACE)


def fig_generator(out: Path) -> Path:
    """Generator danych: próbka D_1 na dwóch cechach oraz gęstości rzutu z = u^T x z progiem Bayesa."""
    cfg = P.GENERATORS["balanced"]
    cfg_imb = P.GENERATORS["imbalanced"]
    X, y = generate(cfg, P.N_TRAIN, P.SEEDS["balanced"]["train"] + 1)   # ten sam zbiór co w przykładzie ręcznym

    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(12, 4.2), dpi=200,
                                     gridspec_kw={"width_ratios": [1, 1.3], "wspace": 0.18})
    fig.patch.set_facecolor(SURFACE)

    # Lewy panel: rozrzut na dwóch pierwszych cechach informacyjnych.
    style(ax_l)
    for label, color, name in ((0, CLASS0, "klasa 0"), (1, CLASS1, "klasa 1")):
        mask = y == label
        ax_l.scatter(X[mask, 0], X[mask, 1], s=34, color=color, edgecolors=SURFACE, linewidths=1.2,
                     label=f"{name} (n = {mask.sum()})")
    ax_l.set_xlabel("x₁")
    ax_l.set_ylabel("x₂")
    ax_l.set_title("Próbka D₁ (n = 200) na cechach x₁, x₂", loc="left")
    ax_l.legend(frameon=False, loc="upper left", fontsize=10.5, labelcolor=INK2)
    ax_l.set_aspect("equal")

    # Prawy panel: gęstości klas na kierunku u i obszary błędu Bayesa.
    style(ax_r)
    d = cfg.delta
    z = np.linspace(-4.5, 4.5, 800)
    pdf0, pdf1 = norm.pdf(z, -d / 2), norm.pdf(z, d / 2)
    t0, t1 = cfg.bayes_threshold(), cfg_imb.bayes_threshold()
    ax_r.plot(z, pdf0, color=CLASS0, lw=2, solid_capstyle="round", label="z | y = 0  ~  N(−δ/2, 1)")
    ax_r.plot(z, pdf1, color=CLASS1, lw=2, solid_capstyle="round", label="z | y = 1  ~  N(+δ/2, 1)")
    ax_r.fill_between(z, 0, pdf0, where=z > t0, color=CLASS0, alpha=0.15, lw=0)
    ax_r.fill_between(z, 0, pdf1, where=z < t0, color=CLASS1, alpha=0.15, lw=0)
    ax_r.axvline(t0, color=INK2, lw=1.4)
    ax_r.axvline(t1, color=MUTED, lw=1.4, ls=(0, (2, 2)))
    # Opisy progów w pustej strefie nad krzywymi, z cienkimi odnośnikami do linii progów.
    leader = {"arrowstyle": "-", "color": INK2, "lw": 0.8, "shrinkA": 2, "shrinkB": 2}
    ax_r.annotate("t = 0 (π₁ = 0,5)\nbłąd Bayesa Φ(−δ/2) = 15,9 %", xy=(t0, 0.50), xytext=(1.75, 0.585),
                  color=INK2, fontsize=10.5, va="top", arrowprops=leader)
    t1_txt = f"{t1:.2f}".replace(".", ",")
    ax_r.annotate(f"t = ln 9/δ ≈ {t1_txt} (π₁ = 0,1)\nbłąd Bayesa 7,0 %", xy=(t1, 0.445), xytext=(1.75, 0.48),
                  color=MUTED, fontsize=10.5, va="top", arrowprops={**leader, "color": MUTED})
    ax_r.set_xlabel("z = uᵀx   (odległość Mahalanobisa średnich: δ = 2)")
    ax_r.set_yticks([])
    ax_r.set_xlim(-4.5, 4.9)
    ax_r.set_ylim(0, 0.6)
    ax_r.set_title("Rzut na kierunek rozdzielający u: gęstości klas i próg Bayesa", loc="left")
    ax_r.legend(frameon=False, loc="upper left", fontsize=10.5, labelcolor=INK2)

    path = out / "generator.png"
    fig.savefig(path, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("etap1/figures"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    print(fig_generator(args.out))


if __name__ == "__main__":
    main()
