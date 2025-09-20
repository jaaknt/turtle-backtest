# Portfolio Backtesting System

A comprehensive portfolio-based backtesting system for the Turtle Trading framework that enables testing trading strategies across multiple stocks with fixed capital allocation, signal ranking, and position management.

## 🎯 Key Features

- **Fixed Capital Management**: Start with configurable capital (default $10,000)
- **Signal-Based Selection**: Buy top-ranked stocks according to strategy signals
- **Position Limits**: Maintain maximum position count (default 10 stocks)
- **Dynamic Rebalancing**: Hold stocks until exit signals, then buy next best signals
- **Multiple Exit Strategies**: ATR, EMA, MACD, Profit/Loss stop strategies
- **Comprehensive Analytics**: Performance metrics, risk analysis, benchmark comparison
- **Quantstats Integration**: Professional-grade performance reporting

## 🏗️ Architecture

### Core Components

```
turtle/portfolio/
├── models.py           # Data models (Position, PortfolioState, PortfolioResults)
├── backtester.py       # Main PortfolioBacktester orchestrator
├── manager.py          # Portfolio position and cash management
├── selector.py         # Signal selection and filtering
├── performance.py      # Analytics and performance calculation
└── __init__.py         # Module exports

turtle/backtest/
└── portfolio_processor.py  # Multi-stock signal processing
```

### Data Flow

```
Daily Trading Loop:
1. Generate signals across stock universe
2. Rank and filter signals by quality/ranking
3. Evaluate exit conditions for current positions
4. Close positions triggering exit strategies
5. Select new positions from top-ranked signals
6. Update portfolio values and record snapshot
7. Calculate performance metrics
```

## 🚀 Quick Start

### Basic Usage

```python
from datetime import datetime
from turtle.service.data_update_service import DataUpdateService
from turtle.portfolio import PortfolioBacktester
from turtle.exit.atr import ATRExitStrategy
from turtle.common.enums import TimeFrameUnit

# Initialize data service
data_service = DataUpdateService(time_frame_unit=TimeFrameUnit.DAY)

# Configure backtest parameters
start_date = datetime(2023, 1, 1)
end_date = datetime(2024, 8, 30)
universe = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'AVGO']

# Create exit strategy
exit_strategy = ATRExitStrategy(
    bars_history=data_service.bars_history,
    time_frame_unit=TimeFrameUnit.DAY,
)

# Initialize portfolio backtester
backtester = PortfolioBacktester(
    trading_strategy=data_service.darvas_box_strategy,
    exit_strategy=exit_strategy,
    bars_history=data_service.bars_history,
    initial_capital=10000.0,
    max_positions=10,
    position_size=1000.0,
    min_signal_ranking=70,
)

# Run backtest
results = backtester.run_backtest(
    start_date=start_date,
    end_date=end_date,
    universe=universe,
    benchmark_tickers=['SPY', 'QQQ']
)

# Display results
from turtle.portfolio import PortfolioAnalytics
analytics = PortfolioAnalytics()
analytics.print_performance_summary(results)
```

### Interactive Notebook

Use the provided Jupyter notebook for interactive analysis:

```bash
uv run jupyter notebook examples/portfolio_backtesting.ipynb
```

### Command Line Example

Run the standalone example script:

```bash
uv run python examples/portfolio_backtest_example.py
```

## ⚙️ Configuration Options

### Portfolio Settings

```python
PortfolioBacktester(
    initial_capital=10000.0,     # Starting capital
    max_positions=10,            # Maximum simultaneous positions
    position_size=1000.0,        # Target $ amount per position
    min_signal_ranking=70,       # Minimum signal quality (1-100)
    time_frame_unit=TimeFrameUnit.DAY,
)
```

### Available Strategies

**Trading Strategies:**
- `darvas_box_strategy`: Trend-following based on Darvas Box theory
- `mars_strategy`: Mars momentum strategy (@marsrides)
- `momentum_strategy`: Traditional momentum indicators

**Exit Strategies:**
- `ATRExitStrategy`: Volatility-based stops using Average True Range
- `EMAExitStrategy`: Exponential moving average crossover exits
- `MACDExitStrategy`: MACD signal line crossover exits
- `ProfitLossExitStrategy`: Fixed profit target and stop loss exits

### Stock Universe Options

```python
# Use predefined symbol groups
symbol_group = data_service.symbol_group_repo.get_symbol_group_list('NAS100')
universe = [x.symbol for x in symbol_group]

# Custom universe
universe = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']

# Available groups: 'NAS100', 'DARVAS50', 'DARVAS100', 'DARVAS200', 'DARVAS500'
```

## 📊 Performance Metrics

