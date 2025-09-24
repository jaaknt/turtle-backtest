"""Signal selection and filtering for portfolio management."""

from __future__ import annotations

import logging
from datetime import datetime
from turtle.signal.models import Signal

logger = logging.getLogger(__name__)


class PortfolioSignalSelector:
    """
    Selects and filters trading signals for portfolio management.

    Responsible for choosing the best signals based on ranking, position limits,
    and diversification requirements.
    """

    def __init__(
        self,
        max_positions: int = 10,
        min_ranking: int = 70,
        max_sector_concentration: float = 0.4,
        exclude_existing_positions: bool = True,
    ):
        """
        Initialize signal selector with filtering parameters.

        Args:
            max_positions: Maximum number of positions to hold simultaneously
            min_ranking: Minimum signal ranking to consider (1-100 scale)
            max_sector_concentration: Maximum percentage of portfolio in single sector
            exclude_existing_positions: Whether to exclude signals for existing positions
        """
        self.max_positions = max_positions
        self.min_ranking = min_ranking
        self.max_sector_concentration = max_sector_concentration
        self.exclude_existing_positions = exclude_existing_positions

    def select_entry_signals(
        self,
        available_signals: list[Signal],
        current_positions: set[str],
        available_positions: int,
        current_date: datetime,
    ) -> list[Signal]:
        """
        Select the best entry signals for new positions.

        Args:
            available_signals: All signals generated for the current date
            current_positions: Set of tickers with existing positions
            available_positions: Number of new positions that can be opened
            current_date: Current backtest date

        Returns:
            List of selected signals for entry, limited by available_positions
        """
        logger.debug(
            f"Selecting entry signals for {current_date}: "
            f"{len(available_signals)} signals, {available_positions} slots available"
        )

        # Step 1: Filter by minimum ranking threshold
        qualified_signals = [
            signal for signal in available_signals
            if signal.ranking >= self.min_ranking
        ]

        logger.debug(f"After ranking filter (>={self.min_ranking}): {len(qualified_signals)} signals")

        # Step 2: Exclude existing positions if configured
        if self.exclude_existing_positions:
            qualified_signals = [
                signal for signal in qualified_signals
                if signal.ticker not in current_positions
            ]
            logger.debug(f"After position exclusion: {len(qualified_signals)} signals")

        # Step 3: Sort by ranking (highest first)
        qualified_signals.sort(key=lambda x: x.ranking, reverse=True)

        # Step 4: Select top signals up to available positions
        selected_signals = qualified_signals[:available_positions]

        logger.debug(
            f"Selected {len(selected_signals)} signals for entry: "
            f"{[f'{s.ticker}({s.ranking})' for s in selected_signals]}"
        )

        return selected_signals

    def filter_signals_by_quality(
        self,
        signals: list[Signal],
        min_ranking_threshold: int | None = None,
    ) -> list[Signal]:
        """
        Filter signals by quality criteria.

        Args:
            signals: Input signals to filter
            min_ranking_threshold: Override minimum ranking (optional)

        Returns:
            Filtered list of high-quality signals
        """
        threshold = min_ranking_threshold or self.min_ranking

        filtered_signals = [
            signal for signal in signals
            if signal.ranking >= threshold
        ]

        logger.debug(f"Quality filter: {len(signals)} -> {len(filtered_signals)} signals")
        return filtered_signals

    def rank_signals_by_strength(self, signals: list[Signal]) -> list[Signal]:
        """
        Sort signals by ranking strength (highest first).

        Args:
            signals: Input signals to rank

        Returns:
            Signals sorted by ranking in descending order
        """
        return sorted(signals, key=lambda x: x.ranking, reverse=True)

    def get_diversification_scores(
        self,
        signals: list[Signal],
        sector_info: dict[str, str] | None = None,
    ) -> dict[str, float]:
        """
        Calculate diversification scores for signal selection.

        This is a placeholder for future sector-based diversification logic.
        Currently returns uniform scores.

        Args:
            signals: Signals to score
            sector_info: Optional sector information for each ticker

        Returns:
            Dictionary mapping ticker to diversification score
        """
        # Placeholder implementation - could be enhanced with sector data
        return {signal.ticker: 1.0 for signal in signals}

    def apply_position_limits(
        self,
        signals: list[Signal],
        current_positions_count: int,
    ) -> list[Signal]:
        """
        Apply position count limits to signal selection.

        Args:
            signals: Input signals
            current_positions_count: Number of currently open positions

        Returns:
            Signals limited by available position slots
        """
        available_slots = max(0, self.max_positions - current_positions_count)
        limited_signals = signals[:available_slots]

        if len(signals) > available_slots:
            logger.debug(
                f"Position limit applied: {len(signals)} signals -> {len(limited_signals)} "
                f"(current: {current_positions_count}, max: {self.max_positions})"
            )

        return limited_signals

    def validate_signal_quality(self, signal: Signal) -> bool:
        """
        Validate individual signal meets quality criteria.

        Args:
            signal: Signal to validate

        Returns:
            True if signal meets quality standards
        """
        if signal.ranking < self.min_ranking:
            logger.debug(f"Signal {signal.ticker} rejected: ranking {signal.ranking} < {self.min_ranking}")
            return False

        if signal.ranking < 1 or signal.ranking > 100:
            logger.warning(f"Signal {signal.ticker} has invalid ranking: {signal.ranking}")
            return False

        return True
