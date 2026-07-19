import logging
from datetime import date

from turtlex.model import Signal
from turtlex.repository.query.ticker import TickerQueryRepository
from turtlex.strategy.trading.base import TradingStrategy

logger = logging.getLogger(__name__)


class SignalService:
    """Orchestrates trading-signal generation across a ticker universe."""

    def __init__(self, trading_strategy: TradingStrategy, ticker_repo: TickerQueryRepository) -> None:
        """
        Initialize the signal service.

        Args:
            trading_strategy: Strategy that generates signals and defines its own ticker universe
            ticker_repo: Repository used to resolve the strategy's ticker universe
        """
        self.trading_strategy = trading_strategy
        self.ticker_repo = ticker_repo

    def scan(self, start_date: date, end_date: date, max_tickers: int | None = None) -> list[Signal]:
        """
        Generate signals for every ticker in the strategy's universe.

        Args:
            start_date: The start date of the analysis period
            end_date: The end date of the analysis period
            max_tickers: Optional maximum number of universe tickers to scan

        Returns:
            list[Signal]: Signals from all scanned tickers, in universe order
        """
        universe = self.trading_strategy.get_universe(self.ticker_repo, limit=max_tickers)
        logger.info(f"Scanning {len(universe)} tickers for signals")
        signals: list[Signal] = []
        for ticker in universe:
            signals.extend(self.trading_strategy.get_signals(ticker, start_date, end_date))
        return signals
