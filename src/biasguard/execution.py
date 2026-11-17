"""Simulated execution: turns orders into fills with realistic costs."""

from dataclasses import dataclass

import pandas as pd

from .events import FillEvent, OrderEvent


@dataclass(frozen=True)
class CostModel:
    commission_per_share: float = 0.0
    commission_bps: float = 0.0   # basis points of traded notional
    slippage_bps: float = 0.0     # adverse price move, in basis points

    def stressed(self, factor: float) -> "CostModel":
        """Scale all costs. Used later by the cost-realism check."""
        return CostModel(
            self.commission_per_share * factor,
            self.commission_bps * factor,
            self.slippage_bps * factor,
        )


class SimulatedExecutionHandler:
    """Fills orders at the OPEN of the bar after the decision.

    Deciding on bar t's close and filling at bar t+1's open is the simplest
    lookahead-safe convention: you cannot trade at a price you used to decide.
    """

    def __init__(self, cost_model: CostModel | None = None):
        self.cost_model = cost_model or CostModel()

    def execute(self, order: OrderEvent, bar: pd.Series, ts: pd.Timestamp) -> FillEvent:
        cm = self.cost_model
        ref_price = float(bar["open"])
        direction = 1 if order.quantity > 0 else -1
        fill_price = ref_price * (1 + direction * cm.slippage_bps / 1e4)
        qty = abs(order.quantity)
        commission = qty * cm.commission_per_share + qty * fill_price * cm.commission_bps / 1e4
        return FillEvent(
            timestamp=ts,
            symbol=order.symbol,
            quantity=order.quantity,
            price=fill_price,
            commission=commission,
            slippage_cost=qty * abs(fill_price - ref_price),
        )
