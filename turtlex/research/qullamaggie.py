"""Bulk Qullamaggie breakout signal layer shared by the scripts/qullamaggie-*.py studies.

This is the multi-symbol counterpart of :class:`turtlex.strategy.trading.qullamaggie.QullamaggieStrategy`.
The production strategy loads one ticker per query because the runner walks the universe
ticker by ticker; the studies here load every ticker in one query so a parameter sweep can
re-filter an in-memory frame instead of re-querying. Both must produce identical signals —
``tests/research/test_qullamaggie_parity.py`` asserts that.

Every indicator is computed on shift-1 (prior-day) values so a filter only ever uses
information available at the prior close; the breakout and SMA-distance checks compare the
current adjusted close against them. Prices are split/dividend-adjusted; the absolute
price band stays on the raw close, because adjusting it would leak knowledge of splits that
had not happened yet as of the signal date.
"""

from datetime import date, timedelta

import polars as pl

from turtlex.repository.query.daily_bars import DailyBarsQueryRepository

# Filter thresholds — must stay in lockstep with QullamaggieStrategy's class attributes.
SMA_THRESH = 0.12
MIN_AVG_VOL = 100_000  # lowered from 500K on 2026-08-02; rationale on QullamaggieStrategy
MIN_PRICE = 5.0
MAX_PRICE = 250.0
COOLDOWN_DAYS = 30
VOL_SURGE_MAX = 2.0
ROC_CAP = 1.00
RSI_CAP = 70.0
ADR_MIN = 0.03
ADR_CHANGE_CAP = 0.90
MARKET_TICKER = "SPY.US"

# Windowing — mirrors QullamaggieStrategy's warmup_period / min_bars constructor defaults.
WARMUP_DAYS = 730
MIN_BARS = 300
MARKET_SMA_WARMUP_DAYS = 300

# Universe qualification — mirrors TickerQueryRepository.get_qullamaggie_qualified_symbols.
MIN_MARKET_CAP = 1_500_000_000
EXCLUDED_SECTORS = ("Communication Services", "Real Estate")

# Entry timing — a signal is entered on the next trading bar; if none appears within this
# many calendar days the signal is dropped. Mirrors SignalProcessor.calculate_entry_data.
ENTRY_SEARCH_DAYS = 7


def load_spy_regime(bars_history: DailyBarsQueryRepository, start_date: date, end_date: date) -> set[date]:
    """Load the set of dates on which SPY closed above its prior-day 200-day SMA.

    Args:
        bars_history: Repository for accessing historical bar data
        start_date: First date signals may be emitted for; SPY history is fetched
            far enough before this that its 200-day SMA is already warm
        end_date: Last date to load

    Returns:
        The dates satisfying the bull-market regime gate.
    """
    fetch_start = start_date - timedelta(days=WARMUP_DAYS + MARKET_SMA_WARMUP_DAYS)
    spy = bars_history.get_bars_pl(MARKET_TICKER, fetch_start, end_date)
    if spy.is_empty():
        return set()
    spy = spy.sort("date").with_columns(pl.col("close").shift(1).rolling_mean(200, min_samples=200).alias("sma200"))
    return set(spy.filter(pl.col("close") > pl.col("sma200"))["date"].to_list())


def load_bars(bars_history: DailyBarsQueryRepository, start_date: date, end_date: date) -> pl.DataFrame:
    """Load adjusted daily bars for the whole qualified universe in one query.

    Args:
        bars_history: Repository for accessing historical bar data
        start_date: First date signals may be emitted for; bars are fetched from
            ``WARMUP_DAYS`` before this so indicators are warm
        end_date: Last date to load

    Returns:
        Frame of symbol, date, raw_close, adj_open, adj_close, adj_high, adj_low, volume. A
        window the data does not cover yields those columns with no rows, not a column-less
        frame — studies walk fixed windows and can legitimately land on an empty one, and a
        caller that then filters on `date` must get an empty result rather than a
        `ColumnNotFoundError`.
    """
    fetch_start = start_date - timedelta(days=WARMUP_DAYS)
    df = bars_history.get_qualified_universe_bars_pl(
        fetch_start,
        end_date,
        min_market_cap=MIN_MARKET_CAP,
        excluded_sectors=list(EXCLUDED_SECTORS),
    )
    return prepare_bars(df.rename({"close": "raw_close"}))


