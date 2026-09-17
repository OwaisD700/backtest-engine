# src/backtest/engine.py
from dataclasses import dataclass
import numpy as np
import pandas as pd

from .strategies import Strategy


@dataclass(frozen=True)
class BacktestResult:
    positions: pd.Series
    asset_returns: pd.Series
    gross_returns: pd.Series
    turnover: pd.Series
    costs: pd.Series
    net_returns: pd.Series
    equity: pd.Series


def run_backtest(
    bars: pd.DataFrame,
    strategy: Strategy,
    cost_bps: float = 0.0,
) -> BacktestResult:
    n = len(bars)

    # step 3: build targets by calling the strategy on a growing slice
    targets = np.full(n, np.nan)
    for i in range(n):
        history = bars.iloc[: i + 1]
        targets[i] = strategy(history)

    # step 4: shift targets into positions actually held
    positions = np.empty(n)
    positions[0] = 0.0
    positions[1:] = targets[:-1]
    # step 5: asset returns
    asset_returns = bars["Close"].pct_change()
    # step 6: gross returns
    positions = pd.Series(positions, index=bars.index)
    gross_returns = positions * asset_returns
    gross_returns = gross_returns.fillna(0.0)






    # commit 1: costs off
    turnover = pd.Series(0.0, index=bars.index)
    turnover = positions.diff().abs().fillna(0.0)
    costs = pd.Series(0.0, index=bars.index)
    costs = turnover * (cost_bps / 10_000)
    net_returns = gross_returns - costs
    # step 7: equity curve
    equity = (1 + net_returns).cumprod()

    return BacktestResult(
        positions= positions,      
        asset_returns= asset_returns,  
        gross_returns = gross_returns,  
        turnover = turnover,
        costs= costs,
        net_returns= net_returns,    
        equity = equity,         
    )