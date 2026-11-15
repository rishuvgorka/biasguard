"""Event types passed between engine components.

Events are immutable so that no component can silently rewrite history.
Quantities are signed: positive = buy, negative = sell.
"""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class OrderEvent:
    timestamp: pd.Timestamp  # when the strategy decided (NOT when it fills)
    symbol: str
    quantity: int


@dataclass(frozen=True)
class FillEvent:
    timestamp: pd.Timestamp  # when the order actually executed
    symbol: str
    quantity: int
    price: float             # price after slippage
    commission: float
    slippage_cost: float     # money lost to slippage vs. the reference price
