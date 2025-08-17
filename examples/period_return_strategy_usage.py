#!/usr/bin/env python3
"""
Example demonstrating how to use StrategyPerformanceTester with different PeriodReturnStrategy classes.

This example shows how to:
1. Use the default BuyAndHoldStrategy
2. Use ProfitLossTargetStrategy with custom parameters
3. Use EMAExitStrategy with custom EMA period
4. Compare results between different strategies
"""

import pandas as pd
from datetime import datetime
from typing import List

from turtle.performance.strategy_performance import StrategyPerformanceTester
from turtle.performance.period_return import (
    BuyAndHoldStrategy, 
    ProfitLossTargetStrategy, 
    EMAExitStrategy
)


def example_usage():
    """Demonstrate different ways to use StrategyPerformanceTester with period return strategies."""
    
    print("🔸 StrategyPerformanceTester with PeriodReturnStrategy Examples")
    print("=" * 70)
    
    # Note: This is a conceptual example showing the API usage
    # In real usage, you would have actual TradingStrategy and BarsHistoryRepo instances
    
    # Example 1: Default BuyAndHoldStrategy
    print("\n1️⃣ Default Strategy (Buy and Hold)")
    print("-" * 40)
    
    """
    # Basic usage - defaults to BuyAndHoldStrategy
    tester_default = StrategyPerformanceTester(
        strategy=my_trading_strategy,
        bars_history=my_bars_history,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31),
        test_periods=[pd.Timedelta(days=7), pd.Timedelta(days=14), pd.Timedelta(days=30)]
    )
    """
    print("✅ Uses BuyAndHoldStrategy by default")
    print("✅ Holds positions until period end")
    print("✅ Backward compatible with existing code")
    
    # Example 2: ProfitLossTargetStrategy
    print("\n2️⃣ Profit/Loss Target Strategy")
    print("-" * 40)
    
    """
    # Using profit/loss targets
    profit_loss_strategy = ProfitLossTargetStrategy(
        profit_target=15.0,  # Take profit at 15% gain
        stop_loss=8.0        # Stop loss at 8% loss
    )
    
    tester_profit_loss = StrategyPerformanceTester(
        strategy=my_trading_strategy,
        bars_history=my_bars_history,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31),
        test_periods=[pd.Timedelta(days=7), pd.Timedelta(days=14), pd.Timedelta(days=30)],
        period_return_strategy=profit_loss_strategy
    )
    """
    print("✅ Exits at 15% profit OR 8% loss (whichever comes first)")
    print("✅ More realistic risk management")
    print("✅ Prevents large drawdowns")
    
    # Example 3: EMAExitStrategy
    print("\n3️⃣ EMA Exit Strategy")
    print("-" * 40)
    
    """
    # Using EMA-based exits
    ema_strategy = EMAExitStrategy(ema_period=20)
    
    tester_ema = StrategyPerformanceTester(
        strategy=my_trading_strategy,
        bars_history=my_bars_history,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31),
        test_periods=[pd.Timedelta(days=7), pd.Timedelta(days=14), pd.Timedelta(days=30)],
        period_return_strategy=ema_strategy
    )
    """
    print("✅ Exits when price closes below 20-day EMA")
    print("✅ Trend-following approach")
    print("✅ Protects against trend reversals")
    
    # Example 4: Custom parameters via kwargs
    print("\n4️⃣ Strategy with Custom Parameters")
    print("-" * 40)
    
    """
    # Passing strategy parameters via kwargs (for SignalResult fallback)
    tester_custom = StrategyPerformanceTester(
        strategy=my_trading_strategy,
        bars_history=my_bars_history,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31),
        test_periods=[pd.Timedelta(days=7), pd.Timedelta(days=14), pd.Timedelta(days=30)],
        period_return_strategy_kwargs={
            'profit_target': 20.0,
            'stop_loss': 5.0
        }
    )
    """
    print("✅ Flexible parameter passing")
    print("✅ Useful for strategy optimization")
    print("✅ Works with both new and legacy signal data")
    
    # Example 5: Comparing strategies
    print("\n5️⃣ Strategy Comparison")
    print("-" * 40)
    
    """
    # Run the same backtest with different strategies
    strategies_to_test = [
        ("Buy & Hold", BuyAndHoldStrategy()),
        ("Conservative P/L", ProfitLossTargetStrategy(profit_target=10.0, stop_loss=5.0)),
        ("Aggressive P/L", ProfitLossTargetStrategy(profit_target=25.0, stop_loss=15.0)),
        ("EMA-20 Exit", EMAExitStrategy(ema_period=20)),
        ("EMA-50 Exit", EMAExitStrategy(ema_period=50)),
    ]
    
    results = {}
    for name, strategy in strategies_to_test:
        tester = StrategyPerformanceTester(
            strategy=my_trading_strategy,
            bars_history=my_bars_history,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            test_periods=[pd.Timedelta(days=7), pd.Timedelta(days=14)],
            period_return_strategy=strategy
        )
        
        signals = tester.generate_signals(['AAPL', 'MSFT', 'GOOGL'])
        performance = tester.calculate_performance()
        results[name] = performance
    
    # Compare results
    for name, perf in results.items():
        avg_return_1w = perf.period_results['1W'].average_return
        win_rate_1w = perf.period_results['1W'].win_rate
        print(f"{name:15} | 1W Avg: {avg_return_1w:+6.2f}% | Win Rate: {win_rate_1w:5.1f}%")
    """
    print("✅ Easy strategy comparison")
    print("✅ Identify best risk/reward profiles")
    print("✅ Optimize strategy parameters")
    
    print("\n🎯 Key Benefits:")
    print("   • More realistic backtesting with proper exit strategies")
    print("   • Easy to extend with new exit strategies")
    print("   • Backward compatible with existing code")
    print("   • Flexible parameter configuration")
    print("   • Enables strategy optimization and comparison")


if __name__ == "__main__":
    example_usage()