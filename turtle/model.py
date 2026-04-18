"""Domain model dataclasses shared across the turtle package."""

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class Signal:
    """Ticker signals

    Attributes:
        ticker (str): Stock symbol code
        date (date): Date when the signal was generated
        ranking (int): Ranking score of the signal (1-100)
    """

    ticker: str
    date: date
    ranking: int


@dataclass
class Trade:
    """
    Represents a single trade.

    Attributes:
        ticker: Stock symbol for the trade
        date: Trade date and time
        price: Price at which the trade was executed
        reason: Reason for entry or exit
    """

    ticker: str
    date: datetime
    price: float
    reason: str


@dataclass
class Benchmark:
    """
    Represents a benchmark return comparison.

    Attributes:
        ticker: Benchmark ticker symbol (e.g., 'SPY', 'QQQ')
        return_pct: Percentage return for the benchmark over the same period
        entry_date: Date when the benchmark calculation period starts
        exit_date: Date when the benchmark calculation period ends
    """

    ticker: str
    return_pct: float
    entry_date: datetime
    exit_date: datetime

    @property
    def annualized_pct(self) -> float:
        """
        Calculate the annualized percentage return.

        Returns:
            Annualized return = ((1 + return_pct/100) ^ (365 / days) - 1) * 100
            Returns return_pct if holding period is zero.
        """
        days = (self.exit_date - self.entry_date).days
        if days <= 0:
            return self.return_pct
        return float(((1 + self.return_pct / 100.0) ** (365.0 / days) - 1) * 100.0)


@dataclass
class FutureTrade:
    """
    Represents a completed trading signal and its outcomes.

    Attributes:
        signal: Signal that is input for calculation
        entry: Trade object containing entry date, price, and reason
        exit: Trade object containing exit date, price, and reason
        benchmark_list: List of benchmark comparisons for the same period
        position_size: Position size in shares or dollar amount (defaults to 1.0)
        slippage_pct: Slippage percentage (defaults to 0.3%)
        entry_signal_ranking: Original signal ranking when position was opened (optional)
    """

    signal: Signal
    entry: Trade
    exit: Trade
    benchmark_list: list[Benchmark]
    position_size: float = 1.0
    slippage_pct: float = 0.3

    @property
    def holding_days(self) -> int:
        """
        Calculate the number of days the position was held.

        Returns:
            Number of days between entry and exit dates
        """
        return (self.exit.date - self.entry.date).days

    @property
    def realized_pnl(self) -> float:
        """
        Calculate the realized profit/loss in dollars.

        Returns:
            Realized profit/loss = (exit_price - entry_price) * position_size
        """
        return (self.exit.price - self.entry.price) * self.position_size

    @property
    def realized_pct(self) -> float:
        """
        Calculate the realized percentage return.

        Returns:
            Percentage return = ((exit_price - entry_price) / entry_price) * 100
        """
        if self.entry.price <= 0:
            raise ValueError(f"Invalid entry price: {self.entry.price}")
        return ((self.exit.price - self.entry.price) / self.entry.price) * 100.0

    @property
    def annualized_pct(self) -> float:
        """
        Calculate the annualized percentage return.

        Returns:
            Annualized return = ((exit_price / entry_price) ^ (365 / holding_days) - 1) * 100
            Returns realized_pct if holding period is zero.
        """
        if self.entry.price <= 0:
            raise ValueError(f"Invalid entry price: {self.entry.price}")
        holding_days = self.holding_days
        if holding_days <= 0:
            return self.realized_pct
        return float(((self.exit.price / self.entry.price) ** (365.0 / holding_days) - 1) * 100.0)

    @property
    def exit_reason(self) -> str:
        """
        Get the exit reason from the exit trade.

        Returns:
            Exit reason string
        """
        return self.exit.reason

    @property
    def ticker(self) -> str:
        """
        Get the ticker symbol from the signal or entry trade.

        Returns:
            Ticker symbol string
        """
        return self.signal.ticker

    @property
    def slippage(self) -> float:
        """
        Calculate the slippage in dollars.
        Returns:
            slippage = (entry_price + exit_price) / 2 * (slippage_pct / 100) * position_size
        """
        entry_price = self.entry.price
        exit_price = self.exit.price
        return (entry_price + exit_price) / 2 * (self.slippage_pct / 100.0) * self.position_size


