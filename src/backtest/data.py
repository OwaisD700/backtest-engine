"""
data.py — data loading and cleaning for the backtest engine.

SCOPE (Gate 1 of the prep plan):
    One function, load_bars(path) -> pd.DataFrame, that turns a raw
    OHLCV CSV into a clean DataFrame the rest of the engine can trust.

    Specifically, this file is responsible for:
      - Reading the CSV
      - Parsing the date column into a proper DatetimeIndex, sorted
        ascending
      - Coercing non-numeric junk in price/volume columns (e.g. "n/a")
        to NaN, rather than silently leaving the column as strings
      - Deciding — explicitly, with a comment explaining why — what
        happens to missing values: drop the row, forward-fill, or
        something else
      - Raising a clear error if a required OHLCV column is missing
        from the file entirely

    OUT OF SCOPE for this file (belongs elsewhere):
      - Computing returns, Sharpe, drawdown, or any other statistic
        (-> stats.py)
      - Any notion of a trading signal, position, or no-look-ahead
        enforcement on a signal (-> engine.py)
      - Numerically stable variance/mean (-> welford.py)
      - Fetching data live over the network — this file only ever
        reads a CSV that's already sitting on disk

    In short: load_bars() takes a messy file and hands back a
    DataFrame with a DatetimeIndex, numeric OHLCV columns, and a
    documented policy on gaps. Nothing more.
"""

import pandas as pd

REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


def load_bars(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")

    # TODO: parse Date into DatetimeIndex, sort
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date")
    df = df.sort_index()
    # TODO: coerce OHLCV columns to numeric
    for col in REQUIRED_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors = "coerce")
    # TODO: apply the drop-any-NaN-row policy
    df = df.dropna()

    return df