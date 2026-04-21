"""Shared benchmark calculation utilities."""

import logging
from datetime import datetime
from turtle.common.enums import TimeFrameUnit
from turtle.model import Benchmark
from turtle.repository.analytics import OhlcvAnalyticsRepository

import polars as pl

logger = logging.getLogger(__name__)


def calculate_benchmark_list(
    start_date: datetime,
    end_date: datetime,
    benchmark_tickers: list[str],
    bars_history: OhlcvAnalyticsRepository,
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

    start_d = start_date.date() if isinstance(start_date, datetime) else start_date
    end_d = end_date.date() if isinstance(end_date, datetime) else end_date

    for ticker in benchmark_tickers:
        try:
            df = bars_history.get_bars_pl(ticker, start_d, end_d, time_frame_unit)

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
    entry_date: datetime,
    exit_date: datetime,
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

        entry_d = entry_date.date() if isinstance(entry_date, datetime) else entry_date
        exit_d = exit_date.date() if isinstance(exit_date, datetime) else exit_date

        entry_data = df.filter(pl.col("date") >= entry_d)
        if entry_data.is_empty():
            logger.warning(f"No {ticker} entry data available on or after {entry_date}")
            return None

        exit_data = df.filter(pl.col("date") <= exit_d)
        if exit_data.is_empty():
            logger.warning(f"No {ticker} exit data available on or before {exit_date}")
            return None

        entry_price = float(entry_data["open"][0])
        exit_price = float(exit_data["close"][-1])

        if entry_price <= 0:
            logger.warning(f"Invalid {ticker} entry price: {entry_price}")
            return None

        return_pct = ((exit_price - entry_price) / entry_price) * 100.0
        return Benchmark(ticker=ticker, return_pct=return_pct, entry_date=entry_date, exit_date=exit_date)

    except Exception as e:
        logger.error(f"Error calculating {ticker} benchmark return: {e}")
        return None
