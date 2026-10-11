"""
stats.py — performance statistics for the backtest engine.

SCOPE (Gate 3 of the prep plan):
    Functions that turn a series of returns into performance metrics:
    annualised_return, annualised_vol, sharpe, max_drawdown, hit_rate,
    bootstrap_sharpe_ci.

    These functions consume LOG returns (see log_returns() below), not
    simple returns, because log returns sum across time — that's what
    makes the annualisation formulas (×252 for return, ×√252 for vol)
    correct in the first place.

    OUT OF SCOPE: loading data (-> data.py), numerically stable
    variance (-> welford.py), any trading/signal logic (-> engine.py).
"""

import numpy as np
import pandas as pd

PERIODS_PER_YEAR = 252


def log_returns(prices: pd.Series) -> pd.Series:
    """Daily log returns from a price series. Drops the first NaN."""
    return np.log(prices / prices.shift(1)).dropna()

def annualised_return(returns: pd.Series, periods_per_year: int = PERIODS_PER_YEAR) -> float:
    return returns.mean() * periods_per_year

def annualised_vol(returns: pd.Series, periods_per_year: int = PERIODS_PER_YEAR) -> float:
    return returns.std() * np.sqrt(periods_per_year)

def sharpe(returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = PERIODS_PER_YEAR) -> float:
    vol = annualised_vol(returns, periods_per_year)
    if (vol < 1e-12):
        return np.nan
    excess = (annualised_return(returns, periods_per_year) - risk_free_rate)
    return excess / vol

def max_drawdown(returns: pd.Series) -> float:
    equity = np.exp(returns.cumsum())
    running_max = equity.cummax()
    drawdown = equity / running_max - 1
    return drawdown.min()

def hit_rate(returns: pd.Series) -> float:
    """Fraction of active days (non-zero return) that were positive."""
    active = returns[returns != 0]
    if len(active) == 0:
        return np.nan
    return (active > 0).mean()

def bootstrap_sharpe_ci(
    returns: pd.Series,
    n_boot: int = 10_000,
    ci: float = 0.90,
    risk_free_rate: float = 0.0,
    periods_per_year: int = PERIODS_PER_YEAR,
) -> tuple[float, float]:
    boot_sharpes = []
    for _ in range(n_boot):
        sample = returns.sample(n=len(returns), replace=True)
        boot_sharpes.append(sharpe(sample, risk_free_rate, periods_per_year))
   

    lower = np.percentile(boot_sharpes, (1 - ci) / 2 * 100)
    upper = np.percentile(boot_sharpes, (1 + ci) / 2 * 100)
    return lower, upper
