"""`load_trading_days` is the calendar every equity-curve study walks, so its CAGR counts real trading days.

The universe's own bar dates are not one: a few symbols carry bars on market holidays, and each
such date entered the exit-sweep and ranking-weights equity curves as a flat trading day.
"""

from datetime import date
from unittest.mock import MagicMock

import polars as pl
import pytest

from turtlex.research import qullamaggie as research


def test_the_calendar_is_spy_s_bar_dates_in_order() -> None:
    repo = MagicMock()
    days = [date(2024, 11, 27), date(2024, 11, 29), date(2024, 11, 26)]  # no bar on Thanksgiving, Nov 28
    repo.get_bars_pl.return_value = pl.DataFrame({"date": days})

    assert research.load_trading_days(repo, date(2024, 11, 26), date(2024, 11, 29)) == sorted(days)
    repo.get_bars_pl.assert_called_once_with(research.MARKET_TICKER, date(2024, 11, 26), date(2024, 11, 29))


def test_no_spy_bars_raises() -> None:
    repo = MagicMock()
    repo.get_bars_pl.return_value = pl.DataFrame()

    with pytest.raises(ValueError, match="no trading calendar"):
        research.load_trading_days(repo, date(2024, 1, 1), date(2024, 1, 31))
