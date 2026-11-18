import math

import pandas as pd
import pytest

from biasguard import (BacktestEngine, CostModel, DataHandler,
                       SimulatedExecutionHandler, Strategy)
from biasguard.analytics import max_drawdown
from biasguard.strategy import BuyAndHold, SMACrossover
from biasguard.synthetic import make_ohlcv


def test_datahandler_never_serves_future_bars():
    df = make_ohlcv(50)
    dh = DataHandler({"X": df})
    dh.advance()
    dh.advance()
    bars = dh.latest_bars("X", 100)
    assert len(bars) == 2
    assert bars.index[-1] == dh.current_time


def test_datahandler_rejects_bad_data():
    df = make_ohlcv(10).drop(columns=["volume"])
    with pytest.raises(ValueError):
        DataHandler({"X": df})


def test_orders_fill_at_next_bar_open():
    df = make_ohlcv(30)
    result = BacktestEngine({"X": df}, BuyAndHold("X")).run()
    fill = result.fills[0]
    assert fill.timestamp == df.index[1]            # next bar, not the same bar
    assert fill.price == pytest.approx(df["open"].iloc[1])


def test_buy_and_hold_matches_manual_calculation():
    df = make_ohlcv(100)
    cash0 = 100_000.0
    result = BacktestEngine({"X": df}, BuyAndHold("X"), initial_cash=cash0).run()
    qty = int(cash0 / df["close"].iloc[0])
    expected = (cash0 - qty * df["open"].iloc[1]) + qty * df["close"].iloc[-1]
    assert result.equity.iloc[-1] == pytest.approx(expected)


def test_costs_reduce_final_equity():
    df = make_ohlcv(200)
    free = BacktestEngine({"X": df}, SMACrossover("X", 10, 30)).run()
    costly = BacktestEngine(
        {"X": df}, SMACrossover("X", 10, 30),
        execution=SimulatedExecutionHandler(CostModel(commission_bps=10, slippage_bps=10)),
    ).run()
    assert costly.equity.iloc[-1] < free.equity.iloc[-1]


def test_max_drawdown():
    eq = pd.Series([100, 120, 90, 110], dtype=float)
    assert max_drawdown(eq) == pytest.approx(-0.25)


def test_sharpe_is_nan_for_flat_equity():
    from biasguard.analytics import compute_metrics
    eq = pd.Series([100.0] * 10, index=pd.bdate_range("2020-01-01", periods=10))
    assert math.isnan(compute_metrics(eq)["sharpe"])


def test_sma_crossover_trades_and_is_deterministic():
    df = make_ohlcv(300, seed=3)
    a = BacktestEngine({"X": df}, SMACrossover("X", 10, 30)).run()
    b = BacktestEngine({"X": df}, SMACrossover("X", 10, 30)).run()
    assert len(a.fills) > 0
    pd.testing.assert_series_equal(a.equity, b.equity)
