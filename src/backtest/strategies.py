# src/backtest/strategies.py
from typing import Protocol
import pandas as pd

class Strategy(Protocol):
    def __call__(self, history: pd.DataFrame) -> float:
        """
        history: OHLCV bars from the start of the sample up to and including
                  day t. Never contains any row after day t.
        returns: position to hold on day t+1. -1.0 short, 0.0 flat, 1.0 long.
        """

def mean_reversion(history: pd.DataFrame) -> float:
    if len(history) < 21:
        return 0.0

    returns = history["Close"].pct_change()
    window = returns.tail(20)
    mu = window.mean()
    sigma = window.std()

    if sigma == 0:
        return 0.0

    z = (returns.iloc[-1] - mu) / sigma

    if z > 1:
        return -1.0
    elif z < -1:
        return 1.0
    else:
        return 0.0
