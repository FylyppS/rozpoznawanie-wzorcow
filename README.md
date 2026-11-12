# Obciążenie i zmienność oceny przez walidację krzyżową

Projekt z przedmiotu **Rozpoznawanie wzorców** (informatyka, studia II stopnia, Politechnika Opolska,
semestr zimowy 2026/27, grupa 2). Temat **06**, obszar: metodologia eksperymentów.

Publikacja: R. Kohavi, *A Study of Cross-Validation and Bootstrap for Accuracy Estimation and Model
Selection*, IJCAI 1995 — <https://ai.stanford.edu/~ronnyk/accEst.pdf>.

## Autorzy

| Imię i nazwisko  | Nr indeksu |
|------------------|-----------:|
| Dariusz Salzburg | 103931     |
| Filip Sejud      | 103928     |

## Pytanie badawcze

Jak liczba części walidacji krzyżowej wpływa na obciążenie i zmienność szacowanego błędu oraz co
zmienia stratyfikacja przy niezbalansowanych klasach?

- **Odtworzenie (adaptacja):** 30 niezależnie wygenerowanych zbiorów treningowych po 200 obiektów
  i jeden duży, niezależny zbiór testowy (10 000 obiektów) z tego samego generatora; CV o 2, 5 i 10
  foldach dla GaussianNB i drzewa CART; mierzona różnica `e_cv − e_test`.
- **Eksperyment własny:** klasa rzadka ≈ 10 %; zwykłe i stratyfikowane 5‑foldowe CV na tych samych
  próbkach.
- Dane i modele autora zastąpiono własnym generatorem i modelami ze scikit‑learn — zmiany względem
  publikacji są wypisane w protokole ([etap1/protokol/protokol.tex](etap1/protokol/protokol.tex)).

## Struktura repozytorium

```
cvbias/            pakiet z kodem badania
  generator.py     generator danych (dwie klasy normalne, znany błąd Bayesa)
  protocol.py      UTRWALONY PROTOKÓŁ: rozmiary, ziarna, liczba powtórzeń, modele, budżet
  experiment.py    przebieg: CV vs duży test, zapis wyników per fold i podsumowań
  analysis.py      obciążenie/zmienność po powtórzeniach, „rachunek ręczny”
run_experiment.py      uruchomienie badania (CLI)
make_figures.py        rysunki do etapu 1 (generator)
make_figures_etap2.py  rysunki z wyników: różnice Δ, metoda vs punkt odniesienia, bias/sd vs k, stratyfikacja
results/pilot/         surowe wyniki małej próby uruchomienia (3 zbiory) z etapu 1
results/etap2/         surowe wyniki etapu 2: pierwsze 10 z 30 niezależnych zbiorów (580 dopasowań)
etap1/                 materiały etapu 1: slajdy, protokół, informacja o AI (wzór 2A), rysunki, formatka
etap2/                 materiały etapu 2: slajdy, notatka z postępów, rysunki
requirements.txt       wersje zależności
```

Każde uruchomienie zapisuje do katalogu wyników: `*_folds.csv` (błąd i skład klas każdego foldu),
`*_summary.csv` (dla każdego zbioru × modelu × wariantu CV: `e_cv`, `e_test`, `diff`) oraz
`meta.json` (wersje bibliotek, ziarna, parametry generatora, liczba dopasowań, czas).

## Uruchomienie

```bash
python3.14 -m venv .venv && . .venv/bin/activate   # fish: . .venv/bin/activate.fish
pip install -r requirements.txt

python run_experiment.py --reps 3 --out results/pilot   # mała próba (etap 1): 174 dopasowania, < 1 s
python run_experiment.py --reps 10 --out results/etap2  # etap 2: pierwsze 10 zbiorów, 580 dopasowań, ~0,5 s
python run_experiment.py --out results/full             # pełna seria: 30 zbiorów (etap 3), 1740 dopasowań
python make_figures.py --out etap1/figures
python make_figures_etap2.py --results results/etap2 --out etap2/figures
```

Ziarna zbiorów zależą tylko od numeru powtórzenia `r`, więc wyniki dla pierwszych 10 zbiorów są
identyczne w `results/etap2` i w pełnej serii. Polecenie `run_experiment.py` wypisuje tabelę
obciążenia i zmienności oraz rachunek ręczny dla zbioru D₁.

## Etapy

| Etap | Termin | Materiały | Status |
|------|--------|-----------|--------|
| 1 — prezentacja tematu | 2026-10-29 | slajdy, protokół ~1 str., informacja 2A, próba uruchomienia | oddany |
| 2 — wstępne wyniki | ? (wstępnie 2026-12-10) | kod, pierwsze wyniki (`results/etap2`), wykres `e_cv − e_test`, notatka 1–2 str., slajdy | w przygotowaniu |
| 3 — raport końcowy | ? (wstępnie 2027-01-14) | raport 6–8 str., slajdy, kod, instrukcja, surowe wyniki | — |

## Wykorzystanie AI

Projekt realizowany na poziomie 2 (AI jako wsparcie pracy) zgodnie z kontraktem przedmiotu.
Informacja według wzoru 2A jest dołączana do materiałów każdego etapu
([etap1/informacja-2a/](etap1/informacja-2a/)).
