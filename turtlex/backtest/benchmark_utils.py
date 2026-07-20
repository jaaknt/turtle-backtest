"""Shared benchmark calculation utilities."""

import logging
from datetime import date

import polars as pl

from turtlex.common.enums import TimeFrameUnit
from turtlex.model import Benchmark
from turtlex.repository.query.daily_bars import DailyBarsQueryRepository

logger = logging.getLogger(__name__)


def calculate_benchmark_list(
    start_date: date,
    end_date: date,
    benchmark_tickers: list[str],
    bars_history: DailyBarsQueryRepository,
    time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
) -> list[Benchmark]:
    """
    Calculate benchmark returns for comparison.

    Args:
        start_date: Start date for benchmark calculation
        end_date: End date for benchmark calculation
        benchmark_tickers: List of benchmark ticker symbols
        bars_history: Data repository
        time_frame_unit: Time frame for data retrieval

    Returns:
        List of Benchmark objects with ticker and return percentages
    """
    benchmarks = []

    for ticker in benchmark_tickers:
        try:
            df = bars_history.get_bars_pl(ticker, start_date, end_date, time_frame_unit)

            if not df.is_empty():
                benchmark = calculate_benchmark(df, ticker, start_date, end_date)
                if benchmark is not None:
                    benchmarks.append(benchmark)

        except Exception as e:
            logger.error(f"Error calculating benchmark return for {ticker}: {e}")
            continue

    return benchmarks


def calculate_benchmark(
    df: pl.DataFrame,
    ticker: str,
    entry_date: date,
    exit_date: date,
) -> Benchmark | None:
    """
    Calculate benchmark for a single benchmark ticker.

    Args:
        df: DataFrame with benchmark data
        ticker: Ticker symbol for logging
        entry_date: Position entry date
        exit_date: Position exit date

    Returns:
        Benchmark with ticker and percentage return, or None if calculation fails
    """
    try:
        if df.is_empty():
            logger.warning(f"No {ticker} data available for benchmark calculation")
            return None

        entry_data = df.filter(pl.col("date") >= entry_date)
        if entry_data.is_empty():
            logger.warning(f"No {ticker} entry data available on or after {entry_date}")
            return None

        exit_data = df.filter(pl.col("date") <= exit_date)
        if exit_data.is_empty():
            logger.warning(f"No {ticker} exit data available on or before {exit_date}")
            return None

        entry_price_raw = entry_data["open"][0]
        exit_price_raw = exit_data["close"][-1]
        if entry_price_raw is None:
            logger.warning(f"Null {ticker} open price on entry")
            return None
        if exit_price_raw is None:
            logger.warning(f"Null {ticker} close price on exit")
            return None
        entry_price = float(entry_price_raw)
        exit_price = float(exit_price_raw)

        if entry_price <= 0:
            logger.warning(f"Invalid {ticker} entry price: {entry_price}")
            return None

        return_pct = ((exit_price - entry_price) / entry_price) * 100.0
        return Benchmark(ticker=ticker, return_pct=return_pct, entry_date=entry_date, exit_date=exit_date)

    except Exception as e:
        logger.error(f"Error calculating {ticker} benchmark return: {e}")
        return None
