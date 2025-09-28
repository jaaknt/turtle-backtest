"""Portfolio backtesting service for executing and analyzing trading strategies."""

from datetime import datetime, timedelta
import logging
import csv
from pathlib import Path

from turtle.signal.base import TradingStrategy
from turtle.exit.base import ExitStrategy
from turtle.data.bars_history import BarsHistoryRepo
from turtle.signal.models import Signal
from turtle.common.enums import TimeFrameUnit
from turtle.backtest.processor import SignalProcessor
from turtle.backtest.models import FutureTrade
from turtle.portfolio.manager import PortfolioManager
from turtle.portfolio.selector import PortfolioSignalSelector
from turtle.portfolio.analytics import PortfolioAnalytics
from turtle.google.models import GoogleSheetsConfig
from turtle.google.signal_exporter import SignalExporter

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
        google_sheets_config: GoogleSheetsConfig | None = None,
    ):
        """
        Initialize portfolio service.

        Args:
            trading_strategy: Strategy for generating trading signals
            exit_strategy: Strategy for determining when to exit positions
            bars_history: Data repository for historical price data
            initial_capital: Starting capital amount
            position_min_amount: Minimum dollar amount per position
            position_max_amount: Maximum dollar amount per position
            min_signal_ranking: Minimum signal ranking to consider
            time_frame_unit: Time frame for analysis (DAY, WEEK, etc.)
            google_sheets_config: Optional Google Sheets configuration for signal export
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

        # Google Sheets export configuration
        self.google_sheets_config = google_sheets_config
        self.signal_exporter = SignalExporter(google_sheets_config, bars_history) if google_sheets_config else None

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
        # for trade in sorted(self.portfolio_manager.state.future_trades, key=lambda trade: trade.exit.date, reverse=True):
        #     print(
        #       f"Entry: {trade.entry.date.date()} @ ${trade.entry.price:.2f} Exit: {trade.exit.date.date()} "
        #       f"@ ${trade.exit.price:.2f} Size: {trade.position_size} "
        #       f"result: ${(trade.exit.price - trade.entry.price) * trade.position_size:.2f}"
        #     )

        # Save all trades to CSV in reports folder (sorted by exit date)
        self._save_trade_to_csv(self.portfolio_manager.state.future_trades)

        total_value = sum(
            (trade.exit.price - trade.entry.price) * trade.position_size for trade in self.portfolio_manager.state.future_trades
        )
        print(f"Trades PL: ${total_value:.2f} current snapshot total value: ${self.portfolio_manager.current_snapshot.total_value:.2f}")

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
        positions_to_process = list(self.portfolio_manager.current_snapshot.positions)
        logger.debug(f"processing {len(positions_to_process)} positions")

        for position in positions_to_process:
            # Check if this position's scheduled exit date matches current date
            if position.exit.date.date() <= current_date.date():
                logger.info(f"Exiting position for {position.ticker} on {position.exit.date.date()}")
                self.portfolio_manager.close_position(exit=position.exit, position_size=position.position_size)
            else:
                logger.debug(f"Holding position for {position.ticker}, scheduled exit on {position.exit.date.date()}")

        logger.info(f"positions after exits: {len(self.portfolio_manager.current_snapshot.positions)}")

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

        # Export signals to Google Sheets if configured
        if self.signal_exporter and qualified_signals:
            try:
                strategy_name = self.trading_strategy.__class__.__name__
                success = self.signal_exporter.export_daily_signals(qualified_signals, strategy_name, include_price_data=True)
                if success:
                    logger.info(f"Successfully exported {len(qualified_signals)} signals to Google Sheets")
                else:
                    logger.warning("Failed to export signals to Google Sheets")
            except Exception as e:
                logger.error(f"Error exporting signals to Google Sheets: {e}")

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

    def _save_trade_to_csv(self, trades: list[FutureTrade]) -> None:
        """
        Save all trades to CSV file in reports folder, sorted by exit date.

        Args:
            trades: List of FutureTrade objects containing trade details
        """
        try:
            if not trades:
                return

            # Create reports directory if it doesn't exist
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)

            # Generate filename based on strategy and date range
            strategy_name = self.trading_strategy.__class__.__name__
            start_str = self.start_date.strftime("%Y%m%d")
            end_str = self.end_date.strftime("%Y%m%d")
            filename = f"{strategy_name}_trades_{start_str}_{end_str}.csv"
            filepath = reports_dir / filename

            # Sort trades by exit date
            sorted_trades = sorted(trades, key=lambda trade: trade.exit.date)

            # Prepare all trade data
            all_trade_data = []
            for trade in sorted_trades:
                trade_data = {
                    "ticker": trade.ticker,
                    "entry_date": trade.entry.date.strftime("%Y-%m-%d %H:%M:%S"),
                    "entry_price": f"{trade.entry.price:.4f}",
                    "entry_reason": trade.entry.reason,
                    "exit_date": trade.exit.date.strftime("%Y-%m-%d %H:%M:%S"),
                    "exit_price": f"{trade.exit.price:.4f}",
                    "exit_reason": trade.exit.reason,
                    "position_size": f"{trade.position_size:.0f}",
                    "holding_days": trade.holding_days,
                    "realized_pnl": f"{trade.realized_pnl:.2f}",
                    "realized_pct": f"{trade.realized_pct:.2f}",
                    "signal_ranking": getattr(trade.signal, "ranking", "N/A"),
                    "signal_date": trade.signal.date.strftime("%Y-%m-%d %H:%M:%S") if hasattr(trade.signal, "date") else "N/A",
                }
                all_trade_data.append(trade_data)

            # Write all trades to CSV (replace file)
            with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
                if all_trade_data:
                    fieldnames = list(all_trade_data[0].keys())
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                    # Write header
                    writer.writeheader()

                    # Write all trade data
                    writer.writerows(all_trade_data)

                    logger.info(f"Saved {len(all_trade_data)} trades to CSV file: {filepath}")

        except Exception as e:
            logger.error(f"Error saving trades to CSV: {e}")
            # Don't raise the exception to avoid disrupting the main backtest process
