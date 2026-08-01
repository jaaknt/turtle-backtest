"""Parity between the bulk research Qullamaggie signal layer and the production strategy.

`turtlex/research/qullamaggie.py` loads the whole universe in one query for the scripts/
studies; `QullamaggieStrategy` loads one ticker at a time for the runner. They must agree
exactly. This feeds one synthetic multi-symbol frame — including a split, a dividend drift
and a zero-volume bar — through both paths and asserts identical
(symbol, signal_date, entry_date, entry_price) tuples.
"""

from datetime import date, timedelta
from unittest.mock import MagicMock

import numpy as np
import polars as pl
import pytest

from turtlex.backtest.processor import SignalProcessor
from turtlex.research import qullamaggie as research
from turtlex.strategy.trading.qullamaggie import QullamaggieStrategy

N = 340  # > min_bars=300 and > 253 bars needed for roc_252d
QUIET = 30  # trailing bars with volume dry-up and a contracted daily range
START = date(2020, 1, 2)


def _symbol_bars(
    breakout_idx: int,
    breakout_close: float = 120.0,
    split_at: int | None = None,
    dividend_drift: bool = False,
    zero_volume_idx: int | None = None,
    n: int = N,
) -> pl.DataFrame:
    """Build one symbol's bars satisfying every filter except the breakout itself.

    Mirrors the fixture in tests/strategy/trading/test_qullamaggie.py: close alternates
    100/101 so RSI sits near 50 and the 50-day max is 101, and the last QUIET bars carry
    600K volume against 1M before (dry-up, no surge) with a 3.5% range against 5% (ADR
    >= 3% while ADR10/ADR50 < 0.9).

    Args:
        breakout_idx: Bar index whose close breaks out
        breakout_close: Close applied at `breakout_idx`
        split_at: If set, raw prices are doubled from this index on, so adjusted_close
            stays on one basis while the raw close shows a discontinuity
        dividend_drift: If True, apply a slowly growing adjustment factor
        zero_volume_idx: If set, that bar gets zero volume (dropped by both paths)
        n: Number of bars
    """
    adj_close = np.array([100.0 + (i % 2) for i in range(n)])
    adj_close[breakout_idx] = breakout_close
    ranges = np.where(np.arange(n) >= n - QUIET, 0.035, 0.05)
    volumes = np.where(np.arange(n) >= n - QUIET, 600_000.0, 1_000_000.0)
    if zero_volume_idx is not None:
        volumes[zero_volume_idx] = 0.0

    # factor = adjusted_close / raw_close; raw = adjusted / factor
    factor = np.ones(n)
    if split_at is not None:
        factor[split_at:] = 0.5
    if dividend_drift:
        factor *= np.linspace(1.0, 0.97, n)
    raw_close = adj_close / factor

    return pl.DataFrame(
        {
            "date": [START + timedelta(days=i) for i in range(n)],
            "open": raw_close,
            "high": raw_close * (1.0 + ranges),
            "low": raw_close,
            "close": raw_close,
            "adjusted_close": adj_close,
            "volume": volumes,
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


def _spy_bull(last_date: date, n: int = 900) -> pl.DataFrame:
    """SPY bars trending up so every date passes the regime gate."""
    return pl.DataFrame(
        {
            "date": [last_date - timedelta(days=n - 1 - i) for i in range(n)],
            "close": np.linspace(300.0, 500.0, n),
        },
        schema={"date": pl.Date, "close": pl.Float64},
    )


@pytest.fixture
def universe() -> dict[str, pl.DataFrame]:
    """Three symbols exercising a clean case, a split and a dividend drift + zero-volume bar."""
    return {
        "CLEAN.US": _symbol_bars(breakout_idx=N - 5),
        "SPLIT.US": _symbol_bars(breakout_idx=N - 2, split_at=N - 120),
        "DIVID.US": _symbol_bars(breakout_idx=N - 3, dividend_drift=True, zero_volume_idx=N - 60),
    }


def _library_entries(
    universe: dict[str, pl.DataFrame], spy: pl.DataFrame, start_date: date, sma_thresh: float = QullamaggieStrategy.SMA_THRESH
) -> set[tuple]:
    """Run the production path: QullamaggieStrategy signals + SignalProcessor entries."""
    end_date = max(df["date"][-1] for df in universe.values())

    def get_bars_pl(ticker: str, start: date, end: date, tf: object = None) -> pl.DataFrame:
        # Faithful stub of DailyBarsQueryRepository: symbol equality, inclusive date range, ordered.
        source = spy if ticker == research.MARKET_TICKER else universe[ticker]
        return source.filter((pl.col("date") >= start) & (pl.col("date") <= end)).sort("date")

    repo = MagicMock()
    repo.get_bars_pl.side_effect = get_bars_pl
    ranking = MagicMock()
    ranking.ranking.return_value = 50
    strategy = QullamaggieStrategy(bars_history=repo, ranking_strategy=ranking, sma_thresh=sma_thresh)
    processor = SignalProcessor(max_holding_period=60, bars_history=repo, exit_strategy=MagicMock(), benchmark_tickers=[])

    out: set[tuple] = set()
    for ticker in sorted(universe):
        for signal in strategy.get_signals(ticker, start_date, end_date):
            entry = processor.calculate_entry_data(signal)
            if entry is not None:
                out.add((signal.ticker, signal.date, entry.date, round(entry.price, 6)))
    return out


def _research_entries(universe: dict[str, pl.DataFrame], spy: pl.DataFrame, start_date: date, sma_thresh: float) -> set[tuple]:
    """Run the bulk research path over the same synthetic data."""
    frame = pl.concat(
        [df.with_columns(pl.lit(symbol).alias("symbol")).rename({"close": "raw_close"}) for symbol, df in sorted(universe.items())]
    )
    bars = research.prepare_bars(frame)
    spy_regime = spy.sort("date").with_columns(pl.col("close").shift(1).rolling_mean(200, min_samples=200).alias("sma200"))
    bull_dates = set(spy_regime.filter(pl.col("close") > pl.col("sma200"))["date"].to_list())

    signals = research.get_signals(research.add_indicators(bars), bull_dates, start_date, sma_thresh=sma_thresh)
    entries = research.resolve_entries(signals, bars)
    return {(row["symbol"], row["date"], row["entry_date"], round(row["entry_price"], 6)) for row in entries.iter_rows(named=True)}


class TestSignalParity:
    def test_thresholds_match_the_production_strategy(self) -> None:
        """The research module's constants must not drift from the strategy's class attributes."""
        assert research.MIN_AVG_VOL == QullamaggieStrategy.MIN_AVG_VOL
        assert research.MIN_PRICE == QullamaggieStrategy.MIN_PRICE
        assert research.MAX_PRICE == QullamaggieStrategy.MAX_PRICE
        assert research.COOLDOWN_DAYS == QullamaggieStrategy.COOLDOWN_DAYS
        assert research.VOL_SURGE_MAX == QullamaggieStrategy.VOL_SURGE_MAX
        assert research.ROC_CAP == QullamaggieStrategy.ROC_CAP
        assert research.RSI_CAP == QullamaggieStrategy.RSI_CAP
        assert research.ADR_MIN == QullamaggieStrategy.ADR_MIN
        assert research.ADR_CHANGE_CAP == QullamaggieStrategy.ADR_CHANGE_CAP
        assert research.MARKET_TICKER == QullamaggieStrategy.MARKET_TICKER
        assert research.MARKET_SMA_WARMUP_DAYS == QullamaggieStrategy.MARKET_SMA_WARMUP_DAYS

    def test_constructor_defaults_match(self) -> None:
        """WARMUP_DAYS/MIN_BARS/SMA_THRESH must equal the strategy constructor defaults they mirror.

        sma_thresh is asserted against the instance, not QullamaggieStrategy.SMA_THRESH: the
        filter reads self.sma_thresh, so a constructor default decoupled from the class
        constant would diverge from the research path while the constants still matched.
        """
        strategy = QullamaggieStrategy(bars_history=MagicMock(), ranking_strategy=MagicMock())
        assert research.WARMUP_DAYS == strategy.warmup_period
        assert research.MIN_BARS == strategy.min_bars
        assert research.SMA_THRESH == strategy.sma_thresh

    def test_both_paths_find_signals(self, universe: dict[str, pl.DataFrame]) -> None:
        """Guard against a vacuous parity assertion: the fixture must actually produce signals."""
        last_date = max(df["date"][-1] for df in universe.values())
        spy = _spy_bull(last_date)
        start_date = last_date - timedelta(days=10)

        entries = _library_entries(universe, spy, start_date)
        assert {symbol for symbol, _, _, _ in entries} == {"CLEAN.US", "SPLIT.US", "DIVID.US"}

    def test_signal_on_the_final_bar_is_dropped_by_both_paths(self, universe: dict[str, pl.DataFrame]) -> None:
        """A breakout on the last available bar has no next bar, so neither path can enter it."""
        universe = {**universe, "TAIL.US": _symbol_bars(breakout_idx=N - 1)}
        last_date = max(df["date"][-1] for df in universe.values())
        spy = _spy_bull(last_date)
        start_date = last_date - timedelta(days=10)

        library = _library_entries(universe, spy, start_date)
        bulk = _research_entries(universe, spy, start_date, QullamaggieStrategy.SMA_THRESH)

        assert "TAIL.US" not in {symbol for symbol, _, _, _ in library}
        assert bulk == library

    @pytest.mark.parametrize(("sma_thresh", "expect_entries"), [(QullamaggieStrategy.SMA_THRESH, True), (0.25, False)])
    def test_entries_are_identical(self, universe: dict[str, pl.DataFrame], sma_thresh: float, expect_entries: bool) -> None:
        """Both paths must agree at the default threshold and under an override.

        Every fixture breakout sits ~19.5% above its SMA50, so 0.25 rejects all of them:
        a path that ignored sma_thresh would still return entries and fail the comparison.
        expect_entries keeps that case from passing vacuously as set() == set().
        """
        last_date = max(df["date"][-1] for df in universe.values())
        spy = _spy_bull(last_date)
        start_date = last_date - timedelta(days=10)

        library = _library_entries(universe, spy, start_date, sma_thresh)
        bulk = _research_entries(universe, spy, start_date, sma_thresh)

        assert bulk == library
        assert bool(library) is expect_entries

    def test_entries_are_identical_over_a_wide_window(self, universe: dict[str, pl.DataFrame]) -> None:
        """A start_date deep inside the frame exercises the warmup-window cooldown chain."""
        last_date = max(df["date"][-1] for df in universe.values())
        spy = _spy_bull(last_date)
        start_date = START + timedelta(days=280)

        library = _library_entries(universe, spy, start_date)
        bulk = _research_entries(universe, spy, start_date, QullamaggieStrategy.SMA_THRESH)

        assert bulk == library

    def test_zero_volume_bar_immediately_after_a_signal_is_skipped_by_both_paths(self, universe: dict[str, pl.DataFrame]) -> None:
        """The bar after a breakout is unfillable, so both paths must enter one bar later.

        This is the case where the production path could previously diverge: its entry search
        queries the repository directly, bypassing the strategy's zero-volume filter.
        """
        universe = {**universe, "GAP.US": _symbol_bars(breakout_idx=N - 4, zero_volume_idx=N - 3)}
        last_date = max(df["date"][-1] for df in universe.values())
        spy = _spy_bull(last_date)
        start_date = last_date - timedelta(days=10)

        library = _library_entries(universe, spy, start_date)
        bulk = _research_entries(universe, spy, start_date, QullamaggieStrategy.SMA_THRESH)

        gap_entries = [entry_date for symbol, _, entry_date, _ in library if symbol == "GAP.US"]
        assert gap_entries == [START + timedelta(days=N - 2)]  # skipped the zero-volume N-3 bar
        assert bulk == library

    def test_zero_volume_bar_is_dropped_by_both_paths(self, universe: dict[str, pl.DataFrame]) -> None:
        """The zero-volume bar must not appear as a signal or an entry bar on either side."""
        zero_volume_date = START + timedelta(days=N - 60)
        assert universe["DIVID.US"].filter(pl.col("date") == zero_volume_date)["volume"][0] == 0.0

        last_date = max(df["date"][-1] for df in universe.values())
        spy = _spy_bull(last_date)
        entries = _research_entries(universe, spy, START + timedelta(days=280), QullamaggieStrategy.SMA_THRESH)

        assert all(entry_date != zero_volume_date for _, _, entry_date, _ in entries)
