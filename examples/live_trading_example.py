"""
Live Trading Example

This example demonstrates how to use the live trading system to:
1. Set up a live trading environment
2. Configure risk parameters
3. Generate and execute trading signals
4. Monitor positions and performance
5. Handle emergency situations

IMPORTANT: This example uses paper trading by default.
Set paper_trading=False only when you're ready for live trading with real money.
"""

import os
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from turtle.signal.darvas_box import DarvasBoxStrategy
from turtle.exit.profit_loss import ProfitLossExitStrategy
from turtle.data.bars_history import BarsHistoryRepo
from psycopg_pool import ConnectionPool
from turtle.trade.models import RiskParameters
from turtle.service.live_trading_service import LiveTradingService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_environment() -> tuple[str, str, str]:
    """Set up environment variables and configuration."""
    # These should be set in your environment or .env file
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    db_dsn = os.getenv("DATABASE_DSN", "host=127.0.0.1 port=5432 dbname=postgres user=postgres password=postgres")

    if not api_key or not secret_key:
        raise ValueError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in environment")

    return api_key, secret_key, db_dsn


def create_trading_strategy(api_key: str, secret_key: str, db_dsn: str, pool: ConnectionPool) -> DarvasBoxStrategy:
    """Create and configure trading strategy."""
    # Import ranking strategy
    from turtle.ranking.volume_momentum import VolumeMomentumRanking

    # Use Darvas Box strategy for this example
    bars_history = BarsHistoryRepo(pool, api_key, secret_key)
    ranking_strategy = VolumeMomentumRanking()

    strategy = DarvasBoxStrategy(
        bars_history=bars_history,
        ranking_strategy=ranking_strategy
    )

    return strategy


def create_exit_strategy(bars_history: BarsHistoryRepo) -> ProfitLossExitStrategy:
    """Create and configure exit strategy."""
    # Use profit/loss exit strategy with stop loss and take profit
    # Note: ProfitLossExitStrategy parameters are set during initialize() call
    exit_strategy = ProfitLossExitStrategy(bars_history)

    return exit_strategy


def create_risk_parameters() -> RiskParameters:
    """Create and configure risk management parameters."""
    risk_params = RiskParameters(
        max_position_size=Decimal("5000"),      # Max $5,000 per position
        max_portfolio_exposure=0.80,            # Max 80% portfolio exposure
        max_daily_loss=Decimal("500"),          # Max $500 daily loss
        max_open_positions=8,                   # Max 8 open positions
        min_account_balance=Decimal("2000"),    # Min $2,000 account balance
        stop_loss_percentage=0.08,              # 8% stop loss trigger
        take_profit_percentage=0.20,            # 20% take profit trigger
        risk_per_trade=0.02                     # 2% risk per trade
    )

    return risk_params


def create_trading_universe() -> list[str]:
    """Create universe of stocks to trade."""
    # Example universe - adjust based on your strategy
    universe = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
        "NVDA", "META", "NFLX", "CRM", "ADBE",
        "PYPL", "INTC", "AMD", "ORCL", "CSCO",
        "IBM", "UBER", "LYFT", "SNAP", "TWTR"
    ]

    return universe


def main() -> None:
    """Main live trading example."""
    try:
        # Step 1: Set up environment
        logger.info("Setting up live trading environment...")
        api_key, secret_key, db_dsn = setup_environment()

        # Step 2: Create database connection pool
        from psycopg_pool import ConnectionPool
        pool = ConnectionPool(db_dsn)

        # Step 3: Initialize data repository
        bars_history = BarsHistoryRepo(pool, api_key, secret_key)

        # Step 4: Create trading components
        strategy = create_trading_strategy(api_key, secret_key, db_dsn, pool)
        exit_strategy = create_exit_strategy(bars_history)
        risk_params = create_risk_parameters()
        universe = create_trading_universe()

        # Step 5: Create live trading service
        logger.info("Initializing live trading service...")
        live_service = LiveTradingService(
            trading_strategy=strategy,
            exit_strategy=exit_strategy,
            bars_history=bars_history,
            api_key=api_key,
            secret_key=secret_key,
            risk_parameters=risk_params,
            db_dsn=db_dsn,
            paper_trading=True,  # IMPORTANT: Set to False for live trading
            initial_capital=25000.0,
            position_min_amount=1000.0,
            position_max_amount=5000.0,
            min_signal_ranking=75,
            universe=universe
        )

        # Step 6: Validate setup
        logger.info("Validating trading setup...")
        validation = live_service.validate_trading_setup()

        if validation["overall_status"] != "valid":
            logger.error(f"Trading setup validation failed: {validation}")
            return

        logger.info("Trading setup validation passed!")

        # Step 6: Run daily signal scan (dry run)
        logger.info("Running daily signal scan...")
        scan_results = live_service.run_daily_signal_scan()

        logger.info("Signal scan results:")
        logger.info(f"  Total signals: {scan_results.get('total_signals', 0)}")
        logger.info(f"  New signals: {scan_results.get('new_signals', 0)}")
        logger.info(f"  Existing positions: {scan_results.get('existing_positions', 0)}")

        # Display top signals
        signals = scan_results.get('signals', [])
        if signals:
            logger.info("Top 5 signals:")
            for signal in sorted(signals, key=lambda x: x['ranking'], reverse=True)[:5]:
                logger.info(f"  {signal['ticker']}: {signal['signal_type']} "
                          f"(ranking: {signal['ranking']}, price: ${signal['price']})")

        # Step 7: Start live trading session
        choice = input("\nStart live trading session? (y/N): ")
        if choice.lower() != 'y':
            logger.info("Live trading not started. Exiting.")
            return

        logger.info("Starting live trading session...")
        if not live_service.start_live_trading():
            logger.error("Failed to start live trading session")
            return

        logger.info("Live trading session started successfully!")

        # Step 8: Monitor trading session
        try:
            monitor_trading_session(live_service)
        finally:
            # Step 9: Stop trading session
            logger.info("Stopping live trading session...")
            live_service.stop_live_trading()
            logger.info("Live trading session stopped.")

    except Exception as e:
        logger.error(f"Error in live trading example: {e}")
        raise


