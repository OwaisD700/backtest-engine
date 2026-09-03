"""
welford.py — numerically stable running mean/variance.

SCOPE (Gate 4 of the prep plan):
    RunningStats, an online (incremental) accumulator for mean and
    variance that avoids the catastrophic cancellation of the naive
    E[X^2] - E[X]^2 formula, by never computing a large intermediate
    sum of squares.

    OUT OF SCOPE: everything else — this file has exactly one job.
"""
import numpy as np

class RunningStats:
    def __init__(self):
        self.n = 0
        self.mean = 0.0
        self.M2 = 0.0


    def update(self, x: float) -> None:
        self.n += 1
        delta = x - self.mean
        self.mean += delta / self.n
        delta2 = x - self.mean
        self.M2 += delta * delta2

    @property
    def variance(self) -> float:
        if (self.n > 1):
            return self.M2 / (self.n - 1)
        else:
            return float("nan")


def naive_variance(values) -> float:
    values = np.asarray(values, dtype=np.float64)
    n = len(values)
    mean_of_squares = np.mean(values ** 2)
    square_of_mean = (np.mean(values)) ** 2
    return (mean_of_squares - square_of_mean) * n / (n - 1)
    