def prepare_bars(df: pl.DataFrame) -> pl.DataFrame:
    """Drop unusable bars, adjust prices, and drop symbols with insufficient history.

    Bars with a non-positive close, adjusted close or zero volume go first — mirroring
    `QullamaggieStrategy.collect_data`, and for the same reason: keeping them skews the
    rolling volume averages. Dropping them before the `MIN_BARS` count also matches the
    strategy, which filters before its own row-count check.

    ``open``/``high``/``low`` are then scaled by ``adjusted_close / close`` so rolling
    indicators and trade returns are not corrupted by the price discontinuity a raw close
    shows on a split date. ``raw_close`` is kept unadjusted for the absolute price band,
    because adjusting it would leak knowledge of splits that had not happened yet.

    Split out from `load_bars` so tests can feed a synthetic frame through the same path.

    An empty input is not special-cased: every step below is a no-op on zero rows, so the
    result still carries the adj_* columns. Returning the frame untouched instead — as this did
    while `get_qualified_universe_bars_pl` answered with a column-less frame — hands the caller
    a different schema for the empty case than for every other, and the failure then surfaces
    several steps downstream as a missing column.

    Args:
        df: Frame with symbol, date, open, raw_close, adjusted_close, high, low, volume

    Returns:
        Frame with adj_open/adj_close/adj_high/adj_low added, unusable bars and
        short-history symbols removed.
    """
    df = df.filter((pl.col("raw_close") > 0) & (pl.col("adjusted_close") > 0) & (pl.col("volume") > 0))
    factor = pl.col("adjusted_close") / pl.col("raw_close")
    df = df.sort(["symbol", "date"]).with_columns(
        (pl.col("open") * factor).alias("adj_open"),
        pl.col("adjusted_close").alias("adj_close"),
        (pl.col("high") * factor).alias("adj_high"),
        (pl.col("low") * factor).alias("adj_low"),
    )
    return df.filter(pl.len().over("symbol") >= MIN_BARS)


def add_indicators(df: pl.DataFrame) -> pl.DataFrame:
    """Add the Qullamaggie filter indicators, grouped per symbol.

    Mirrors `QullamaggieStrategy.calculate_indicators_pl` exactly, with `.over("symbol")`
    added to every windowed expression.

    Args:
        df: Adjusted bar frame from `prepare_bars` / `load_bars`

    Returns:
        The frame with rsi14, sma50, avg_vol_10/20/50, max_c_50d, adr_pct,
        adr_pct_change, pct_vs_sma50 and roc_252d added. An empty input keeps that contract:
        every expression below is a no-op on zero rows, so the columns are added regardless.
    """
    df = df.sort(["symbol", "date"]).with_columns(
        pl.col("adj_close").shift(1).over("symbol").alias("_c1"),
        pl.col("volume").cast(pl.Float64).shift(1).over("symbol").alias("_v1"),
        ((pl.col("adj_high") - pl.col("adj_low")) / pl.col("adj_low")).shift(1).over("symbol").alias("_rp1"),
    )
    # RSI(14) on the prior-day close, simple rolling means (not Wilder smoothing)
    df = df.with_columns(pl.col("_c1").diff(1).over("symbol").alias("_diff"))
    df = df.with_columns(
        pl.when(pl.col("_diff") > 0).then(pl.col("_diff")).otherwise(0.0).alias("_gain"),
        pl.when(pl.col("_diff") < 0).then(-pl.col("_diff")).otherwise(0.0).alias("_loss"),
    )
    df = df.with_columns(
        pl.col("_gain").rolling_mean(14, min_samples=14).over("symbol").alias("_avg_gain"),
        pl.col("_loss").rolling_mean(14, min_samples=14).over("symbol").alias("_avg_loss"),
    )
    df = df.with_columns((100.0 - 100.0 / (1.0 + pl.col("_avg_gain") / pl.col("_avg_loss"))).alias("rsi14"))
    # Rolling averages and reference levels
    df = df.with_columns(
        pl.col("_c1").rolling_mean(50, min_samples=50).over("symbol").alias("sma50"),
        pl.col("_v1").rolling_mean(50, min_samples=50).over("symbol").alias("avg_vol_50"),
        pl.col("_v1").rolling_mean(20, min_samples=20).over("symbol").alias("avg_vol_20"),
        pl.col("_v1").rolling_mean(10, min_samples=10).over("symbol").alias("avg_vol_10"),
        pl.col("_c1").rolling_max(50, min_samples=50).over("symbol").alias("max_c_50d"),
        pl.col("_rp1").rolling_mean(20, min_samples=20).over("symbol").alias("adr_pct"),
        pl.col("_rp1").rolling_mean(10, min_samples=10).over("symbol").alias("_adr10"),
        pl.col("_rp1").rolling_mean(50, min_samples=50).over("symbol").alias("_adr50"),
        pl.col("_c1").shift(251).over("symbol").alias("_c_252d"),
    )
    df = df.with_columns(
        ((pl.col("adj_close") / pl.col("sma50")) - 1.0).alias("pct_vs_sma50"),
        (pl.col("_adr10") / pl.col("_adr50")).alias("adr_pct_change"),
        (pl.col("adj_close") / pl.col("_c_252d") - 1.0).alias("roc_252d"),
    )
    return df.drop(["_c1", "_v1", "_rp1", "_diff", "_gain", "_loss", "_avg_gain", "_avg_loss", "_adr10", "_adr50", "_c_252d"])


