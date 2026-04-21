"""Tests for MarsStrategy polars path."""
from datetime import date, timedelta
from turtle.common.enums import TimeFrameUnit
from turtle.repository.analytics import OhlcvAnalyticsRepository
from turtle.strategy.ranking.base import RankingStrategy
from turtle.strategy.trading.mars import MarsStrategy
from unittest.mock import MagicMock

import polars as pl


def _build_ohlcv(n: int = 300) -> pl.DataFrame:
    """Build n bars of uptrending OHLCV data sufficient to warm up all Mars indicators."""
    base, growth = 100.0, 1.003
    closes = [base * (growth**i) for i in range(n)]
    opens = [c * 0.998 for c in closes]
    highs = [c * 1.002 for c in closes]
    lows = [c * 0.997 for c in closes]
    volumes = [1_000_000.0] * n
    start = date(2019, 1, 1)
    return pl.DataFrame({
        "date": [start + timedelta(days=i) for i in range(n)],
        "open": opens, "high": highs, "low": lows, "close": closes, "volume": volumes,
    })


def _make_strategy(pl_df: pl.DataFrame, min_bars: int = 100) -> MarsStrategy:
    mock_repo = MagicMock(spec=OhlcvAnalyticsRepository)
    mock_repo.get_bars_pl.return_value = pl_df
    mock_ranking = MagicMock(spec=RankingStrategy)
    mock_ranking.ranking.return_value = 8
    return MarsStrategy(
        bars_history=mock_repo,
        ranking_strategy=mock_ranking,
        time_frame_unit=TimeFrameUnit.WEEK,
        warmup_period=100,
        min_bars=min_bars,
    )


# ---------------------------------------------------------------------------
# calculate_indicators_pl
# ---------------------------------------------------------------------------

def test_calculate_indicators_pl_columns() -> None:
    """All expected indicator columns are present after calculate_indicators_pl()."""
    strategy = _make_strategy(_build_ohlcv())
    strategy.pl_df = _build_ohlcv(50)
    strategy.calculate_indicators_pl()

    expected = [
        "max_box_4", "min_box_4", "max_close_10", "ema_10", "ema_20",
        "macd", "ema_volume_4", "macd_signal", "macd_histogram",
        "consolidation_change", "hard_stoploss", "volume_change",
    ]
    for col in expected:
        assert col in strategy.pl_df.columns, f"Missing column: {col}"


def test_macd_histogram_is_macd_minus_signal() -> None:
    """macd_histogram = macd - macd_signal (positive when MACD is above signal line)."""
    strategy = _make_strategy(_build_ohlcv())
    strategy.pl_df = _build_ohlcv(100)
    strategy.calculate_indicators_pl()
    last = strategy.pl_df.row(-1, named=True)
    if last["macd"] is not None and last["macd_signal"] is not None:
        expected = last["macd"] - last["macd_signal"]
        assert abs(last["macd_histogram"] - expected) < 1e-9


# ---------------------------------------------------------------------------
# is_buy_signal
# ---------------------------------------------------------------------------

def _good_row() -> dict:
    """A row dict that satisfies all buy conditions."""
    return {
        "date": date(2024, 1, 15),
        "close": 100.0,
        "max_close_10": 99.0,          # close >= max_close_10 ✓
        "ema_10": 98.0,
        "ema_20": 97.0,                 # ema_10 >= ema_20 ✓
        "macd": 0.5,
        "macd_signal": 0.3,             # not None ✓
        "consolidation_change": 0.05,   # <= 0.12 ✓
        "hard_stoploss": 80.0,          # (100-80)/100 = 0.20 <= 0.25 ✓
        "max_box_4": 90.0,
        "min_box_4": 85.0,
        "volume": 1_000_000.0,
        "ema_volume_4": 900_000.0,
        "volume_change": 1.1,
        "macd_histogram": 0.2,
    }


