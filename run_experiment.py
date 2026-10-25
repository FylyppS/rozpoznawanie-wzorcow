#!/usr/bin/env python3
"""Uruchamia badanie i zapisuje surowe wyniki (CSV + meta.json).

Przykłady:
    python run_experiment.py --reps 3 --out results/pilot      # mała próba uruchomienia (etap 1)
    python run_experiment.py --out results/full                # pełna seria: 30 niezależnych zbiorów
    python run_experiment.py --part reproduction --out results/r
"""

from __future__ import annotations

import argparse
from pathlib import Path

from cvbias import protocol as P
from cvbias.analysis import bias_variance_table, format_table, load, manual_example
from cvbias.experiment import run_all


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reps", type=int, default=P.N_REPS, help=f"liczba niezależnych zbiorów treningowych (domyślnie {P.N_REPS})")
    parser.add_argument("--out", type=Path, default=Path("results/full"), help="katalog na surowe wyniki")
    parser.add_argument("--part", choices=["all", "reproduction", "own"], default="all",
                        help="odtworzenie (k = 2/5/10), eksperyment własny (stratyfikacja) albo oba")
    args = parser.parse_args()

    parts = ("reproduction", "own") if args.part == "all" else (args.part,)
    meta = run_all(args.out, args.reps, parts)
    print(f"Dopasowań: {meta['fits_performed']}  (budżet {P.FIT_BUDGET}, pełna seria: "
          f"{meta['fits_planned_full_series']['total']})  czas: {meta['elapsed_seconds']} s  →  {args.out}")

    for part in parts:
        folds, summary = load(args.out, part)
        print(f"\n== {part}: obciążenie (bias) i zmienność (sd_diff) różnicy e_cv − e_test")
        print(format_table(bias_variance_table(summary)))

    if "reproduction" in parts:
        folds, summary = load(args.out, "reproduction")
        print("\n== Rachunek ręczny: średnia błędów foldów (zbiór D_1, GaussianNB, k = 5)")
        print(manual_example(folds, summary))


if __name__ == "__main__":
    main()
