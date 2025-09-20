"""Portfolio-aware signal processing for multi-stock backtesting."""

import logging
from datetime import datetime, timedelta

from turtle.signal.base import TradingStrategy
from turtle.signal.models import Signal
from turtle.data.bars_history import BarsHistoryRepo
from turtle.common.enums import TimeFrameUnit

logger = logging.getLogger(__name__)


class PortfolioSignalProcessor:
    """
    Portfolio-aware signal processor that generates signals across multiple stocks
    and coordinates with portfolio constraints.

    Extends the individual signal processing capabilities to handle portfolio-level
    signal generation and ranking across multiple stocks simultaneously.
    """

    def __init__(
        self,
        trading_strategy: TradingStrategy,
        bars_history: BarsHistoryRepo,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
        batch_size: int = 50,
    ):
        """
        Initialize portfolio signal processor.

        Args:
            trading_strategy: Strategy for generating trading signals
            bars_history: Data repository for historical price data
            time_frame_unit: Time frame for analysis
            batch_size: Number of stocks to process in each batch for efficiency
        """
        self.trading_strategy = trading_strategy
        self.bars_history = bars_history
        self.time_frame_unit = time_frame_unit
        self.batch_size = batch_size

    def generate_universe_signals(
        self,
        date: datetime,
        universe: list[str],
        exclude_tickers: set[str] | None = None,
        min_ranking: int = 50,
    ) -> list[Signal]:
        """
        Generate signals for entire stock universe on a specific date.

        Args:
            date: Date to generate signals for
            universe: List of stock tickers to analyze
            exclude_tickers: Set of tickers to exclude from analysis
            min_ranking: Minimum ranking threshold for signal inclusion

        Returns:
            List of qualified signals sorted by ranking (descending)
        """
        logger.debug(f"Generating universe signals for {len(universe)} stocks on {date}")

        exclude_tickers = exclude_tickers or set()
        eligible_universe = [ticker for ticker in universe if ticker not in exclude_tickers]

        all_signals = []

        # Process universe in batches for efficiency
        for i in range(0, len(eligible_universe), self.batch_size):
            batch = eligible_universe[i:i + self.batch_size]
            batch_signals = self._process_ticker_batch(date, batch)
            all_signals.extend(batch_signals)

        # Filter by minimum ranking
        qualified_signals = [s for s in all_signals if s.ranking >= min_ranking]

        # Sort by ranking (highest first)
        qualified_signals.sort(key=lambda x: x.ranking, reverse=True)

        logger.debug(
            f"Generated {len(all_signals)} total signals, "
            f"{len(qualified_signals)} above ranking {min_ranking}"
        )

        return qualified_signals

    def _process_ticker_batch(self, date: datetime, tickers: list[str]) -> list[Signal]:
        """
        Process a batch of tickers for signal generation.

        Args:
            date: Date to generate signals for
            tickers: List of tickers in this batch

        Returns:
            List of signals generated for the batch
        """
        batch_signals = []

        for ticker in tickers:
            try:
                # Generate signals for single ticker
                ticker_signals = self._generate_ticker_signals(ticker, date)
                batch_signals.extend(ticker_signals)

            except Exception as e:
                logger.debug(f"Error processing {ticker}: {e}")
                continue

        return batch_signals

    def _generate_ticker_signals(self, ticker: str, date: datetime) -> list[Signal]:
        """
        Generate signals for a single ticker.

        Args:
            ticker: Stock ticker symbol
            date: Date to generate signals for

        Returns:
            List of signals for the ticker
        """
        try:
            # Get signals from trading strategy
            signals = self.trading_strategy.get_signals(
                ticker,
                date - timedelta(days=1),  # Look back one day for signal generation
                date
            )

            # Filter for signals on target date
            target_signals = [s for s in signals if s.date.date() == date.date()]

            return target_signals

        except Exception as e:
            logger.debug(f"Error generating signals for {ticker} on {date}: {e}")
            return []

    def rank_signals_cross_sectional(
        self,
        signals: list[Signal],
        ranking_method: str = "percentile",
    ) -> list[Signal]:
        """
        Apply cross-sectional ranking to signals.

        Re-ranks signals relative to each other rather than using individual rankings.

        Args:
            signals: List of signals to re-rank
            ranking_method: Method for cross-sectional ranking

        Returns:
            Signals with updated cross-sectional rankings
        """
        if not signals:
            return signals

        if ranking_method == "percentile":
            # Sort by original ranking
            sorted_signals = sorted(signals, key=lambda x: x.ranking, reverse=True)

            # Assign percentile-based rankings
            for i, signal in enumerate(sorted_signals):
                percentile_rank = int(((len(sorted_signals) - i) / len(sorted_signals)) * 100)
                signal.ranking = max(1, min(100, percentile_rank))

            return sorted_signals

        else:
            # Default: return signals sorted by original ranking
            return sorted(signals, key=lambda x: x.ranking, reverse=True)

    def filter_signals_by_data_quality(
        self,
        signals: list[Signal],
        min_volume: float = 100000,
        min_price: float = 5.0,
    ) -> list[Signal]:
        """
        Filter signals based on data quality criteria.

        Args:
            signals: Input signals to filter
            min_volume: Minimum average daily volume
            min_price: Minimum stock price

        Returns:
            Filtered signals meeting quality criteria
        """
        filtered_signals = []

        for signal in signals:
            try:
                # Get recent price data for quality check
                end_date = signal.date + timedelta(days=1)
                start_date = signal.date - timedelta(days=5)

                df = self.bars_history.get_ticker_history(
                    signal.ticker, start_date, end_date, self.time_frame_unit
                )

                if df.empty:
                    continue

                # Check volume and price criteria
                avg_volume = df["volume"].mean()
                current_price = float(df.iloc[-1]["close"])

                if avg_volume >= min_volume and current_price >= min_price:
                    filtered_signals.append(signal)

            except Exception as e:
                logger.debug(f"Error checking data quality for {signal.ticker}: {e}")
                continue

        logger.debug(
            f"Data quality filter: {len(signals)} -> {len(filtered_signals)} signals "
            f"(min_volume: {min_volume}, min_price: ${min_price})"
        )

        return filtered_signals

    def get_signal_universe_statistics(
        self,
        signals: list[Signal],
        universe: list[str],
    ) -> dict[str, int | float | dict[str, int]]:
        """
        Calculate statistics about signal generation across universe.

        Args:
            signals: Generated signals
            universe: Original universe of stocks

        Returns:
            Dictionary with universe statistics
        """
        if not signals:
            return {
                "total_universe": len(universe),
                "signals_generated": 0,
                "signal_coverage_pct": 0.0,
                "avg_ranking": 0.0,
                "top_quartile_count": 0,
                "rankings_distribution": {},
            }

        unique_tickers = {s.ticker for s in signals}
        signal_coverage_pct = (len(unique_tickers) / len(universe)) * 100.0

        rankings = [s.ranking for s in signals]
        avg_ranking = sum(rankings) / len(rankings)
        top_quartile_count = len([r for r in rankings if r >= 75])

        # Rankings distribution
        distribution = {
            "90-100": len([r for r in rankings if 90 <= r <= 100]),
            "80-89": len([r for r in rankings if 80 <= r < 90]),
            "70-79": len([r for r in rankings if 70 <= r < 80]),
            "60-69": len([r for r in rankings if 60 <= r < 70]),
            "50-59": len([r for r in rankings if 50 <= r < 60]),
            "below-50": len([r for r in rankings if r < 50]),
        }

        return {
            "total_universe": len(universe),
            "signals_generated": len(signals),
            "unique_tickers": len(unique_tickers),
            "signal_coverage_pct": signal_coverage_pct,
            "avg_ranking": avg_ranking,
            "top_quartile_count": top_quartile_count,
            "rankings_distribution": distribution,
        }

    def validate_signal_data_availability(
        self,
        signals: list[Signal],
        required_days_ahead: int = 5,
    ) -> list[Signal]:
        """
        Validate that required price data is available for signal processing.

        Args:
            signals: Signals to validate
            required_days_ahead: Number of future days of data required

        Returns:
            Valid signals with sufficient data availability
        """
        validated_signals = []

        for signal in signals:
            try:
                end_date = signal.date + timedelta(days=required_days_ahead)

                df = self.bars_history.get_ticker_history(
                    signal.ticker, signal.date, end_date, self.time_frame_unit
                )

                # Check if we have sufficient future data
                if not df.empty and len(df) >= required_days_ahead:
                    validated_signals.append(signal)

            except Exception as e:
                logger.debug(f"Data validation failed for {signal.ticker}: {e}")
                continue

        logger.debug(
            f"Data validation: {len(signals)} -> {len(validated_signals)} signals "
            f"with {required_days_ahead} days of future data"
        )

        return validated_signals
