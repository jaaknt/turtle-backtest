# Live Trading System

This document describes the comprehensive live trading system that has been implemented for the turtle-backtest project.

## Overview

The live trading system provides a complete pipeline from signal generation to trade execution, with comprehensive risk management, position tracking, and audit trails. The system is designed to work with the existing backtesting framework while adding real-time trading capabilities through the Alpaca API.

## Architecture

### Core Components

The live trading system consists of several interconnected components:

#### 1. Data Models (`turtle/trade/models.py`)
- **LiveOrder**: Represents trading orders with full lifecycle tracking
- **LivePosition**: Tracks open positions with real-time P&L
- **TradingSession**: Manages trading session state and performance
- **RiskParameters**: Configurable risk management settings
- **ExecutionReport**: Detailed trade execution records
- **AccountInfo**: Trading account information and balances

#### 2. Alpaca Trading Client (`turtle/trade/client.py`)
- Wrapper around the Alpaca API with error handling
- Order submission, cancellation, and status updates
- Position and account information retrieval
- Market status and timing checks
- Automatic conversion between internal and Alpaca data formats

#### 3. Order Executor (`turtle/trade/order_executor.py`)
- Order lifecycle management with retry logic
- Support for market, limit, stop, and stop-limit orders
- Order monitoring and status updates
- Portfolio-level order tracking and statistics

#### 4. Position Tracker (`turtle/trade/position_tracker.py`)
- Real-time position monitoring and P&L calculation
- Execution processing and position updates
- Position closing and realized P&L calculation
- Market price updates and unrealized P&L tracking

#### 5. Risk Manager (`turtle/trade/risk_manager.py`)
- Comprehensive risk controls and safety measures
- Pre-trade risk validation (position size, portfolio exposure, etc.)
- Real-time position monitoring for stop-losses
- Emergency stop functionality
- Risk event logging and tracking

#### 6. Trade Logger (`turtle/trade/trade_logger.py`)
- Complete audit trail for all trading activities
- Database persistence for orders, positions, executions
- Risk event logging and session performance tracking
- Historical data retrieval and analysis

#### 7. Live Trading Manager (`turtle/trade/manager.py`)
- Main orchestration layer for live trading
- Session management and lifecycle control
- Signal processing and order execution
- Portfolio summary and status reporting

#### 8. Live Trading Service (`turtle/service/live_trading_service.py`)
- Integration layer between backtesting and live trading
- Signal generation using existing portfolio service
- Market update processing and position management
- Setup validation and configuration management

## Database Schema

The system extends the existing turtle schema with new tables:

- **live_orders**: Order tracking and history
- **live_positions**: Position tracking and P&L
- **trading_sessions**: Session management and performance
- **execution_reports**: Trade execution details
- **account_snapshots**: Account balance history
- **risk_events**: Risk management events and alerts

## Key Features

### Signal-to-Execution Pipeline
1. **Signal Generation**: Uses existing trading strategies to generate signals
2. **Risk Validation**: Pre-trade risk checks and position sizing
3. **Order Execution**: Automated order submission with retry logic
4. **Position Tracking**: Real-time monitoring and P&L calculation
5. **Risk Monitoring**: Continuous risk assessment and stop-loss triggers

### Risk Management
- **Position Limits**: Maximum position size and portfolio exposure
- **Daily Loss Limits**: Stop trading if daily losses exceed thresholds
- **Emergency Stop**: Complete trading halt with order cancellation
- **Stop Loss Orders**: Automatic position protection
- **Account Monitoring**: Minimum balance and buying power checks

### Audit and Compliance
- **Complete Audit Trail**: All orders, executions, and risk events logged
- **Session Tracking**: Performance metrics and trade statistics
- **Risk Event Logging**: Detailed risk management event history
- **Data Retention**: Configurable data cleanup and archival

## Usage

### Basic Setup