The system provides comprehensive performance analytics:

### Portfolio Metrics
- Total return ($ and %)
- Maximum drawdown
- Sharpe ratio
- Volatility (annualized)
- Win rate and profit factor

### Trade Analysis
- Number of trades (winning/losing)
- Average win/loss percentages
- Average holding period
- Best/worst performing trades
- Performance by ticker
- Exit reason analysis

### Risk Analysis
- Maximum drawdown periods
- Daily return distribution
- Correlation with benchmarks
- Portfolio concentration metrics

### Benchmark Comparison
- SPY and QQQ relative performance
- Alpha and beta calculations
- Risk-adjusted returns

## 🧪 Testing

Run the test suite to validate functionality:

```bash
# Run portfolio-specific tests
uv run pytest tests/test_portfolio.py -v

# Run all tests
uv run pytest
```

## 📈 Advanced Usage

### Custom Signal Selection

```python
from turtle.portfolio import PortfolioSignalSelector

selector = PortfolioSignalSelector(
    max_positions=15,
    min_ranking=80,
    max_sector_concentration=0.3,  # Future enhancement
)
```

### Custom Position Sizing

```python
from turtle.portfolio import PortfolioManager

manager = PortfolioManager(
    initial_capital=25000.0,
    position_size_strategy="equal_weight",
    position_size_amount=2500.0,
    min_cash_reserve=1000.0,
)
```

### Performance Analytics

```python
from turtle.portfolio import PortfolioAnalytics

analytics = PortfolioAnalytics()

# Generate comprehensive results
results = analytics.generate_results(
    portfolio_state, start_date, end_date,
    initial_capital, ['SPY', 'QQQ'], bars_history
)

# Print detailed summary
analytics.print_performance_summary(results)

# Future: Create quantstats report
# report = analytics.create_quantstats_report(results)
```

## 🎯 Use Cases

### Strategy Development
- Test different signal generation strategies
- Optimize entry/exit parameters
- Compare strategy performance across time periods

### Risk Management
- Evaluate position sizing strategies
- Test different portfolio concentration limits
- Analyze drawdown characteristics

### Portfolio Optimization
- Find optimal number of positions
- Test different signal ranking thresholds
- Evaluate impact of minimum cash reserves

### Performance Attribution
- Identify top/bottom performing stocks
- Analyze sector allocation effects
- Compare exit strategy effectiveness

## 🔧 Extending the System

### Adding New Exit Strategies

```python
from turtle.exit.base import ExitStrategy

class CustomExitStrategy(ExitStrategy):
    def calculate_exit(self, data: pd.DataFrame) -> Trade:
        # Implement your custom exit logic
        pass
```

### Custom Performance Metrics

```python
from turtle.portfolio.performance import PortfolioAnalytics

class CustomAnalytics(PortfolioAnalytics):
    def calculate_custom_metrics(self, results):
        # Add your custom calculations
        pass
```

### Integration with External Data

```python
# Add external data sources for signal enhancement
# Implement sector classification for diversification
# Add fundamental data integration
```

## 🚧 Future Enhancements

### Planned Features
- [ ] Full quantstats integration
- [ ] Sector-based diversification constraints
- [ ] Position sizing based on volatility (ATR-based)
- [ ] Walk-forward analysis and out-of-sample testing
- [ ] Monte Carlo simulation for robustness testing
- [ ] Multi-timeframe strategy support
- [ ] Real-time portfolio monitoring dashboard

### Advanced Analytics
- [ ] Factor analysis and attribution
- [ ] Correlation-based position limits
- [ ] Dynamic position sizing algorithms
- [ ] Machine learning signal enhancement
- [ ] Options overlay strategies

## 📚 Examples and Tutorials

1. **Basic Portfolio Backtest**: `examples/portfolio_backtest_example.py`
2. **Interactive Analysis**: `examples/portfolio_backtesting.ipynb`
3. **Strategy Comparison**: Compare different strategies side-by-side
4. **Parameter Optimization**: Grid search for optimal parameters
5. **Risk Analysis**: Deep-dive into portfolio risk characteristics

## 🤝 Contributing

When adding new features:

1. Follow the existing class structure and design patterns
2. Add comprehensive tests for new functionality
3. Update documentation and examples
4. Ensure compatibility with existing strategies and data sources

## 📝 Notes

- The system is designed to work with existing Turtle Trading infrastructure
- All position management follows proper risk management principles
- Performance calculations use industry-standard methodologies
- The framework is extensible for custom strategies and analytics

---

This portfolio backtesting system transforms individual stock backtesting into comprehensive portfolio management with proper capital allocation, risk management, and performance analytics suitable for serious trading strategy development and validation.