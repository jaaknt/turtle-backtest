"""Main portfolio backtesting engine."""

import logging
from datetime import datetime, timedelta

from turtle.backtest.models import Trade
from turtle.signal.base import TradingStrategy
from turtle.exit.base import ExitStrategy
from turtle.data.bars_history import BarsHistoryRepo
from turtle.common.enums import TimeFrameUnit
from turtle.signal.models import Signal
from turtle.backtest.processor import SignalProcessor

from .models import PortfolioResults
from .manager import PortfolioManager
from .selector import PortfolioSignalSelector
from .performance import PortfolioAnalytics

logger = logging.getLogger(__name__)


class PortfolioBacktester:
    """
    Main portfolio backtesting engine that orchestrates the entire process.

    Manages daily signal generation, position entry/exit, and performance tracking
    across a portfolio of stocks with fixed capital allocation.
    """

    def __init__(
        self,
        trading_strategy: TradingStrategy,
        exit_strategy: ExitStrategy,
        bars_history: BarsHistoryRepo,
        initial_capital: float = 10000.0,
        max_positions: int = 10,
        position_size: float = 1000.0,
        min_signal_ranking: int = 70,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
    ):
        """
        Initialize portfolio backtester.

        Args:
            trading_strategy: Strategy for generating trading signals
            exit_strategy: Strategy for determining when to exit positions
            bars_history: Data repository for historical price data
            initial_capital: Starting capital amount
            max_positions: Maximum number of simultaneous positions
            position_size: Target dollar amount per position
            min_signal_ranking: Minimum signal ranking to consider
            time_frame_unit: Time frame for analysis (DAY, WEEK, etc.)
        """
        self.trading_strategy = trading_strategy
        self.exit_strategy = exit_strategy
        self.bars_history = bars_history
        self.time_frame_unit = time_frame_unit

        # Initialize components
        self.portfolio_manager = PortfolioManager(
            initial_capital=initial_capital,
            position_size_amount=position_size,
        )

        self.signal_selector = PortfolioSignalSelector(
            max_positions=max_positions,
            min_ranking=min_signal_ranking,
        )

        self.analytics = PortfolioAnalytics()

        # Initialize signal processor for shared calculations
        self.signal_processor = SignalProcessor(
            max_holding_period=365,  # Configurable max holding period
            bars_history=bars_history,
            exit_strategy=exit_strategy,
            time_frame_unit=time_frame_unit,
        )

        # Backtest configuration
        self.max_positions = max_positions
        self.min_signal_ranking = min_signal_ranking

    def run_backtest(
        self,
        start_date: datetime,
        end_date: datetime,
        universe: list[str],
        benchmark_tickers: list[str] | None = None,
    ) -> PortfolioResults:
        """
        Execute complete portfolio backtest.

        Args:
            start_date: Backtest start date
            end_date: Backtest end date
            universe: List of stock tickers to consider
            benchmark_tickers: Optional benchmark tickers (e.g., ['SPY', 'QQQ'])

        Returns:
            PortfolioResults with complete backtest analysis
        """
        logger.info(f"Starting portfolio backtest: {start_date} to {end_date} ({len(universe)} stocks, max {self.max_positions} positions)")

        benchmark_tickers = benchmark_tickers or ["SPY", "QQQ"]
        current_date = start_date

        while current_date <= end_date:
            if current_date.weekday() < 5:  # Monday=0, Friday=4 (trading days only)
                self._process_trading_day(current_date, universe)

            current_date += timedelta(days=1)

        # Generate final results
        results = self._generate_results(start_date, end_date, benchmark_tickers)

        logger.info(
            f"Backtest completed: {results.total_trades} trades, {results.total_return_pct:.2f}% return, {results.win_rate:.1f}% win rate"
        )

        return results

    def _process_trading_day(self, current_date: datetime, universe: list[str]) -> None:
        """
        Process a single trading day: generate signals, manage positions, update portfolio.

        Args:
            current_date: Current trading date
            universe: Stock universe for signal generation
        """
        logger.debug(f"Processing trading day: {current_date}")

        # Step 1: Check exit conditions for existing positions
        exit_signals = self._evaluate_exit_conditions(current_date)
        self._process_exits(exit_signals, current_date)

        # Step 2: Generate new entry signals
        entry_signals = self._generate_entry_signals(current_date, universe)

        # Step 3: Select and process new entries
        selected_signals = self._select_entry_signals(entry_signals, current_date)
        self._process_entries(selected_signals, current_date)

        # Step 4: Update portfolio with current prices
        self._update_portfolio_prices(current_date, universe)

        # Step 5: Record daily snapshot
        self.portfolio_manager.record_daily_snapshot(current_date)

    def _evaluate_exit_conditions(self, current_date: datetime) -> list[dict[str, Trade]]:
        """
        Evaluate exit conditions for all current positions.

        Args:
            current_date: Current date

        Returns:
            List of exit signals with ticker and reason
        """
        return self.signal_processor.evaluate_exit_conditions(self.portfolio_manager.state.positions, current_date)

    def _process_exits(self, exit_signals: list[dict[str, Trade]], current_date: datetime) -> None:
        """
        Process position exits.

        Args:
            exit_signals: List of exit signals to process
            current_date: Current date
        """
        for exit_signal in exit_signals:
            self.portfolio_manager.close_position(
                ticker=exit_signal["ticker"],  # type: ignore
                exit_date=current_date,
                exit_price=exit_signal["exit_price"],  # type: ignore
                exit_reason=exit_signal["exit_reason"],  # type: ignore
            )

    def _generate_entry_signals(self, current_date: datetime, universe: list[str]) -> list[Signal]:
        """
        Generate trading signals for all stocks in universe.

        Args:
            current_date: Current date
            universe: Stock universe

        Returns:
            List of generated signals
        """
        all_signals = []

        for ticker in universe:
            try:
                # Generate signals for this ticker
                signals = self.trading_strategy.get_signals(ticker, current_date - timedelta(days=1), current_date)

                # Filter for signals on current date
                current_signals = [s for s in signals if s.date.date() == current_date.date()]
                all_signals.extend(current_signals)

            except Exception as e:
                logger.debug(f"Error generating signals for {ticker}: {e}")
                continue

        logger.debug(f"Generated {len(all_signals)} signals for {current_date}")
        return all_signals

    def _select_entry_signals(self, signals: list[Signal], current_date: datetime) -> list[Signal]:
        """
        Select best signals for new positions.

        Args:
            signals: Available signals
            current_date: Current date

        Returns:
            Selected signals for entry
        """
        current_positions = set(self.portfolio_manager.state.positions.keys())
        available_slots = self.portfolio_manager.get_available_position_slots(self.max_positions)

        selected_signals = self.signal_selector.select_entry_signals(signals, current_positions, available_slots, current_date)

        return selected_signals

    def _process_entries(self, signals: list[Signal], current_date: datetime) -> None:
        """
        Process new position entries.

        Args:
            signals: Signals to process for entry
            current_date: Current date
        """
        # Use signal processor to calculate entry data
        entry_data = self.signal_processor.calculate_batch_entry_data(signals)

        for signal in signals:
            entry_trade = entry_data.get(signal.ticker)
            if entry_trade is not None:
                self.portfolio_manager.open_position(signal, entry_trade.date, entry_trade.price)
            else:
                logger.warning(f"No entry data available for {signal.ticker}")
                continue

    def _update_portfolio_prices(self, current_date: datetime, universe: list[str]) -> None:
        """
        Update current prices for all portfolio positions.

        Args:
            current_date: Current date
            universe: Stock universe
        """
        if not self.portfolio_manager.state.positions:
            return

        price_data: dict[str, float] = {}

        for ticker in self.portfolio_manager.state.positions.keys():
            try:
                df = self.bars_history.get_ticker_history(ticker, current_date, current_date + timedelta(days=1), self.time_frame_unit)

                if not df.empty:
                    price_data[ticker] = float(df.iloc[0]["close"])

            except Exception as e:
                logger.debug(f"Error updating price for {ticker}: {e}")
                continue

        self.portfolio_manager.update_position_prices(price_data, current_date)

    def _generate_results(
        self,
        start_date: datetime,
        end_date: datetime,
        benchmark_tickers: list[str],
    ) -> PortfolioResults:
        """
        Generate comprehensive backtest results.

        Args:
            start_date: Backtest start date
            end_date: Backtest end date
            benchmark_tickers: Benchmark ticker symbols

        Returns:
            PortfolioResults with complete analysis
        """
        return self.analytics.generate_results(
            self.portfolio_manager.state,
            start_date,
            end_date,
            self.portfolio_manager.initial_capital,
            benchmark_tickers,
            self.bars_history,
        )
