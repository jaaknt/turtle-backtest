"""Shared benchmark calculation utilities."""

import logging
from datetime import datetime
import pandas as pd

from turtle.data.bars_history import BarsHistoryRepo
from turtle.common.enums import TimeFrameUnit
from turtle.backtest.models import Benchmark

logger = logging.getLogger(__name__)


def calculate_benchmark_list(
    start_date: datetime,
    end_date: datetime,
    benchmark_tickers: list[str],
    bars_history: BarsHistoryRepo,
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
            df = bars_history.get_ticker_history(
                ticker, start_date, end_date, time_frame_unit
            )

            if not df.empty:
                benchmark = calculate_benchmark(df, ticker, start_date, end_date)
                if benchmark is not None:
                    benchmarks.append(benchmark)

        except Exception as e:
            logger.error(f"Error calculating benchmark return for {ticker}: {e}")
            continue

    return benchmarks


def calculate_benchmark(
    df: pd.DataFrame,
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
        if df.empty:
            logger.warning(f"No {ticker} data available for benchmark calculation")
            return None

        # Find entry price (open price on or after entry_date)
        entry_data = df[df.index == pd.Timestamp(entry_date)]

        if entry_data.empty:
            logger.warning(f"No {ticker} entry data available for {entry_date}")
            return None

        entry_price = float(entry_data.iloc[0]["open"])

        # Find exit price (close price on or closest to exit_date)
        exit_data = df[df.index == pd.Timestamp(exit_date)]

        if exit_data.empty:
            logger.warning(f"No {ticker} exit data available for {exit_date}")
            return None

        # Get last available date up to exit_date
        exit_price = float(exit_data.iloc[-1]["close"])

        if entry_price <= 0:
            logger.warning(f"Invalid {ticker} entry price: {entry_price}")
            return None

        return_pct = ((exit_price - entry_price) / entry_price) * 100.0
        return Benchmark(ticker=ticker, return_pct=return_pct, entry_date=entry_date, exit_date=exit_date)

    except Exception as e:
        logger.error(f"Error calculating {ticker} benchmark return: {e}")
        return None


