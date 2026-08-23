"""
stats.py — performance statistics for the backtest engine.

SCOPE (Gate 3 of the prep plan):
    Functions that turn a series of returns into performance metrics:
    annualised_return, annualised_vol, sharpe, max_drawdown, hit_rate,
    turnover, bootstrap_sharpe_ci.

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