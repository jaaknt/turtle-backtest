"""Live trading service that integrates portfolio backtesting with live execution."""

import logging
from datetime import datetime, timedelta
from typing import Any

from turtle.signal.base import TradingStrategy
from turtle.exit.base import ExitStrategy
from turtle.data.bars_history import BarsHistoryRepo
from turtle.common.enums import TimeFrameUnit
from turtle.trade.manager import LiveTradingManager
from turtle.trade.models import RiskParameters
from turtle.service.portfolio_service import PortfolioService

logger = logging.getLogger(__name__)


class LiveTradingService:
    """
    Service that bridges portfolio backtesting with live trading execution.

    Generates signals using the portfolio service and executes them using
    the live trading manager with comprehensive risk management.
    """

    def __init__(
        self,
        trading_strategy: TradingStrategy,
        exit_strategy: ExitStrategy,
        bars_history: BarsHistoryRepo,
        api_key: str,
        secret_key: str,
        risk_parameters: RiskParameters,
        db_dsn: str,
        paper_trading: bool = True,
        initial_capital: float = 30000.0,
        position_min_amount: float = 1500.0,
        position_max_amount: float = 3000.0,
        min_signal_ranking: int = 70,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
        universe: list[str] | None = None
    ):
        """
        Initialize live trading service.

        Args:
            trading_strategy: Strategy for generating trading signals
            exit_strategy: Strategy for determining when to exit positions
            bars_history: Data repository for historical price data
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            risk_parameters: Risk management parameters
            db_dsn: Database connection string
            paper_trading: Whether to use paper trading
            initial_capital: Starting capital amount
            position_min_amount: Minimum dollar amount per position
            position_max_amount: Maximum dollar amount per position
            min_signal_ranking: Minimum signal ranking to consider
            time_frame_unit: Time frame for analysis
            universe: List of symbols to trade
        """
        self.trading_strategy = trading_strategy
        self.exit_strategy = exit_strategy
        self.bars_history = bars_history
        self.time_frame_unit = time_frame_unit
        self.universe = universe or []

        # Initialize portfolio service for signal generation
        # Use current date for portfolio service
        current_date = datetime.now()
        lookback_days = 365  # One year lookback for strategy context

        self.portfolio_service = PortfolioService(
            trading_strategy=trading_strategy,
            exit_strategy=exit_strategy,
            bars_history=bars_history,
            start_date=current_date - timedelta(days=lookback_days),
            end_date=current_date,
            initial_capital=initial_capital,
            position_min_amount=position_min_amount,
            position_max_amount=position_max_amount,
            min_signal_ranking=min_signal_ranking,
            time_frame_unit=time_frame_unit
        )

        # Initialize live trading manager
        strategy_name = trading_strategy.__class__.__name__

        self.live_trading_manager = LiveTradingManager(
            api_key=api_key,
            secret_key=secret_key,
            strategy_name=strategy_name,
            risk_parameters=risk_parameters,
            db_dsn=db_dsn,
            paper_trading=paper_trading,
            universe=universe
        )

        logger.info(f"Live trading service initialized: {strategy_name} (paper: {paper_trading})")

    def start_live_trading(self) -> bool:
        """
        Start live trading session.

        Returns:
            True if session started successfully
        """
        try:
            # Start the live trading session
            success = self.live_trading_manager.start_session()

            if success:
                logger.info("Live trading session started successfully")

                # Generate initial signals for current market state
                self._generate_and_process_signals()

                return True
            else:
                logger.error("Failed to start live trading session")
                return False

        except Exception as e:
            logger.error(f"Error starting live trading: {e}")
            return False

    def stop_live_trading(self) -> bool:
        """
        Stop live trading session.

        Returns:
            True if session stopped successfully
        """
        try:
            success = self.live_trading_manager.stop_session()

            if success:
                logger.info("Live trading session stopped successfully")
                return True
            else:
                logger.error("Failed to stop live trading session")
                return False

        except Exception as e:
            logger.error(f"Error stopping live trading: {e}")
            return False

    def process_market_update(self) -> None:
        """Process market updates and manage positions."""
        try:
            # Update positions and orders
            self.live_trading_manager.update_positions_and_orders()

            # Generate new signals and process them
            self._generate_and_process_signals()

            logger.debug("Market update processed successfully")

        except Exception as e:
            logger.error(f"Error processing market update: {e}")

    def get_portfolio_status(self) -> dict:
        """
        Get comprehensive portfolio status.

        Returns:
            Dictionary with portfolio metrics and status
        """
        try:
            # Get live trading summary
            live_summary = self.live_trading_manager.get_portfolio_summary()

            # Get active positions
            positions = self.live_trading_manager.get_positions()

            # Get active orders
            orders = self.live_trading_manager.get_active_orders()

            # Calculate additional metrics
            position_count = len(positions)
            order_count = len(orders)

            total_position_value = sum(
                float(pos.market_value) for pos in positions
            )

            total_unrealized_pnl = sum(
                float(pos.unrealized_pnl) for pos in positions
            )

            return {
                "timestamp": datetime.now(),
                "live_summary": live_summary,
                "metrics": {
                    "position_count": position_count,
                    "order_count": order_count,
                    "total_position_value": total_position_value,
                    "total_unrealized_pnl": total_unrealized_pnl
                },
                "positions": [
                    {
                        "ticker": pos.ticker,
                        "quantity": pos.quantity,
                        "avg_price": float(pos.avg_price),
                        "market_price": float(pos.market_price),
                        "market_value": float(pos.market_value),
                        "unrealized_pnl": float(pos.unrealized_pnl),
                        "pnl_percentage": pos.pnl_percentage,
                        "entry_date": pos.entry_date
                    }
                    for pos in positions
                ],
                "orders": [
                    {
                        "id": order.id,
                        "ticker": order.ticker,
                        "side": order.side.value,
                        "type": order.order_type.value,
                        "quantity": order.quantity,
                        "price": float(order.price) if order.price else None,
                        "status": order.status.value,
                        "created_at": order.created_at
                    }
                    for order in orders
                ]
            }

        except Exception as e:
            logger.error(f"Error getting portfolio status: {e}")
            return {"error": str(e)}

    def manual_close_position(self, ticker: str, percentage: float | None = None) -> bool:
        """
        Manually close a position.

        Args:
            ticker: Stock symbol
            percentage: Percentage to close (None for 100%)

        Returns:
            True if close order submitted successfully
        """
        return self.live_trading_manager.close_position(ticker, percentage)

    def manual_cancel_order(self, order_id: str) -> bool:
        """
        Manually cancel an order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancellation successful
        """
        return self.live_trading_manager.cancel_order(order_id)

    def emergency_stop(self, reason: str) -> bool:
        """
        Execute emergency stop.

        Args:
            reason: Reason for emergency stop

        Returns:
            True if emergency stop executed successfully
        """
        return self.live_trading_manager.emergency_stop(reason)

    def get_session_performance(self) -> dict:
        """
        Get detailed session performance metrics.

        Returns:
            Dictionary with performance data
        """
        return self.live_trading_manager.get_session_performance()

    def _generate_and_process_signals(self) -> None:
        """Generate signals using portfolio service and process them for live trading."""
        try:
            current_date = datetime.now()

            # Generate signals using the portfolio service logic
            signals = self.portfolio_service._generate_entry_signals(current_date, self.universe)

            # Filter signals to avoid positions we already have
            existing_positions = self.live_trading_manager.get_positions()
            existing_tickers = {pos.ticker for pos in existing_positions}

            new_signals = [
                signal for signal in signals
                if signal.ticker not in existing_tickers
            ]

            # Process each signal for live trading
            for signal in new_signals:
                try:
                    # Process signal through live trading manager
                    order = self.live_trading_manager.process_signal(signal)

                    if order:
                        logger.info(f"Successfully processed signal for {signal.ticker}: order {order.id}")
                    else:
                        logger.debug(f"Signal for {signal.ticker} not processed (likely filtered by risk management)")

                except Exception as e:
                    logger.error(f"Error processing signal for {signal.ticker}: {e}")

            if new_signals:
                logger.info(f"Processed {len(new_signals)} new signals for live trading")

        except Exception as e:
            logger.error(f"Error generating and processing signals: {e}")

    def run_daily_signal_scan(self) -> dict:
        """
        Run daily signal scan and return results without executing trades.

        Useful for analysis and verification before live trading.

        Returns:
            Dictionary with scan results
        """
        try:
            current_date = datetime.now()

            # Generate signals
            signals = self.portfolio_service._generate_entry_signals(current_date, self.universe)

            # Get current positions for filtering
            existing_positions = self.live_trading_manager.get_positions()
            existing_tickers = {pos.ticker for pos in existing_positions}

            # Analyze signals
            new_signals = [s for s in signals if s.ticker not in existing_tickers]
            filtered_signals = [s for s in signals if s.ticker in existing_tickers]

            return {
                "scan_date": current_date,
                "total_signals": len(signals),
                "new_signals": len(new_signals),
                "filtered_signals": len(filtered_signals),
                "existing_positions": len(existing_positions),
                "signals": [
                    {
                        "ticker": signal.ticker,
                        "signal_type": getattr(signal, "signal_type", "unknown"),
                        "ranking": signal.ranking,
                        "price": getattr(signal, "price", None),
                        "date": signal.date,
                        "is_new": signal.ticker not in existing_tickers
                    }
                    for signal in signals
                ]
            }

        except Exception as e:
            logger.error(f"Error running daily signal scan: {e}")
            return {"error": str(e)}

    def validate_trading_setup(self) -> dict:
        """
        Validate trading setup and configuration.

        Returns:
            Dictionary with validation results
        """
        try:
            validation_results: dict[str, Any] = {
                "timestamp": datetime.now(),
                "overall_status": "valid",
                "checks": {}
            }

            # Check market status
            try:
                market_status = self.live_trading_manager.trading_client.get_market_status()
                validation_results["checks"]["market_status"] = {
                    "status": "pass",
                    "details": market_status
                }
            except Exception as e:
                validation_results["checks"]["market_status"] = {
                    "status": "fail",
                    "error": str(e)
                }
                validation_results["overall_status"] = "invalid"

            # Check account access
            try:
                account = self.live_trading_manager.trading_client.get_account()
                validation_results["checks"]["account_access"] = {
                    "status": "pass",
                    "details": {
                        "account_id": account.account_id,
                        "equity": float(account.equity),
                        "cash": float(account.cash),
                        "buying_power": float(account.buying_power)
                    }
                }
            except Exception as e:
                validation_results["checks"]["account_access"] = {
                    "status": "fail",
                    "error": str(e)
                }
                validation_results["overall_status"] = "invalid"

            # Check data availability
            try:
                current_date = datetime.now()
                test_ticker = self.universe[0] if self.universe else "AAPL"
                df = self.bars_history.get_ticker_history(
                    test_ticker,
                    current_date - timedelta(days=1),
                    current_date,
                    self.time_frame_unit
                )
                validation_results["checks"]["data_access"] = {
                    "status": "pass" if not df.empty else "warning",
                    "details": f"Tested {test_ticker}, got {len(df)} records"
                }
            except Exception as e:
                validation_results["checks"]["data_access"] = {
                    "status": "fail",
                    "error": str(e)
                }
                validation_results["overall_status"] = "invalid"

            # Check risk parameters
            try:
                risk_summary = self.live_trading_manager.risk_manager.get_risk_summary()
                validation_results["checks"]["risk_management"] = {
                    "status": "pass",
                    "details": risk_summary
                }
            except Exception as e:
                validation_results["checks"]["risk_management"] = {
                    "status": "fail",
                    "error": str(e)
                }
                validation_results["overall_status"] = "invalid"

            return validation_results

        except Exception as e:
            logger.error(f"Error validating trading setup: {e}")
            return {
                "timestamp": datetime.now(),
                "overall_status": "error",
                "error": str(e)
            }
