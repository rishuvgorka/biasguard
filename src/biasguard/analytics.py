"""Performance metrics computed from an equity curve."""

import numpy as np
import pandas as pd


def max_drawdown(equity: pd.Series) -> float:
    """Largest peak-to-trough decline, as a negative fraction (e.g. -0.25)."""
    running_peak = equity.cummax()
    return float((equity / running_peak - 1.0).min())


def compute_metrics(equity: pd.Series, periods_per_year: int = 252) -> dict[str, float]:
    if len(equity) < 2:
        raise ValueError("Need at least two equity points")
    returns = equity.pct_change().dropna()
    years = (len(equity) - 1) / periods_per_year
    total_return = float(equity.iloc[-1] / equity.iloc[0] - 1.0)
    cagr = float((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1.0) if years > 0 else float("nan")
    vol = float(returns.std(ddof=1) * np.sqrt(periods_per_year))
    mean_ann = float(returns.mean() * periods_per_year)
    sharpe = mean_ann / vol if vol > 0 else float("nan")  # risk-free rate assumed 0
    return {
        "total_return": total_return,
        "cagr": cagr,
        "annual_vol": vol,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown(equity),
    }
