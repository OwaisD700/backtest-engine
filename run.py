# run.py
"""
Reproduce every number in the README from the raw CSV.

Usage (from the project root, venv active):
    python run.py
"""
import numpy as np
import pandas as pd

from src.backtest.data import load_bars
from src.backtest.engine import run_backtest, BacktestResult
from src.backtest.strategies import mean_reversion
from src.backtest.stats import (
    annualised_return,
    annualised_vol,
    sharpe,
    max_drawdown,
    hit_rate,
    bootstrap_sharpe_ci,
)

# Fixed settings. Every number in the README depends on these.
DATA_PATH = "data/spy.csv"            # check: must match your filename in data/
COST_BPS = 5.0                        # headline cost assumption
COST_SWEEP = [0.0, 1.0, 2.0, 5.0, 10.0, 20.0]
N_RESAMPLES = 10_000
SEED = 42                             # fixed so the bootstrap reproduces exactly


def buy_and_hold(history: pd.DataFrame) -> float:
    """Benchmark: always fully long. Same Strategy contract as mean_reversion."""
    return 1.0


def to_log(simple_returns: pd.Series) -> pd.Series:
    """
    Boundary conversion. engine.py works in SIMPLE returns (correct for
    scaling by position and subtracting costs). stats.py expects LOG
    returns (correct for annualising and compounding). Convert once, here.
    """
    return np.log1p(simple_returns)


def summarise(result: BacktestResult) -> dict:
    """All headline stats, computed on NET returns (after costs)."""
    r = to_log(result.net_returns)
    return {
        "Annualised return": annualised_return(r),
        "Annualised volatility": annualised_vol(r),
        "Sharpe ratio": sharpe(r),
        "Max drawdown": max_drawdown(r),
        "Hit rate": hit_rate(r[result.positions != 0]),
        "Total turnover": result.turnover.sum(),
    }


def main() -> None:
    # step 1: load data
    bars = load_bars(DATA_PATH)
    print(f"Data: {DATA_PATH}")
    print(f"Range: {bars.index[0].date()} to {bars.index[-1].date()} ({len(bars)} bars)\n")

    # step 2: run strategy and benchmark at the headline cost
    strat = run_backtest(bars, mean_reversion, cost_bps=COST_BPS)
    bench = run_backtest(bars, buy_and_hold, cost_bps=COST_BPS)

    # step 3: headline stats table
    s, b = summarise(strat), summarise(bench)
    print(f"## Results at {COST_BPS:g} bps per unit turnover\n")
    print("| Statistic | Mean reversion | Buy and hold |")
    print("|---|---|---|")
    for name in s:
        print(f"| {name} | {s[name]:.4f} | {b[name]:.4f} |")
    print()

    # step 4: bootstrap the strategy's Sharpe o@n net returns
    # pandas .sample() falls back to numpy's global RNG, so seeding it here
    # makes the interval identical on every run.
    np.random.seed(SEED)
    lo, hi = bootstrap_sharpe_ci(to_log(strat.net_returns), n_boot=N_RESAMPLES)
    print(f"## Bootstrap ({N_RESAMPLES:,} resamples, seed {SEED})\n")
    print(f"90% interval for Sharpe: [{lo:.3f}, {hi:.3f}]")
    if lo <= 0 <= hi:
        print("Zero is inside the interval: the Sharpe is not distinguishable from zero.\n")
    else:
        print("Zero is outside the interval.\n")

    # step 5: cost sensitivity sweep
    print("## Cost sensitivity\n")
    print("| Cost (bps) | Sharpe (net) |")
    print("|---|---|")
    breakeven = None
    for bps in COST_SWEEP:
        sr = sharpe(to_log(run_backtest(bars, mean_reversion, cost_bps=bps).net_returns))
        print(f"| {bps:g} | {sr:.4f} |")
        if breakeven is None and sr <= 0:
            breakeven = bps
    print()
    if breakeven is None:
        print(f"Sharpe stays positive up to {COST_SWEEP[-1]:g} bps.")
    else:
        print(f"Sharpe first drops to zero or below at {breakeven:g} bps.")


if __name__ == "__main__":
    main()