@dataclass
class Position:
    """
    Represents a single portfolio position.

    Attributes:
        entry: Trade object representing entry trade
        exit: Trade object representing exit trade in future
        position_size: Number of shares held
        slippage_pct: Slippage percentage (defaults to 0.3%)
    """

    entry: Trade
    exit: Trade
    current_price: float
    position_size: int
    slippage_pct: float = 0.3

    @property
    def ticker(self) -> str:
        """Get the ticker symbol from the entry trade."""
        return self.entry.ticker

    @property
    def current_value(self) -> float:
        """Get the current market value of the position."""
        return self.current_price * self.position_size

    @property
    def unrealized_pnl(self) -> float:
        """Get unrealized P&L"""
        return (self.current_price - self.entry.price) * self.position_size

    @property
    def holding_period_days(self) -> int:
        """Get the holding period in days"""
        return (self.exit.date - self.entry.date).days

    @property
    def slippage(self) -> float:
        """
        Calculate the slippage in dollars.
        Returns:
            slippage = (entry_price + exit_price) / 2 * (slippage_pct / 100) * position_size
        """
        entry_price = self.entry.price
        exit_price = self.exit.price
        return (entry_price + exit_price) / 2 * (self.slippage_pct / 100.0) * self.position_size


@dataclass
class DailyPortfolioSnapshot:
    """
    Daily snapshot of portfolio state.

    Attributes:
        date: Snapshot date
        total_value: Total portfolio value
        cash: Available cash
        positions: List of positions at snapshot time
    """

    date: date
    cash: float
    positions: list[Position]

    @property
    def positions_value(self) -> float:
        """Total value of all positions at snapshot time."""
        return sum(position.current_value for position in self.positions)

    @property
    def positions_count(self) -> int:
        """Number of positions at snapshot time."""
        return len(self.positions)

    @property
    def total_value(self) -> float:
        """Total value of all positions at snapshot time."""
        return self.cash + self.positions_value

    def get_position(self, ticker: str) -> Position:
        """Get a position by ticker symbol."""
        for position in self.positions:
            if position.ticker == ticker:
                return position
        raise ValueError(f"Position not found for ticker: {ticker}")

    def add_position(self, position: Position) -> None:
        """Add a new position."""
        self.positions.append(position)
        self.cash -= position.current_value

    def remove_position(self, ticker: str, price: float) -> None:
        """Remove a position by ticker symbol."""
        position = self.get_position(ticker)
        self.cash += position.position_size * price - position.slippage
        self.positions.remove(position)

    def update_position_price(self, ticker: str, new_price: float) -> None:
        """Update the price of an existing position by creating a new exit trade."""
        position = self.get_position(ticker)
        position.current_price = new_price
        return None

    def copy(self) -> "DailyPortfolioSnapshot":
        """Create a deep copy of the snapshot."""
        return DailyPortfolioSnapshot(
            date=self.date,
            cash=self.cash,
            positions=[
                Position(
                    entry=Trade(p.entry.ticker, p.entry.date, p.entry.price, p.entry.reason),
                    exit=Trade(p.exit.ticker, p.exit.date, p.exit.price, p.exit.reason),
                    position_size=p.position_size,
                    current_price=p.current_price,
                    slippage_pct=p.slippage_pct,
                )
                for p in self.positions
            ],
        )

    def get_tickers(self) -> list[str]:
        """Get a list of all ticker symbols in the portfolio."""
        return [position.ticker for position in self.positions]


@dataclass
class PortfolioState:
    """
    Current state of the portfolio.

    Attributes:
        daily_snapshots: Historical daily snapshots
        future_trades: List of all future trades
    """

    daily_snapshots: list[DailyPortfolioSnapshot] = field(default_factory=list)
    future_trades: list[FutureTrade] = field(default_factory=list)


@dataclass
class SymbolGroup:
    """Stock symbol groups

    Attributes:
    code (str): group (NAS100, ...) where the symbol belongs
    ticker_code (str): symbol code in stock exchange
    rate (float): rate of the symbol in the group
    """

    code: str
    ticker_code: str
    rate: float
