"""Generator danych syntetycznych do badania obciążenia i zmienności CV.

Dwie klasy o rozkładach normalnych z jednostkową macierzą kowariancji:

    X | y ~ N(mu_y, I_d),    mu_1 = +delta/2 * u,    mu_0 = -delta/2 * u,

gdzie u jest wektorem jednostkowym rozpiętym na pierwszych ``n_informative``
cechach (pozostałe cechy to czysty szum N(0, 1)). Odległość Mahalanobisa
między średnimi klas wynosi dokładnie ``delta``, więc błąd Bayesa — najmniejszy
osiągalny błąd prawdziwy — jest znany analitycznie i służy jako punkt
odniesienia dla błędów mierzonych na dużym zbiorze testowym.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import norm


@dataclass(frozen=True)
class GeneratorConfig:
    n_features: int = 10      # d — liczba cech
    n_informative: int = 5    # liczba cech, wzdłuż których klasy się różnią
    delta: float = 2.0        # odległość Mahalanobisa między średnimi klas
    prior_1: float = 0.5      # P(y = 1); 0.5 = klasy zbalansowane, 0.1 = klasa rzadka

    @property
    def direction(self) -> np.ndarray:
        """Wektor jednostkowy u wyznaczający kierunek rozdzielający klasy."""
        u = np.zeros(self.n_features)
        u[: self.n_informative] = 1.0 / np.sqrt(self.n_informative)
        return u

    def class_mean(self, label: int) -> np.ndarray:
        """Średnia mu_y rozkładu klasy ``label``."""
        sign = 1.0 if label == 1 else -1.0
        return sign * (self.delta / 2.0) * self.direction

    def bayes_threshold(self) -> float:
        """Próg t na rzucie z = u^T x: reguła Bayesa wybiera klasę 1, gdy z > t.

        Z porównania pi_1 * phi(z - delta/2) > pi_0 * phi(z + delta/2) wynika
        t = ln(pi_0 / pi_1) / delta (dla pi_0 = pi_1 próg t = 0).
        """
        prior_0 = 1.0 - self.prior_1
        return float(np.log(prior_0 / self.prior_1) / self.delta)

    def bayes_error(self) -> float:
        """Błąd klasyfikatora Bayesa e* = pi_0 P(z > t | y=0) + pi_1 P(z < t | y=1)."""
        t = self.bayes_threshold()
        prior_0 = 1.0 - self.prior_1
        err_0 = 1.0 - norm.cdf(t + self.delta / 2.0)   # z | y=0 ~ N(-delta/2, 1)
        err_1 = norm.cdf(t - self.delta / 2.0)         # z | y=1 ~ N(+delta/2, 1)
        return float(prior_0 * err_0 + self.prior_1 * err_1)

    def bayes_recall_1(self) -> float:
        """Czułość klasy 1 (rzadkiej) klasyfikatora Bayesa: P(z > t | y=1)."""
        return float(1.0 - norm.cdf(self.bayes_threshold() - self.delta / 2.0))


def generate(cfg: GeneratorConfig, n: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Losuje n obiektów: y ~ Bernoulli(prior_1), potem X = mu_y + eps, eps ~ N(0, I_d).

    Ten sam ``seed`` daje zawsze ten sam zbiór — to utrwala losowania protokołu.
    """
    rng = np.random.default_rng(seed)
    y = (rng.random(n) < cfg.prior_1).astype(int)
    noise = rng.standard_normal((n, cfg.n_features))
    means = np.where(y[:, None] == 1, cfg.class_mean(1), cfg.class_mean(0))
    return means + noise, y
