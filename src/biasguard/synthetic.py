"""Synthetic price data so tests and demos need no network access."""

import numpy as np
import pandas as pd


def make_ohlcv(n: int = 500, seed: int = 0, start: str = "2020-01-01",
               s0: float = 100.0, mu: float = 0.08, sigma: float = 0.20) -> pd.DataFrame:
    """Geometric Brownian motion daily bars (deterministic given ``seed``)."""
    rng = np.random.default_rng(seed)
    dt = 1 / 252
    rets = rng.normal((mu - 0.5 * sigma**2) * dt, sigma * np.sqrt(dt), n)
    close = s0 * np.exp(np.cumsum(rets))
    open_ = np.concatenate([[s0], close[:-1]]) * (1 + rng.normal(0, 0.001, n))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.003, n)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.003, n)))
    volume = rng.integers(100_000, 1_000_000, n)
    idx = pd.bdate_range(start, periods=n, name="date")
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=idx
    )
