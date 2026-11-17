"""Portfolio accounting: cash, positions, and the equity curve."""

import pandas as pd

from .events import FillEvent


class Portfolio:
    def __init__(self, initial_cash: float):
        self.initial_cash = float(initial_cash)
        self.cash = float(initial_cash)
        self.positions: dict[str, int] = {}
        self._last_price: dict[str, float] = {}
        self._curve: list[tuple[pd.Timestamp, float]] = []

    def position(self, symbol: str) -> int:
        return self.positions.get(symbol, 0)

    @property
    def equity(self) -> float:
        held = sum(q * self._last_price.get(s, 0.0) for s, q in self.positions.items())
        return self.cash + held

    def on_fill(self, fill: FillEvent) -> None:
        self.cash -= fill.quantity * fill.price + fill.commission
        self.positions[fill.symbol] = self.position(fill.symbol) + fill.quantity

    def mark_to_market(self, ts: pd.Timestamp, prices: dict[str, float]) -> None:
        self._last_price.update(prices)
        self._curve.append((ts, self.equity))

    def equity_curve(self) -> pd.Series:
        if not self._curve:
            return pd.Series(dtype=float, name="equity")
        idx, vals = zip(*self._curve)
        return pd.Series(vals, index=pd.DatetimeIndex(idx), name="equity")