def get_signals(
    df: pl.DataFrame,
    bull_dates: set[date],
    start_date: date,
    sma_thresh: float = SMA_THRESH,
) -> pl.DataFrame:
    """Apply the breakout filters and the per-symbol cooldown.

    The cooldown chain runs over the **whole** frame including the warmup window, so a
    trigger just before `start_date` correctly suppresses an early in-range signal; only
    accepted triggers on or after `start_date` are returned.

    Args:
        df: Indicator frame from `add_indicators`
        bull_dates: Dates passing the SPY regime gate, from `load_spy_regime`
        start_date: Earliest date a signal may be emitted for
        sma_thresh: Minimum fraction the adjusted close must sit above the 50-day SMA

    Returns:
        Frame of surviving signals sorted by (date, symbol), carrying the indicator
        columns for downstream reporting.
    """
    if df.is_empty():
        return df
    candidates = df.filter(
        pl.col("sma50").is_not_null()
        & pl.col("max_c_50d").is_not_null()
        & pl.col("rsi14").is_not_null()
        & pl.col("roc_252d").is_not_null()
        & pl.col("adr_pct_change").is_not_null()
        & (pl.col("rsi14") < RSI_CAP)
        & (pl.col("raw_close") > MIN_PRICE)
        & (pl.col("raw_close") < MAX_PRICE)
        & (pl.col("avg_vol_20") >= MIN_AVG_VOL)
        & (pl.col("adr_pct") >= ADR_MIN)
        & (pl.col("adr_pct_change") < ADR_CHANGE_CAP)
        & (pl.col("adj_close") > pl.col("max_c_50d"))
        & (pl.col("pct_vs_sma50") >= sma_thresh)
        & (pl.col("volume").cast(pl.Float64) < VOL_SURGE_MAX * pl.col("avg_vol_50"))
        & (pl.col("roc_252d") < ROC_CAP)
        & pl.col("date").is_in(sorted(bull_dates))
    ).sort(["symbol", "date"])
    if candidates.is_empty():
        return candidates

    keep: list[bool] = []
    last_trigger: dict[str, date] = {}
    for symbol, day in zip(candidates["symbol"].to_list(), candidates["date"].to_list(), strict=True):
        prev = last_trigger.get(symbol)
        if prev is not None and (day - prev).days <= COOLDOWN_DAYS:
            keep.append(False)
            continue
        last_trigger[symbol] = day
        keep.append(day >= start_date)
    return candidates.filter(pl.Series(keep)).sort(["date", "symbol"])


def resolve_entries(signals: pl.DataFrame, bars: pl.DataFrame) -> pl.DataFrame:
    """Attach the next-trading-bar entry date and adjusted open price to each signal.

    Mirrors `SignalProcessor.calculate_entry_data`: the entry is the first bar strictly
    after the signal date and within `ENTRY_SEARCH_DAYS` calendar days. Signals with no
    such bar — typically the last few days of available data — are dropped, exactly as the
    production path drops them.

    Args:
        signals: Signal frame from `get_signals`
        bars: Adjusted bar frame covering the entry search window

    Returns:
        The signals with `entry_date` and `entry_price` added, signals lacking a next bar removed.
    """
    if signals.is_empty():
        return signals.with_columns(
            pl.Series("entry_date", [], dtype=pl.Date),
            pl.Series("entry_price", [], dtype=pl.Float64),
        )
    # Every signal date is itself a bar date, so the "first bar after the signal" is simply
    # that symbol's next row — no range search needed.
    lookup = bars.sort(["symbol", "date"]).select(
        "symbol",
        "date",
        pl.col("date").shift(-1).over("symbol").alias("entry_date"),
        pl.col("adj_open").shift(-1).over("symbol").alias("entry_price"),
    )
    matched = signals.join(lookup, on=["symbol", "date"], how="left")
    return matched.filter(
        pl.col("entry_date").is_not_null()
        & (pl.col("entry_price") > 0)
        & (pl.col("entry_date") <= pl.col("date") + pl.duration(days=ENTRY_SEARCH_DAYS))
    ).sort(["date", "symbol"])
