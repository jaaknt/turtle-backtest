"""Portfolio backtesting service for executing and analyzing trading strategies."""

from datetime import datetime, timedelta
import logging

from turtle.signal.base import TradingStrategy
from turtle.exit.base import ExitStrategy
from turtle.data.bars_history import BarsHistoryRepo
from turtle.signal.models import Signal
from turtle.common.enums import TimeFrameUnit
from turtle.backtest.processor import SignalProcessor
from turtle.portfolio.manager import PortfolioManager
from turtle.portfolio.selector import PortfolioSignalSelector
from turtle.portfolio.analytics import PortfolioAnalytics

logger = logging.getLogger(__name__)


class PortfolioService:
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
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 30000.0,
        position_min_amount: float = 1500.0,
        position_max_amount: float = 3000.0,
        min_signal_ranking: int = 70,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
    ):
        """
        Initialize portfolio service.

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
        self.start_date = start_date
        self.end_date = end_date
        self.min_signal_ranking = min_signal_ranking

        # Initialize components
        self.portfolio_manager = PortfolioManager(
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            position_min_amount=position_min_amount,
            position_max_amount=position_max_amount,
        )

        self.signal_selector = PortfolioSignalSelector(
            min_ranking=min_signal_ranking,
        )

        self.analytics = PortfolioAnalytics()

        # Initialize signal processor for shared calculations
        self.signal_processor = SignalProcessor(
            max_holding_period=365,  # Configurable max holding period in days
            bars_history=bars_history,
            exit_strategy=exit_strategy,
            benchmark_tickers=[],  # Standard benchmarks, ignored in portfolio calculations
            time_frame_unit=time_frame_unit,
        )

        # Backtest configuration
        self.min_signal_ranking = min_signal_ranking

    def run_backtest(
        self,
        start_date: datetime,
        end_date: datetime,
        universe: list[str],
        output_file: str | None = None,
    ) -> None:
        """
        Execute complete portfolio backtest with printed results and tearsheet.

        Args:
            start_date: Backtest start date
            end_date: Backtest end date
            universe: List of stock tickers to consider
            output_file: Optional file path for HTML tearsheet output
        """
        logger.info(f"Starting portfolio backtest: {start_date.date()} to {end_date.date()} ({len(universe)} stocks)")

        current_date = start_date

        while current_date <= end_date:
            if current_date.weekday() < 5:  # Monday=0, Friday=4 (trading days only)
                self._process_trading_day(current_date, end_date, universe)

            current_date += timedelta(days=1)

        # Generate final results and display
        self._generate_results(output_file=output_file)
        for trade in self.portfolio_manager.state.future_trades:
            print(
                f"Entry: {trade.entry.date.date()} @ ${trade.entry.price} Exit: {trade.exit.date.date()} "
                f"@ ${trade.exit.price} Size: {trade.position_size} result: ${(trade.exit.price - trade.entry.price) * trade.position_size}"
            )

        total_value = sum(
            (trade.exit.price - trade.entry.price) * trade.position_size for trade in self.portfolio_manager.state.future_trades
        )
        print(f"Total portfolio value: ${total_value:.2f} cash: ${self.portfolio_manager.current_snapshot.cash:.2f}")

    def _process_trading_day(self, current_date: datetime, end_date: datetime, universe: list[str]) -> None:
        """
        Process a single trading day: generate signals, manage positions, update portfolio.

        Args:
            current_date: Current trading date
            universe: Stock universe for signal generation
        """

        # Step 1: Record daily snapshot
        self.portfolio_manager.record_daily_snapshot(current_date)

        logger.info(
            f"Processing trading day: {current_date.date()} Total value: ${self.portfolio_manager.current_snapshot.total_value:.2f}"
        )

        # Step 2: Process scheduled exits
        self._process_exits(current_date)

        # Step 3: Generate new entry signals
        if self.portfolio_manager.current_snapshot.cash >= self.portfolio_manager.position_min_amount and current_date < end_date:
            entry_signals = self._generate_entry_signals(current_date, universe)

            # Step 4: Select and process new entries
            self._process_signals(entry_signals, current_date, end_date)

        # Step 5: Update portfolio with current prices
        self._update_portfolio_prices(current_date)

    def _process_exits(self, current_date: datetime) -> None:
        """
        Process scheduled exits for current date using pre-calculated trade data.

        Args:
            current_date: Current trading date
        """

        for position in self.portfolio_manager.current_snapshot.positions:
            # Check if this position's scheduled exit date matches current date
            # print(f"Position: {position}")
            if position.exit.date.date() <= current_date.date():
                self.portfolio_manager.close_position(exit=position.exit, position_size=position.position_size)

    def _generate_entry_signals(self, current_date: datetime, universe: list[str]) -> list[Signal]:
        """
        Generate trading signals for all stocks in universe.

        Args:
            current_date: Current date
            universe: Stock universe

        Returns:
            List of generated signals
        """
        signals: list[Signal] = []
        qualified_signals: list[Signal] = []

        for ticker in universe:
            signals.extend(self.trading_strategy.get_signals(ticker, current_date, current_date))

        # Step 1: Filter by minimum ranking threshold
        qualified_signals = [
            signal
            for signal in signals
            if signal.ranking >= self.min_signal_ranking and signal.ticker not in self.portfolio_manager.current_snapshot.get_tickers()
        ]

        # order by ranking descending
        qualified_signals.sort(key=lambda s: s.ranking, reverse=True)

        logger.info(f"Generated {len(qualified_signals)} signals for {current_date}")
        return qualified_signals

    def _process_signals(self, signals: list[Signal], current_date: datetime, end_date: datetime) -> None:
        """
        Process new position entries using complete ClosedTrade calculations.

        Args:
            signals: Signals to process for entry
            current_date: Current date
        """
        for signal in signals:
            # Use signal processor to get complete trade data including exit
            future_trade = self.signal_processor.run(signal, end_date)
            if future_trade is None:
                logger.warning(f"No trade data available for {signal.ticker}")
                continue

            # calculate position size based on entry price and position sizing strategy
            position_size = self.portfolio_manager.calculate_position_size(future_trade.entry)
            future_trade.position_size = position_size
            if position_size == 0:
                logger.warning(f"Calculated zero shares for {signal.ticker} at price ${future_trade.entry.price}")
                continue
            # Add the closed trade to the portfolio state for tracking
            self.portfolio_manager.state.future_trades.append(future_trade)
            # Open the position in the portfolio
            self.portfolio_manager.open_position(future_trade.entry, future_trade.exit, position_size)

            logger.info(
                f"Opened position for {signal.ticker} on {future_trade.entry.date.date()}, "
                f"scheduled exit on {future_trade.exit.date.date()}"
            )
            if self.portfolio_manager.current_snapshot.cash < self.portfolio_manager.position_min_amount:
                break

    def _update_portfolio_prices(self, current_date: datetime) -> None:
        """
        Update current prices for all portfolio positions.

        Args:
            current_date: Current date
            universe: Stock universe
        """
        for position in self.portfolio_manager.current_snapshot.positions:
            try:
                df = self.bars_history.get_ticker_history(position.ticker, current_date, current_date, self.time_frame_unit)

                if not df.empty:
                    self.portfolio_manager.current_snapshot.update_position_price(position.ticker, float(df.iloc[0]["close"]))

            except Exception as e:
                logger.debug(f"Error updating price for {position.ticker}, date: {current_date} : {e}")
                continue

    def _generate_results(
        self,
        output_file: str | None = None,
    ) -> None:
        self.analytics.generate_results(
            self.portfolio_manager.state,
            self.start_date,
            self.end_date,
            self.bars_history,
            output_file=output_file,
        )
