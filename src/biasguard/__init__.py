"""BiasGuard: event-driven backtesting with built-in bias detection."""

from .analytics import compute_metrics
from .data import DataHandler, load_csv
from .engine import BacktestEngine, BacktestResult, Context
from .events import FillEvent, OrderEvent
from .execution import CostModel, SimulatedExecutionHandler
from .portfolio import Portfolio
from .strategy import Strategy

__all__ = [
    "BacktestEngine", "BacktestResult", "Context", "CostModel", "DataHandler",
    "FillEvent", "OrderEvent", "Portfolio", "SimulatedExecutionHandler",
    "Strategy", "compute_metrics", "load_csv",
]
