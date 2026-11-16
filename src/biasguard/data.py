"""Data handling with a hard wall against lookahead.

The strategy never touches the raw DataFrames. It can only call
``latest_bars``, which returns data up to and including the current bar.
This is the first line of defence against lookahead bias.
"""

from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = ("open", "high", "low", "close", "volume")


def load_csv(path: str) -> pd.DataFrame:
    """Load an OHLCV CSV with a 'date' column into a validated DataFrame."""
    df = pd.read_csv(path, parse_dates=["date"], index_col="date")
    df.columns = [c.lower() for c in df.columns]
    return _validate(df)


def _validate(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("Index must be a DatetimeIndex")
    if not df.index.is_monotonic_increasing:
        df = df.sort_index()
    if df.index.has_duplicates:
        raise ValueError("Duplicate timestamps in data")
    if df[list(REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError("NaNs found in OHLCV data")
    return df


class DataHandler:
    """Serves bars one timestamp at a time across one or more symbols."""

    def __init__(self, data: dict[str, pd.DataFrame]):
        if not data:
            raise ValueError("No data provided")
        self._data = {s: _validate(df) for s, df in data.items()}
        index = None
        for df in self._data.values():
            index = df.index if index is None else index.union(df.index)
        self._timestamps = index.sort_values()
        self._i = -1

    @property
    def symbols(self) -> list[str]:
        return list(self._data)

    @property
    def current_time(self) -> pd.Timestamp:
        if self._i < 0:
            raise RuntimeError("Call advance() first")
        return self._timestamps[self._i]

    def advance(self) -> bool:
        """Move to the next timestamp. Returns False when data is exhausted."""
        if self._i + 1 >= len(self._timestamps):
            return False
        self._i += 1
        return True

    def current_bar(self, symbol: str) -> pd.Series | None:
        """The bar at the current timestamp, or None if the symbol has none."""
        df = self._data[symbol]
        t = self.current_time
        return df.loc[t] if t in df.index else None

    def latest_bars(self, symbol: str, n: int = 1) -> pd.DataFrame:
        """Up to ``n`` most recent bars, never beyond the current timestamp."""
        df = self._data[symbol]
        pos = df.index.searchsorted(self.current_time, side="right")
        return df.iloc[max(0, pos - n):pos]
