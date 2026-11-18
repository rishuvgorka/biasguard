"""Strategy base class and two reference strategies."""

from abc import ABC, abstractmethod


class Strategy(ABC):
    """Subclass and implement ``on_bar``.

    Rule: only use ``ctx.data.latest_bars`` to look at market data.
    """

    def on_start(self, ctx) -> None:
        pass

    @abstractmethod
    def on_bar(self, ctx) -> None:
        ...


class BuyAndHold(Strategy):
    """Baseline: buy once on the first bar and hold. Every strategy must beat this."""

    def __init__(self, symbol: str, target_pct: float = 1.0):
        self.symbol = symbol
        self.target_pct = target_pct
        self._done = False

    def on_bar(self, ctx) -> None:
        if not self._done:
            ctx.order_target_percent(self.symbol, self.target_pct)
            self._done = True


class SMACrossover(Strategy):
    """Long when the fast moving average is above the slow one, else flat."""

    def __init__(self, symbol: str, fast: int = 20, slow: int = 50):
        if fast >= slow:
            raise ValueError("fast must be < slow")
        self.symbol, self.fast, self.slow = symbol, fast, slow

    def on_bar(self, ctx) -> None:
        closes = ctx.data.latest_bars(self.symbol, self.slow)["close"]
        if len(closes) < self.slow:
            return  # not enough history yet
        fast_ma = closes.tail(self.fast).mean()
        slow_ma = closes.mean()
        ctx.order_target_percent(self.symbol, 1.0 if fast_ma > slow_ma else 0.0)
