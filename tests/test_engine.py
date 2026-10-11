# tests/test_engine.py
import pandas as pd
import numpy as np
import pytest
from src.backtest.engine import run_backtest
from src.backtest.stats import sharpe


def test_strategy_never_sees_the_future():
    dates = pd.date_range("2020-01-01", periods=10, freq="D")
    bars = pd.DataFrame({"Close": [100]*10}, index=dates)

    seen_last_dates = []

    def recorder(history: pd.DataFrame) -> float:
        # TODO: record the last date in `history` into seen_last_dates
        seen_last_dates.append(history.index[-1])
        return 0.0

    run_backtest(bars, recorder)

    # TODO: assert recorder was called once per row
    assert len(seen_last_dates) == len(bars)
    # TODO: assert seen_last_dates equals bars.index exactly, in order
    assert seen_last_dates == list(bars.index)

def test_oracle_strategy_produces_impossible_results():
    dates = pd.date_range("2020-01-01", periods=100, freq="D")
    rng = np.random.default_rng(0)
    prices = rng.normal(loc=0, scale=1, size=100).cumsum() + 1000
    bars = pd.DataFrame({"Close" : prices}, index=dates)

    future_return = bars["Close"].pct_change().shift(-1)

    def oracle(history: pd.DataFrame) -> float:
        today = history.index[-1]
        return np.sign(future_return.loc[today])

    result = run_backtest(bars, oracle, cost_bps=0.0)
    assert sharpe(result.net_returns) > 5.0


def test_alignment_on_hand_computed_series():
    dates = pd.date_range("2020-01-01", periods=6, freq="D")
    prices = [100,100,90,100,110,120]
    bars = pd.DataFrame({"Close" : prices}, index=dates)
 
    def trigger_strategy(history: pd.DataFrame) -> float:
        return 1.0 if history["Close"].iloc[-1] < 95 else 0.0

    result = run_backtest(bars, trigger_strategy, cost_bps=0.0)
    assert result.positions.loc["2020-01-04"] == 1.0
    assert result.gross_returns.loc["2020-01-04"] == pytest.approx(0.1111, rel = 1e-3)
    mask = result.gross_returns.index != "2020-01-04"
    assert (result.gross_returns[mask] == 0.0).all()



def test_cost_accounting_in_isolation():
    dates = pd.date_range("2020-01-01", periods=6, freq="D")
    prices = [100, 100, 100, 100, 100, 100]
    bars = pd.DataFrame({"Close": prices}, index=dates)

    flips = [1.0, -1.0, 1.0, -1.0, 1.0, -1.0]
    i = {"n": 0}
    def flipper(history: pd.DataFrame) -> float:
        val = flips[i["n"]]
        i["n"] += 1
        return val

    cost_bps = 10.0
    result = run_backtest(bars, flipper, cost_bps=cost_bps)

    # TODO 1: total turnover — every flip is a change of 2.0 (e.g. +1 to -1), work out by hand
    positions = [0, 1, -1, 1, -1, 1]
    total_turnover = 9;
    expected_total_cost = total_turnover * cost_bps / 10_000
    assert result.costs.sum() == pytest.approx(expected_total_cost)
    assert result.net_returns.sum() == pytest.approx(-expected_total_cost)