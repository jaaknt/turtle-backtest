#!/usr/bin/env python3
import logging
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


from turtle.portfolio.models import PortfolioState # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Main execution function."""
    logger.info("Starting Portfolio Backtesting Example")

    # Note: This example is a template - it requires proper database setup
    # For working examples, use the portfolio_backtesting.ipynb notebook
    logger.warning("This is a template file. Use portfolio_backtesting.ipynb for working examples.")
    return

    # Initialize data service (requires proper pool and app_config setup)
    # data_service = DataUpdateService(pool, app_config, time_frame_unit=TimeFrameUnit.DAY)

    # Define backtest parameters
    # start_date = datetime(2023, 1, 1)
    # end_date = datetime(2024, 8, 30)
    # initial_capital = 10000.0
    # max_positions = 10
    # position_size = 1000.0
    # min_signal_ranking = 70

    # Define stock universe - using a subset for this example
    # In practice, you might use data_service.get_symbol_group_list("NAS100") or similar
    # universe = [
    #     'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'AVGO', 'NFLX', 'AMD',
    #     'CRM', 'ADBE', 'PYPL', 'INTC', 'CMCSA', 'PEP', 'COST', 'TMUS', 'AMGN', 'GILD',
    #     'MRNA', 'BKNG', 'ASML', 'AZN', 'TXN', 'QCOM', 'INTU', 'ISRG', 'AMAT', 'ADI'
    # ]

    # logger.info(f"Universe: {len(universe)} stocks")
    # logger.info(f"Period: {start_date.date()} to {end_date.date()}")
    # logger.info(f"Capital: ${initial_capital:,.0f}, Max Positions: {max_positions}")

    # Initialize exit strategy (you can experiment with different strategies)
    # Note: This is a placeholder - in practice, you'd need proper exit strategy initialization
    # For now, we'll comment this out as it requires proper setup
    # exit_strategy = ProfitLossExitStrategy(
    #     bars_history=data_service.bars_history
    # )
    # Using a simple mock for demonstration
    # exit_strategy = None

    # Create portfolio service (requires proper strategy setup)
    # portfolio_service = PortfolioService(
    #     trading_strategy=data_service.darvas_box_strategy,
    #     exit_strategy=exit_strategy,
    #     bars_history=data_service.bars_history,
    #     start_date=start_date,
    #     end_date=end_date,
    #     initial_capital=initial_capital,
    #     position_min_amount=position_size,
    #     position_max_amount=position_size * 2,
    #     min_signal_ranking=min_signal_ranking,
    #     time_frame_unit=TimeFrameUnit.DAY,
    # )

    # Note: Template code - actual implementation would be:
    # try:
    #     # Run the backtest
    #     logger.info("Running portfolio backtest...")
    #     portfolio_service.run_backtest(
    #         start_date=start_date,
    #         end_date=end_date,
    #         universe=universe,
    #     )
    #
    #     logger.info("Portfolio backtest completed successfully")
    #
    # except Exception as e:
    #     logger.error(f"Backtest failed: {e}")
    #     raise


def print_trade_analysis(results: PortfolioState) -> None:
    """Print detailed trade analysis."""
    if not results.future_trades:
        print("\nNo completed trades found.")
        return

    print(f"\n{'='*60}")
    print("DETAILED TRADE ANALYSIS")
    print(f"{'='*60}")

    # Group by ticker
    trades_by_ticker: dict[str, list] = {}
    for future_trade in results.future_trades:
        if future_trade.ticker not in trades_by_ticker:
            trades_by_ticker[future_trade.ticker] = []
        trades_by_ticker[future_trade.ticker].append(future_trade)

    # Print per-ticker summary
    print(f"{'Ticker':<8} {'Trades':<7} {'Win%':<6} {'Avg Return':<12} {'Total P&L':<12}")
    print("-" * 60)

    for ticker, trades in trades_by_ticker.items():
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.realized_pnl > 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

        avg_return = sum(t.realized_pct for t in trades) / total_trades
        total_pnl = sum(t.realized_pnl for t in trades)

        print(f"{ticker:<8} {total_trades:<7} {win_rate:<6.1f} {avg_return:<12.2f} ${total_pnl:<11.2f}")


def print_top_performers(results: PortfolioState) -> None:
    """Print top and bottom performing trades."""
    if not results.future_trades:
        return

    print(f"\n{'='*60}")
    print("TOP/BOTTOM PERFORMERS")
    print(f"{'='*60}")

    # Sort by realized P&L percentage
    sorted_trades = sorted(results.future_trades, key=lambda x: x.realized_pct, reverse=True)

    print("\nTop 5 Winning Trades:")
    print(f"{'Ticker':<8} {'Entry':<12} {'Exit':<12} {'Return%':<10} {'P&L':<10} {'Days':<6}")
    print("-" * 60)

    for trade in sorted_trades[:5]:
        print(
            f"{trade.ticker:<8} "
            f"{trade.entry.date.strftime('%Y-%m-%d'):<12} "
            f"{trade.exit.date.strftime('%Y-%m-%d'):<12} "
            f"{trade.realized_pct:<10.2f} "
            f"${trade.realized_pnl:<9.2f} "
            f"{trade.holding_days:<6}"
        )

    print("\nBottom 5 Losing Trades:")
    print(f"{'Ticker':<8} {'Entry':<12} {'Exit':<12} {'Return%':<10} {'P&L':<10} {'Days':<6}")
    print("-" * 60)

    for trade in sorted_trades[-5:]:
        print(
            f"{trade.ticker:<8} "
            f"{trade.entry.date.strftime('%Y-%m-%d'):<12} "
            f"{trade.exit.date.strftime('%Y-%m-%d'):<12} "
            f"{trade.realized_pct:<10.2f} "
            f"${trade.realized_pnl:<9.2f} "
            f"{trade.holding_days:<6}"
        )


if __name__ == "__main__":
    main()
