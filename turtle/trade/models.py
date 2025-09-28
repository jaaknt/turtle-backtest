"""Data models for live trading operations."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum

from turtle.signal.models import Signal


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderSide(Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


@dataclass
class LiveOrder:
    """
    Represents a live trading order.

    Attributes:
        id: Unique order identifier (from Alpaca)
        client_order_id: Client-side order identifier
        ticker: Stock symbol
        side: Buy or sell order
        order_type: Market, limit, stop, etc.
        quantity: Number of shares
        price: Order price (for limit orders)
        stop_price: Stop price (for stop orders)
        time_in_force: Order duration (day, gtc, etc.)
        status: Current order status
        created_at: Order creation timestamp
        submitted_at: Order submission timestamp
        filled_at: Order fill timestamp
        filled_price: Actual fill price
        filled_quantity: Number of shares filled
        commission: Commission paid
        signal_id: Associated signal ID (for tracking)
    """

    ticker: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    id: str | None = None
    client_order_id: str | None = None
    price: Decimal | None = None
    stop_price: Decimal | None = None
    time_in_force: str = "day"
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    submitted_at: datetime | None = None
    filled_at: datetime | None = None
    filled_price: Decimal | None = None
    filled_quantity: int | None = None
    commission: Decimal | None = None
    signal_id: str | None = None

    @property
    def is_complete(self) -> bool:
        """Check if order is in a terminal state."""
        return self.status in [OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.REJECTED, OrderStatus.EXPIRED]

    @property
    def is_filled(self) -> bool:
        """Check if order is fully filled."""
        return self.status == OrderStatus.FILLED

    @property
    def fill_value(self) -> Decimal:
        """Calculate total fill value."""
        if self.filled_price and self.filled_quantity:
            return self.filled_price * Decimal(self.filled_quantity)
        return Decimal(0)


@dataclass
class LivePosition:
    """
    Represents a live trading position.

    Attributes:
        ticker: Stock symbol
        quantity: Number of shares held (positive for long, negative for short)
        avg_price: Average cost basis
        market_price: Current market price
        unrealized_pnl: Unrealized profit/loss
        market_value: Current market value
        cost_basis: Total cost basis
        entry_date: Position entry date
        entry_signal: Signal that initiated the position
        stop_loss_order_id: Associated stop loss order ID
        take_profit_order_id: Associated take profit order ID
    """

    ticker: str
    quantity: int
    avg_price: Decimal
    market_price: Decimal
    cost_basis: Decimal
    entry_date: datetime
    unrealized_pnl: Decimal = field(default=Decimal(0))
    entry_signal: Signal | None = None
    stop_loss_order_id: str | None = None
    take_profit_order_id: str | None = None

    @property
    def market_value(self) -> Decimal:
        """Calculate current market value."""
        return self.market_price * Decimal(abs(self.quantity))

    @property
    def is_long(self) -> bool:
        """Check if position is long."""
        return self.quantity > 0

    @property
    def is_short(self) -> bool:
        """Check if position is short."""
        return self.quantity < 0

    @property
    def pnl_percentage(self) -> float:
        """Calculate P&L percentage."""
        if self.cost_basis == 0:
            return 0.0
        return float(self.unrealized_pnl / self.cost_basis * 100)


@dataclass
class RiskParameters:
    """
    Risk management parameters for live trading.

    Attributes:
        max_position_size: Maximum dollar amount per position
        max_portfolio_exposure: Maximum portfolio exposure (0.0-1.0)
        max_daily_loss: Maximum daily loss limit
        max_open_positions: Maximum number of open positions
        min_account_balance: Minimum account balance to maintain
        stop_loss_percentage: Default stop loss percentage
        take_profit_percentage: Default take profit percentage
        position_sizing_method: Method for calculating position sizes
        use_atr_sizing: Use ATR for position sizing
        risk_per_trade: Risk percentage per trade (0.0-1.0)
    """

    max_position_size: Decimal = Decimal(10000)
    max_portfolio_exposure: float = 0.8
    max_daily_loss: Decimal = Decimal(1000)
    max_open_positions: int = 10
    min_account_balance: Decimal = Decimal(5000)
    stop_loss_percentage: float = 0.05  # 5%
    take_profit_percentage: float = 0.15  # 15%
    position_sizing_method: str = "fixed"  # fixed, percentage, atr
    use_atr_sizing: bool = False
    risk_per_trade: float = 0.02  # 2%

    def validate(self) -> None:
        """Validate risk parameters."""
        if self.max_portfolio_exposure < 0 or self.max_portfolio_exposure > 1:
            raise ValueError("max_portfolio_exposure must be between 0 and 1")
        if self.risk_per_trade < 0 or self.risk_per_trade > 1:
            raise ValueError("risk_per_trade must be between 0 and 1")
        if self.max_daily_loss <= 0:
            raise ValueError("max_daily_loss must be positive")


@dataclass
class TradingSession:
    """
    Represents a live trading session.

    Attributes:
        id: Unique session identifier
        start_time: Session start time
        end_time: Session end time (None if active)
        strategy_name: Trading strategy used
        initial_balance: Starting account balance
        current_balance: Current account balance
        total_trades: Total number of trades executed
        winning_trades: Number of winning trades
        losing_trades: Number of losing trades
        total_pnl: Total realized P&L
        max_drawdown: Maximum drawdown during session
        is_active: Whether session is currently active
        paper_trading: Whether using paper trading
        universe: List of symbols being traded
    """

    id: str
    strategy_name: str
    initial_balance: Decimal
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    current_balance: Decimal | None = None
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: Decimal = field(default=Decimal(0))
    max_drawdown: Decimal = field(default=Decimal(0))
    is_active: bool = True
    paper_trading: bool = True
    universe: list[str] = field(default_factory=list)

    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage."""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100.0

    @property
    def duration_hours(self) -> float:
        """Calculate session duration in hours."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds() / 3600.0


@dataclass
class ExecutionReport:
    """
    Trade execution report.

    Attributes:
        order_id: Order identifier
        execution_id: Unique execution identifier
        ticker: Stock symbol
        side: Buy or sell
        quantity: Number of shares executed
        price: Execution price
        timestamp: Execution timestamp
        commission: Commission paid
        liquidity: Liquidity indicator (added/removed)
    """

    order_id: str
    execution_id: str
    ticker: str
    side: OrderSide
    quantity: int
    price: Decimal
    timestamp: datetime
    commission: Decimal = field(default=Decimal(0))
    liquidity: str | None = None

    @property
    def execution_value(self) -> Decimal:
        """Calculate execution value."""
        return self.price * Decimal(self.quantity)


@dataclass
class MarketData:
    """
    Real-time market data.

    Attributes:
        ticker: Stock symbol
        timestamp: Data timestamp
        bid: Bid price
        ask: Ask price
        last_price: Last trade price
        volume: Volume
        bid_size: Bid size
        ask_size: Ask size
    """

    ticker: str
    timestamp: datetime
    bid: Decimal
    ask: Decimal
    last_price: Decimal
    volume: int
    bid_size: int = 0
    ask_size: int = 0

    @property
    def spread(self) -> Decimal:
        """Calculate bid-ask spread."""
        return self.ask - self.bid

    @property
    def mid_price(self) -> Decimal:
        """Calculate mid price."""
        return (self.bid + self.ask) / Decimal(2)


@dataclass
class AccountInfo:
    """
    Trading account information.

    Attributes:
        account_id: Account identifier
        equity: Total account equity
        cash: Available cash
        buying_power: Available buying power
        portfolio_value: Total portfolio value
        long_market_value: Long positions market value
        short_market_value: Short positions market value
        day_trade_count: Day trade count
        pattern_day_trader: Pattern day trader status
        trading_blocked: Whether trading is blocked
        account_blocked: Whether account is blocked
        transfers_blocked: Whether transfers are blocked
    """

    account_id: str
    equity: Decimal
    cash: Decimal
    buying_power: Decimal
    portfolio_value: Decimal
    long_market_value: Decimal = field(default=Decimal(0))
    short_market_value: Decimal = field(default=Decimal(0))
    day_trade_count: int = 0
    pattern_day_trader: bool = False
    trading_blocked: bool = False
    account_blocked: bool = False
    transfers_blocked: bool = False

    @property
    def net_market_value(self) -> Decimal:
        """Calculate net market value."""
        return self.long_market_value - self.short_market_value

    @property
    def cash_percentage(self) -> float:
        """Calculate cash as percentage of portfolio."""
        if self.portfolio_value == 0:
            return 0.0
        return float(self.cash / self.portfolio_value * 100)
