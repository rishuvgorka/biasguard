"""The event loop that ties data, strategy, execution and portfolio together.

Per timestamp, in this exact order:
  1. Advance the clock to the next bar.
  2. Fill orders queued on earlier bars at THIS bar's open.
  3. Mark the portfolio to market at THIS bar's close.
  4. Let the strategy see data up to this close and queue new orders.
New orders therefore always fill on a later bar than the one that triggered them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .analytics import compute_metrics
from .data import DataHandler
from .events import FillEvent, OrderEvent
from .execution import SimulatedExecutionHandler
from .portfolio import Portfolio
from .strategy import Strategy


class Context:
    """The only handle a strategy gets on the outside world."""

    def __init__(self, data: DataHandler, portfolio: Portfolio):
        self.data = data
        self.portfolio = portfolio
        self._queued: list[OrderEvent] = []

    @property
    def now(self) -> pd.Timestamp:
        return self.data.current_time

    def order(self, symbol: str, quantity: int) -> None:
        if quantity != 0:
            self._queued.append(OrderEvent(self.now, symbol, int(quantity)))

    def order_target_percent(self, symbol: str, pct: float) -> None:
        bar = self.data.current_bar(symbol)
        if bar is None:
            return
        target_qty = int(self.portfolio.equity * pct / float(bar["close"]))
        self.order(symbol, target_qty - self.portfolio.position(symbol))

    def _drain(self) -> list[OrderEvent]:
        orders, self._queued = self._queued, []
        return orders


@dataclass
class BacktestResult:
    equity: pd.Series
    fills: list[FillEvent]
    metrics: dict[str, float] = field(default_factory=dict)

    def fills_frame(self) -> pd.DataFrame:
        return pd.DataFrame([vars(f) for f in self.fills])


class BacktestEngine:
    def __init__(
        self,
        data: dict[str, pd.DataFrame],
        strategy: Strategy,
        initial_cash: float = 100_000.0,
        execution: SimulatedExecutionHandler | None = None,
    ):
        self.data = DataHandler(data)
        self.strategy = strategy
        self.portfolio = Portfolio(initial_cash)
        self.execution = execution or SimulatedExecutionHandler()
        self.ctx = Context(self.data, self.portfolio)

    def run(self) -> BacktestResult:
        pending: list[OrderEvent] = []
        fills: list[FillEvent] = []
        started = False

        while self.data.advance():
            ts = self.data.current_time

            # 2. fill earlier orders at this bar's open
            still_pending = []
            for order in pending:
                bar = self.data.current_bar(order.symbol)
                if bar is None:  # symbol not trading today: carry over
                    still_pending.append(order)
                    continue
                fill = self.execution.execute(order, bar, ts)
                self.portfolio.on_fill(fill)
                fills.append(fill)
            pending = still_pending

            # 3. mark to market at this bar's close
            prices = {
                s: float(b["close"])
                for s in self.data.symbols
                if (b := self.data.current_bar(s)) is not None
            }
            self.portfolio.mark_to_market(ts, prices)

            # 4. strategy decides using data up to this close
            if not started:
                self.strategy.on_start(self.ctx)
                started = True
            self.strategy.on_bar(self.ctx)
            pending.extend(self.ctx._drain())

        equity = self.portfolio.equity_curve()
        return BacktestResult(equity, fills, compute_metrics(equity))
