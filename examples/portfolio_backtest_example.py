#!/usr/bin/env python3
"""
Portfolio Backtesting Example - TEMPLATE

NOTE: This is a template showing the API structure.
For a working example, use the Jupyter notebook: portfolio_backtesting.ipynb

This template demonstrates:
1. Setting up a portfolio backtester with 10 stock limit and $10K capital
2. Running backtest across a stock universe with signal ranking
3. Analyzing performance with quantstats-style metrics
4. Comparing against benchmarks (SPY, QQQ)

REQUIREMENTS:
- Database connection (PostgreSQL)
- Proper DataUpdateService initialization
- Trading strategy configuration
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime
import logging

from turtle.service.data_update_service import DataUpdateService
from turtle.common.enums import TimeFrameUnit
from turtle.portfolio import PortfolioBacktester, PortfolioAnalytics, PortfolioResults

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Main execution function."""
    logger.info("Starting Portfolio Backtesting Example")

    # Initialize data service (using existing pattern from notebook examples)
    data_service = DataUpdateService(time_frame_unit=TimeFrameUnit.DAY)

    # Define backtest parameters
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 8, 30)
    initial_capital = 10000.0
    max_positions = 10
    position_size = 1000.0
    min_signal_ranking = 70

    # Define stock universe - using a subset for this example
    # In practice, you might use data_service.get_symbol_group_list("NAS100") or similar
    universe = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'AVGO', 'NFLX', 'AMD',
        'CRM', 'ADBE', 'PYPL', 'INTC', 'CMCSA', 'PEP', 'COST', 'TMUS', 'AMGN', 'GILD',
        'MRNA', 'BKNG', 'ASML', 'AZN', 'TXN', 'QCOM', 'INTU', 'ISRG', 'AMAT', 'ADI'
    ]

    logger.info(f"Universe: {len(universe)} stocks")
    logger.info(f"Period: {start_date.date()} to {end_date.date()}")
    logger.info(f"Capital: ${initial_capital:,.0f}, Max Positions: {max_positions}")

    # Initialize exit strategy (you can experiment with different strategies)
    # Note: This is a placeholder - in practice, you'd need proper exit strategy initialization
    # For now, we'll comment this out as it requires proper setup
    # exit_strategy = ProfitLossExitStrategy(
    #     bars_history=data_service.bars_history
    # )
    # Using a simple mock for demonstration
    exit_strategy = None

    # Create portfolio backtester
    backtester = PortfolioBacktester(
        # trading_strategy=data_service.darvas_box_strategy,  # Or mars_strategy, momentum_strategy
        # Note: Using None for now as a placeholder - in practice use actual strategy
        trading_strategy=None,
        exit_strategy=exit_strategy,
        bars_history=data_service.bars_history,
        initial_capital=initial_capital,
        max_positions=max_positions,
        position_size=position_size,
        min_signal_ranking=min_signal_ranking,
        time_frame_unit=TimeFrameUnit.DAY,
    )

    try:
        # Run the backtest
        logger.info("Running portfolio backtest...")
        results = backtester.run_backtest(
            start_date=start_date,
            end_date=end_date,
            universe=universe,
            benchmark_tickers=['SPY', 'QQQ']
        )

        # Display results
        analytics = PortfolioAnalytics()
        analytics.print_performance_summary(results)

        # Print detailed trade analysis
        print_trade_analysis(results)

        # Print top performing stocks
        print_top_performers(results)

        logger.info("Portfolio backtest completed successfully")

    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        raise


def print_trade_analysis(results: PortfolioResults) -> None:
    """Print detailed trade analysis."""
    if not results.closed_positions:
        print("\nNo completed trades found.")
        return

    print(f"\n{'='*60}")
    print("DETAILED TRADE ANALYSIS")
    print(f"{'='*60}")

    # Group by ticker
    trades_by_ticker: dict[str, list] = {}
    for position in results.closed_positions:
        if position.ticker not in trades_by_ticker:
            trades_by_ticker[position.ticker] = []
        trades_by_ticker[position.ticker].append(position)

    # Print per-ticker summary
    print(f"{'Ticker':<8} {'Trades':<7} {'Win%':<6} {'Avg Return':<12} {'Total P&L':<12}")
    print("-" * 60)

    for ticker, positions in trades_by_ticker.items():
        total_trades = len(positions)
        winning_trades = len([p for p in positions if p.realized_pnl > 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

        avg_return = sum(p.realized_pct for p in positions) / total_trades
        total_pnl = sum(p.realized_pnl for p in positions)

        print(f"{ticker:<8} {total_trades:<7} {win_rate:<6.1f} {avg_return:<12.2f} ${total_pnl:<11.2f}")


def print_top_performers(results: PortfolioResults) -> None:
    """Print top and bottom performing trades."""
    if not results.closed_positions:
        return

    print(f"\n{'='*60}")
    print("TOP/BOTTOM PERFORMERS")
    print(f"{'='*60}")

    # Sort by realized P&L percentage
    sorted_positions = sorted(results.closed_positions, key=lambda x: x.realized_pct, reverse=True)

    print("\nTop 5 Winning Trades:")
    print(f"{'Ticker':<8} {'Entry':<12} {'Exit':<12} {'Return%':<10} {'P&L':<10} {'Days':<6}")
    print("-" * 60)

    for position in sorted_positions[:5]:
        print(
            f"{position.ticker:<8} "
            f"{position.entry_date.strftime('%Y-%m-%d'):<12} "
            f"{position.exit_date.strftime('%Y-%m-%d'):<12} "
            f"{position.realized_pct:<10.2f} "
            f"${position.realized_pnl:<9.2f} "
            f"{position.holding_period_days:<6}"
        )

    print("\nBottom 5 Losing Trades:")
    print(f"{'Ticker':<8} {'Entry':<12} {'Exit':<12} {'Return%':<10} {'P&L':<10} {'Days':<6}")
    print("-" * 60)

    for position in sorted_positions[-5:]:
        print(
            f"{position.ticker:<8} "
            f"{position.entry_date.strftime('%Y-%m-%d'):<12} "
            f"{position.exit_date.strftime('%Y-%m-%d'):<12} "
            f"{position.realized_pct:<10.2f} "
            f"${position.realized_pnl:<9.2f} "
            f"{position.holding_period_days:<6}"
        )


if __name__ == "__main__":
    main()
