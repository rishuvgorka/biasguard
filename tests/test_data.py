import pytest

from biasguard import DataHandler
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