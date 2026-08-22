import pytest
import pandas as pd
from src.backtest.data import load_bars

SAMPLE_CSV = "data/sample_bars.csv"

def test_load_bars_happy_path():
    df = load_bars(SAMPLE_CSV)

    assert len(df) == 8
    assert list(df.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert df.index.is_monotonic_increasing
    assert df.isna().sum().sum() == 0

def test_load_bars_drops_junk_row():
    df = load_bars(SAMPLE_CSV)

    assert pd.Timestamp("2024-01-09") not in df.index
    assert pd.Timestamp ("2024-01-16") not in df.index
    assert pd.Timestamp("2024-01-08") in df.index

def test_load_bars_raises_on_missing_column(tmp_path):
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("Date,Open,High,Low,Close\n2024-01-02,1,2,3,4\n")

    with pytest.raises(ValueError):
        load_bars(str(bad_csv))


def test_load_bars_no_error_on_good_csv():
    df = load_bars(SAMPLE_CSV)
    assert df is not None