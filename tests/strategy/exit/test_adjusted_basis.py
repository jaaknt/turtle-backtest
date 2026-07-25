"""Every exit strategy must price its exit on the same basis as the entry.

`SignalProcessor.calculate_entry_data` enters on the split/dividend-adjusted open. An exit
priced on the raw close would misstate the return by the cumulative adjustment between the
exit bar and the newest stored bar — a bias that grows with trade age, because
`adjusted_close` is normalised to the latest bar. On a perfectly flat stock that shows up as
a phantom gain equal to the dividends paid after the exit.
"""

from datetime import date, timedelta
from unittest.mock import MagicMock

import polars as pl
import pytest

from turtlex.backtest.processor import SignalProcessor
from turtlex.model import Signal
from turtlex.strategy.exit import (
    ATRExitStrategy,
    BuyAndHoldExitStrategy,
    EMAExitStrategy,
    MACDExitStrategy,
    ProfitLossExitStrategy,
    TrailingPercentageLossExitStrategy,
)
from turtlex.strategy.exit.base import ExitStrategy, add_adjusted_columns

N_BARS = 90
DIVIDEND_AT = 70  # after every trade in this test has exited
START = date(2024, 1, 1)

EXIT_STRATEGY_CLASSES = [
    BuyAndHoldExitStrategy,
    EMAExitStrategy,
    MACDExitStrategy,
    ATRExitStrategy,
    ProfitLossExitStrategy,
    TrailingPercentageLossExitStrategy,
]


def _flat_stock_with_late_dividend() -> pl.DataFrame:
    """A stock whose price never moves, with a 2% dividend landing after every exit.

    Raw prices are flat at 100. `adjusted_close` is 98 before the dividend and 100 after, so
    the adjustment factor is 0.98 across the whole trade window. Any correctly-computed trade
    return here is exactly 0%.
    """
    raw = [100.0] * N_BARS
    adjusted = [98.0] * DIVIDEND_AT + [100.0] * (N_BARS - DIVIDEND_AT)
    return pl.DataFrame(
        {
            "date": [START + timedelta(days=i) for i in range(N_BARS)],
            "open": raw,
            "high": [101.0] * N_BARS,
            "low": [99.0] * N_BARS,
            "close": raw,
            "adjusted_close": adjusted,
            "volume": [1_000_000.0] * N_BARS,
        },
        schema={
            "date": pl.Date,
            "open": pl.Float64,
            "high": pl.Float64,
            "low": pl.Float64,
            "close": pl.Float64,
            "adjusted_close": pl.Float64,
            "volume": pl.Float64,
        },
    )


@pytest.fixture
def bars_repo() -> MagicMock:
    """Repository stub that filters by date range the way the real query does."""
    df = _flat_stock_with_late_dividend()
    repo = MagicMock()
    repo.get_bars_pl.side_effect = lambda ticker, start, end, *a, **kw: df.filter((pl.col("date") >= start) & (pl.col("date") <= end)).sort(
        "date"
    )
    return repo


@pytest.mark.parametrize("exit_strategy_class", EXIT_STRATEGY_CLASSES, ids=lambda c: c.__name__)
def test_flat_stock_reports_zero_return(bars_repo: MagicMock, exit_strategy_class: type[ExitStrategy]) -> None:
    """A flat stock must report a 0% return regardless of which exit strategy closes it."""
    processor = SignalProcessor(
        max_holding_period=60,
        bars_history=bars_repo,
        exit_strategy=exit_strategy_class(bars_repo),
        benchmark_tickers=[],
    )

    result = processor.run(Signal(ticker="X.US", date=START, ranking=50))

    assert result is not None
    assert result.realized_pct == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("exit_strategy_class", EXIT_STRATEGY_CLASSES, ids=lambda c: c.__name__)
def test_entry_and_exit_share_the_adjusted_basis(bars_repo: MagicMock, exit_strategy_class: type[ExitStrategy]) -> None:
    """Both legs must land on the adjusted basis (98), not the raw one (100)."""
    processor = SignalProcessor(
        max_holding_period=60,
        bars_history=bars_repo,
        exit_strategy=exit_strategy_class(bars_repo),
        benchmark_tickers=[],
    )

    result = processor.run(Signal(ticker="X.US", date=START, ranking=50))

    assert result is not None
    assert result.entry.price == pytest.approx(98.0)
    assert result.exit.price == pytest.approx(98.0)


class TestAddAdjustedColumns:
    """Direct tests for the shared adjustment helper."""

    def test_scales_ohl_by_the_bars_own_factor(self) -> None:
        df = pl.DataFrame(
            {
                "date": [date(2024, 1, 2)],
                "open": [200.0],
                "high": [220.0],
                "low": [180.0],
                "close": [202.0],
                "adjusted_close": [101.0],  # factor 0.5
            }
        )

        result = add_adjusted_columns(df)

        assert result["adj_open"][0] == pytest.approx(100.0)
        assert result["adj_high"][0] == pytest.approx(110.0)
        assert result["adj_low"][0] == pytest.approx(90.0)
        assert result["adj_close"][0] == pytest.approx(101.0)

    def test_factor_of_one_leaves_prices_unchanged(self) -> None:
        df = pl.DataFrame(
            {
                "date": [date(2024, 1, 2)],
                "open": [100.0],
                "high": [110.0],
                "low": [90.0],
                "close": [105.0],
                "adjusted_close": [105.0],
            }
        )

        result = add_adjusted_columns(df)

        assert result["adj_open"][0] == pytest.approx(100.0)
        assert result["adj_high"][0] == pytest.approx(110.0)
        assert result["adj_low"][0] == pytest.approx(90.0)
        assert result["adj_close"][0] == pytest.approx(105.0)

    def test_nonpositive_close_yields_null_instead_of_dividing_by_zero(self) -> None:
        df = pl.DataFrame(
            {
                "date": [date(2024, 1, 2)],
                "open": [100.0],
                "high": [110.0],
                "low": [90.0],
                "close": [0.0],
                "adjusted_close": [105.0],
            }
        )

        result = add_adjusted_columns(df)

        assert result["adj_open"][0] is None
        assert result["adj_high"][0] is None
        assert result["adj_low"][0] is None

    def test_empty_frame_passes_through(self) -> None:
        assert add_adjusted_columns(pl.DataFrame()).is_empty()