def monitor_trading_session(live_service: LiveTradingService) -> None:
    """Monitor live trading session with periodic updates."""
    import time

    logger.info("Starting trading session monitoring...")
    logger.info("Commands: 'status', 'positions', 'orders', 'stop', 'emergency'")

    monitoring = True
    last_update = datetime.now()

    while monitoring:
        try:
            # Process market updates every 60 seconds
            if datetime.now() - last_update >= timedelta(seconds=60):
                logger.info("Processing market update...")
                live_service.process_market_update()
                last_update = datetime.now()

                # Display brief status
                status = live_service.get_portfolio_status()
                live_summary = status.get('live_summary', {})
                account = live_summary.get('account', {})
                performance = live_summary.get('performance', {})

                logger.info(f"Portfolio Value: ${account.get('portfolio_value', 0):.2f}, "
                          f"P&L: ${performance.get('total_pnl', 0):.2f}, "
                          f"Trades: {performance.get('total_trades', 0)}")

            # Check for user input (non-blocking)
            # In a real implementation, you might use a separate thread for user input
            # or integrate with a web interface

            time.sleep(5)  # Short sleep to prevent excessive CPU usage

        except KeyboardInterrupt:
            logger.info("Received interrupt signal. Stopping monitoring...")
            monitoring = False
        except Exception as e:
            logger.error(f"Error during monitoring: {e}")

            # Check if we should continue or stop
            choice = input("Continue monitoring? (Y/n): ")
            if choice.lower() == 'n':
                monitoring = False


def display_portfolio_status(live_service: LiveTradingService) -> None:
    """Display detailed portfolio status."""
    status = live_service.get_portfolio_status()

    print("\n" + "="*60)
    print("PORTFOLIO STATUS")
    print("="*60)

    # Session info
    session = status.get('live_summary', {}).get('session', {})
    print(f"Session ID: {session.get('id', 'N/A')}")
    print(f"Strategy: {session.get('strategy', 'N/A')}")
    print(f"Running: {session.get('is_running', False)}")
    print(f"Paper Trading: {session.get('paper_trading', True)}")

    # Account info
    account = status.get('live_summary', {}).get('account', {})
    print(f"\nAccount Equity: ${account.get('equity', 0):.2f}")
    print(f"Cash: ${account.get('cash', 0):.2f}")
    print(f"Buying Power: ${account.get('buying_power', 0):.2f}")

    # Positions
    positions = status.get('positions', [])
    if positions:
        print(f"\nPositions ({len(positions)}):")
        for pos in positions:
            print(f"  {pos['ticker']}: {pos['quantity']} shares @ ${pos['market_price']:.2f} "
                  f"(P&L: ${pos['unrealized_pnl']:.2f}, {pos['pnl_percentage']:.1f}%)")
    else:
        print("\nNo open positions")

    # Orders
    orders = status.get('orders', [])
    if orders:
        print(f"\nActive Orders ({len(orders)}):")
        for order in orders:
            print(f"  {order['ticker']}: {order['side']} {order['quantity']} @ "
                  f"{order.get('price', 'MARKET')} ({order['status']})")
    else:
        print("\nNo active orders")

    # Performance
    performance = status.get('live_summary', {}).get('performance', {})
    print("\nPerformance:")
    print(f"  Total Trades: {performance.get('total_trades', 0)}")
    print(f"  Win Rate: {performance.get('win_rate', 0):.1f}%")
    print(f"  Total P&L: ${performance.get('total_pnl', 0):.2f}")

    print("="*60 + "\n")


def emergency_stop_example(live_service: LiveTradingService) -> None:
    """Example of emergency stop functionality."""
    logger.warning("EMERGENCY STOP EXAMPLE")

    # In a real scenario, this might be triggered by:
    # - Market conditions
    # - System errors
    # - Risk threshold breaches
    # - External events

    reason = "Example emergency stop - market volatility detected"

    logger.critical(f"Executing emergency stop: {reason}")
    success = live_service.emergency_stop(reason)

    if success:
        logger.info("Emergency stop executed successfully")
    else:
        logger.error("Emergency stop failed")

    # Display final status
    display_portfolio_status(live_service)


if __name__ == "__main__":
    main()