```python
from turtle.service.live_trading_service import LiveTradingService
from turtle.trade.models import RiskParameters
from turtle.signal.darvas_box import DarvasBoxStrategy
from turtle.exit.profit_loss import ProfitLossExitStrategy

# Configure risk parameters
risk_params = RiskParameters(
    max_position_size=Decimal("5000"),
    max_portfolio_exposure=0.80,
    max_daily_loss=Decimal("500"),
    stop_loss_percentage=0.08
)

# Initialize live trading service
live_service = LiveTradingService(
    trading_strategy=DarvasBoxStrategy(...),
    exit_strategy=ProfitLossExitStrategy(...),
    bars_history=BarsHistoryRepo(),
    api_key="your_alpaca_key",
    secret_key="your_alpaca_secret",
    risk_parameters=risk_params,
    db_dsn="your_database_connection",
    paper_trading=True  # Start with paper trading!
)

# Start trading
live_service.start_live_trading()

# Monitor and manage
status = live_service.get_portfolio_status()
live_service.process_market_update()
```

### Configuration Options

#### Risk Parameters
- `max_position_size`: Maximum dollar amount per position
- `max_portfolio_exposure`: Maximum portfolio exposure (0-1)
- `max_daily_loss`: Maximum daily loss limit
- `max_open_positions`: Maximum number of open positions
- `stop_loss_percentage`: Default stop loss percentage
- `risk_per_trade`: Risk percentage per trade

#### Trading Parameters
- `initial_capital`: Starting capital amount
- `position_min_amount`: Minimum position size
- `position_max_amount`: Maximum position size
- `min_signal_ranking`: Minimum signal quality threshold
- `universe`: List of symbols to trade

## Safety Features

### Paper Trading
- Always start with paper trading (`paper_trading=True`)
- Test strategies thoroughly before live trading
- Validate configuration and risk parameters

### Risk Controls
- **Pre-trade Validation**: All orders validated before submission
- **Position Monitoring**: Continuous monitoring for risk thresholds
- **Emergency Stops**: Manual and automatic emergency stop capabilities
- **Account Protection**: Minimum balance and exposure limits

### Audit Trail
- All trading activities logged to database
- Complete order and execution history
- Risk event tracking and resolution
- Session performance metrics

## Testing

Comprehensive test suite covers:
- Data model validation and calculations
- Order execution and lifecycle management
- Risk management controls and thresholds
- Position tracking and P&L calculations
- Integration testing for complete workflows

Run tests with:
```bash
uv run pytest tests/test_live_trading.py -v
```

## Setup and Installation

1. **Database Setup**:
   ```bash
   uv run python scripts/setup_live_trading.py
   ```

2. **Environment Configuration**:
   ```bash
   # Set in .env file
   ALPACA_API_KEY=your_api_key
   ALPACA_SECRET_KEY=your_secret_key
   DATABASE_DSN=your_database_connection
   ```

3. **Dependencies**:
   All required dependencies are included in the existing project setup.

## Examples

See `examples/live_trading_example.py` for a complete working example that demonstrates:
- Environment setup and validation
- Strategy and risk parameter configuration
- Live trading session management
- Portfolio monitoring and control
- Emergency procedures

## Production Considerations

### Before Going Live
1. **Thorough Testing**: Test extensively with paper trading
2. **Risk Validation**: Validate all risk parameters and thresholds
3. **Monitoring Setup**: Establish monitoring and alerting systems
4. **Backup Plans**: Have emergency procedures and contact information ready

### Operational Best Practices
1. **Start Small**: Begin with small position sizes and limited universe
2. **Monitor Actively**: Regular monitoring especially during market hours
3. **Risk Management**: Never disable or bypass risk controls
4. **Documentation**: Keep detailed records of configuration changes
5. **Regular Reviews**: Periodic review of performance and risk metrics

### Security
- Secure API key storage and rotation
- Database security and access controls
- Audit log integrity and backup
- Network security for trading systems

## Support and Maintenance

### Monitoring
- Real-time position and P&L tracking
- Risk event monitoring and alerting
- Performance metrics and reporting
- System health and connectivity checks

### Maintenance
- Regular database cleanup and archival
- Log rotation and storage management
- API key rotation and security updates
- Strategy and parameter optimization

## Troubleshooting

### Common Issues
1. **Connection Problems**: Check API keys and network connectivity
2. **Order Rejections**: Verify account status and buying power
3. **Risk Violations**: Review risk parameters and position sizes
4. **Data Issues**: Check database connectivity and schema

### Debug Tools
- Portfolio status and summary reports
- Order and execution history queries
- Risk event analysis and resolution
- Session performance metrics

For detailed troubleshooting, check the trade logger database tables for complete audit trails and error information.