def test_is_buy_signal_null_guard() -> None:
    """is_buy_signal returns False without crashing when box indicators are None."""
    strategy = _make_strategy(_build_ohlcv())
    row = {**_good_row(), "max_close_10": None, "max_box_4": None, "min_box_4": None}
    assert strategy.is_buy_signal("TEST", row) is False


def test_is_buy_signal_happy_path() -> None:
    """is_buy_signal returns True when all conditions are satisfied."""
    strategy = _make_strategy(_build_ohlcv())
    assert strategy.is_buy_signal("TEST", _good_row()) is True


def test_is_buy_signal_close_below_max_close_10() -> None:
    strategy = _make_strategy(_build_ohlcv())
    row = {**_good_row(), "max_close_10": 105.0}  # close < max_close_10
    assert strategy.is_buy_signal("TEST", row) is False


def test_is_buy_signal_ema_not_stacked() -> None:
    strategy = _make_strategy(_build_ohlcv())
    row = {**_good_row(), "ema_10": 96.0, "ema_20": 97.0}  # ema_10 < ema_20
    assert strategy.is_buy_signal("TEST", row) is False


def test_is_buy_signal_macd_null() -> None:
    strategy = _make_strategy(_build_ohlcv())
    row = {**_good_row(), "macd": None}
    assert strategy.is_buy_signal("TEST", row) is False


def test_is_buy_signal_consolidation_too_wide() -> None:
    strategy = _make_strategy(_build_ohlcv())
    row = {**_good_row(), "consolidation_change": 0.15}  # > 0.12
    assert strategy.is_buy_signal("TEST", row) is False


def test_is_buy_signal_stoploss_too_far() -> None:
    strategy = _make_strategy(_build_ohlcv())
    row = {**_good_row(), "hard_stoploss": 70.0}  # (100-70)/100 = 0.30 > 0.25
    assert strategy.is_buy_signal("TEST", row) is False


# ---------------------------------------------------------------------------
# _get_polars_signals / get_signals
# ---------------------------------------------------------------------------

def test_get_signals_produces_signal() -> None:
    """get_signals returns at least one signal on strongly uptrending data."""
    pl_df = _build_ohlcv(300)
    strategy = _make_strategy(pl_df, min_bars=100)
    last_date = pl_df["date"][-1]
    signals = strategy.get_signals("TEST", last_date, last_date)
    assert len(signals) >= 1


def test_get_signals_returns_empty_when_insufficient_data() -> None:
    pl_df = _build_ohlcv(50)  # 50 bars < min_bars=100
    strategy = _make_strategy(pl_df, min_bars=100)
    last_date = pl_df["date"][-1]
    assert strategy.get_signals("TEST", last_date, last_date) == []


def test_get_signals_returns_empty_when_start_date_beyond_data() -> None:
    strategy = _make_strategy(_build_ohlcv(300))
    assert strategy.get_signals("TEST", date(2099, 1, 1), date(2099, 1, 1)) == []


# ---------------------------------------------------------------------------
# ranking
# ---------------------------------------------------------------------------

def test_ranking_returns_correct_price_bracket() -> None:
    """ranking() returns the correct score for the closing price on a given date."""
    pl_df = _build_ohlcv(300)
    strategy = _make_strategy(pl_df)
    # close at last bar ~= 100 * 1.003^299 ≈ 246 → bracket $240-$1000 → score 4
    last_date = pl_df["date"][-1]
    result = strategy.ranking("TEST", last_date)
    assert result == 4


def test_ranking_returns_zero_when_no_data() -> None:
    mock_repo = MagicMock(spec=OhlcvAnalyticsRepository)
    mock_repo.get_bars_pl.return_value = pl.DataFrame()
    mock_ranking = MagicMock(spec=RankingStrategy)
    strategy = MarsStrategy(mock_repo, mock_ranking, min_bars=1)
    assert strategy.ranking("TEST", date(2024, 1, 1)) == 0
