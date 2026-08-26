import numpy as np
import pandas as pd
import pytest

from src.backtest.stats import (
    log_returns,
    annualised_return,
    annualised_vol,
    sharpe,
    max_drawdown,
    bootstrap_sharpe_ci
)

def test_annualised_vol_and_sharpe_on_constant_series():
    constant = pd.Series([0.001] * 252)
    assert annualised_vol(constant) == pytest.approx(0, abs=1e-10)
    assert np.isnan(sharpe(constant))


def test_log_returns_known_values():
    prices = pd.Series([100, 110, 99])
    result = log_returns(prices)
    assert len(result) == 2
    assert result.iloc[0] == pytest.approx(np.log(110/100), abs = 1e-10)
    assert result.iloc[1] == pytest.approx(np.log(99/110), abs = 1e-10)

def test_max_drawdown_known_value():
    equity_example = pd.Series([1.00, 1.10, 1.05, 0.90, 1.20, 1.15])
    returns = np.log(equity_example / equity_example.shift(1)).dropna()

    # TODO: assert max_drawdown(returns) approx -0.1818, abs tolerance ~1e-3
    assert max_drawdown(returns) == pytest.approx(-0.1818, abs = 1e-3)

def test_annualised_return_known_value():
    prices = pd.Series([100, 110, 99])
    returns = log_returns(prices)

    expected = returns.mean() * 252
    # TODO: assert annualised_return(returns) approx expected
    assert annualised_return(returns) == pytest.approx(expected, abs = 1e-10)

def test_bootstrap_sharpe_ci_on_strong_positive_series():
    # small daily returns, consistently positive, tiny noise
    strong = pd.Series(np.random.normal(loc=0.001, scale=0.0001, size=252))

    lower, upper = bootstrap_sharpe_ci(strong, n_boot=1000)

    assert lower <= upper
    # TODO: assert the interval doesn't contain zero
    assert (lower > 0) or (upper < 0)