import numpy as np
import pytest

from src.backtest.welford import RunningStats, naive_variance

def test_running_stats_known_values():
    rs = RunningStats()
    for x in [2,4,6]:
        rs.update(x)

    assert rs.mean == pytest.approx(4)
    assert rs.variance == pytest.approx(4)

def test_welford_beats_naive_on_large_mean_data():
    np.random.seed(0)
    data = 1e8 + np.random.normal(loc=0, scale=1, size=10_000)
    rs = RunningStats()
    for x in data:
        rs.update(x)

    naive = naive_variance(data)
    true_variance = 1.0

    welford_error = abs(true_variance - rs.variance)
    naive_error = abs(naive - true_variance)
    assert welford_error < 0.1

    assert welford_error < 0.1 * naive_error