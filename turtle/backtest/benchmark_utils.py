"""Shared benchmark calculation utilities."""

import logging
from datetime import datetime
import pandas as pd

from turtle.data.bars_history import BarsHistoryRepo
from turtle.common.enums import TimeFrameUnit

logger = logging.getLogger(__name__)


def calculate_benchmark_returns(
    start_date: datetime,
    end_date: datetime,
    benchmark_tickers: list[str],
    bars_history: BarsHistoryRepo,
    time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
) -> dict[str, float] | None:
    """
    Calculate benchmark returns for comparison.

    Args:
        start_date: Start date for benchmark calculation
        end_date: End date for benchmark calculation
        benchmark_tickers: List of benchmark ticker symbols
        bars_history: Data repository
        time_frame_unit: Time frame for data retrieval

    Returns:
        Dictionary mapping benchmark ticker to total return percentage
    """
    try:
        benchmark_returns = {}

        for ticker in benchmark_tickers:
            df = bars_history.get_ticker_history(
                ticker, start_date, end_date, time_frame_unit
            )

            if not df.empty:
                start_price = float(df.iloc[0]["open"])
                end_price = float(df.iloc[-1]["close"])
                total_return = ((end_price - start_price) / start_price) * 100.0
                benchmark_returns[ticker] = total_return

        return benchmark_returns

    except Exception as e:
        logger.error(f"Error calculating benchmark returns: {e}")
        return None


def calculate_single_benchmark_return(
    df: pd.DataFrame,
    symbol: str,
    entry_date: datetime,
    exit_date: datetime,
) -> float:
    """
    Calculate return for a single benchmark symbol.

    Args:
        df: DataFrame with benchmark data
        symbol: Symbol name for logging
        entry_date: Position entry date
        exit_date: Position exit date

    Returns:
        Percentage return, or 0.0 if calculation fails
    """
    try:
        if df.empty:
            logger.warning(f"No {symbol} data available for benchmark calculation")
            return 0.0

        # Find entry price (open price on or after entry_date)
        entry_data = df[df.index == pd.Timestamp(entry_date)]

        if entry_data.empty:
            logger.warning(f"No {symbol} entry data available for {entry_date}")
            return 0.0

        entry_price = float(entry_data.iloc[0]["open"])

        # Find exit price (close price on or closest to exit_date)
        exit_data = df[df.index == pd.Timestamp(exit_date)]

        if exit_data.empty:
            logger.warning(f"No {symbol} exit data available for {exit_date}")
            return 0.0

        # Get last available date up to exit_date
        exit_price = float(exit_data.iloc[-1]["close"])

        if entry_price <= 0:
            logger.warning(f"Invalid {symbol} entry price: {entry_price}")
            return 0.0

        return ((exit_price - entry_price) / entry_price) * 100.0

    except Exception as e:
        logger.error(f"Error calculating {symbol} benchmark return: {e}")
        return 0.0


def get_benchmark_data(
    bars_history: BarsHistoryRepo,
    benchmark_tickers: list[str],
    start_date: datetime,
    end_date: datetime,
    time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
) -> dict[str, pd.DataFrame]:
    """
    Pre-load benchmark data for efficient calculations.

    Args:
        bars_history: Data repository
        benchmark_tickers: List of benchmark tickers
        start_date: Data start date
        end_date: Data end date
        time_frame_unit: Time frame for data

    Returns:
        Dictionary mapping ticker to DataFrame
    """
    benchmark_data = {}

    for ticker in benchmark_tickers:
        try:
            df = bars_history.get_ticker_history(
                ticker, start_date, end_date, time_frame_unit
            )
            if not df.empty:
                benchmark_data[ticker] = df
                logger.debug(f"Loaded {ticker} data: {len(df)} records")

        except Exception as e:
            logger.error(f"Error loading benchmark data for {ticker}: {e}")
            continue

    return benchmark_data
