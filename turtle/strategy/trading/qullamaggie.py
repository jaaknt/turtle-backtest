import logging
from datetime import date, timedelta
from turtle.common.enums import TimeFrameUnit
from turtle.model import Signal
from turtle.repository.daily_bars_query import DailyBarsQueryRepository
from turtle.repository.ticker_query import TickerQueryRepository
from turtle.strategy.ranking.base import RankingStrategy

import polars as pl

from .base import TradingStrategy

logger = logging.getLogger(__name__)


class QullamaggieStrategy(TradingStrategy):
    """Qullamaggie-style 50-day-high breakout strategy (bk50d_s15_v1.2_roc100).

    Port of the validated signal from scripts/qullamaggie-backtest-v4.py:
    adjusted close breaks above the max of the prior 50 closes while sitting
    more than 15% above the 50-day SMA, with volume dry-up, a volume-surge cap,
    a 12-month ROC cap, RSI/ADR filters, a $5-$250 raw-close band, and a
    SPY > 200d SMA market-regime gate. Signals within 30 calendar days of the
    previous accepted trigger are suppressed.

    All rolling indicators are computed on shift-1 (prior-day) values so every
    filter only uses information available at the prior close; the breakout and
    SMA-distance checks compare the current adjusted close against them.
    Despite the historical label, no 1.2x volume-surge floor is enforced — the
    validated backtest code has none.
    """

    SMA_THRESH = 0.15
    MIN_AVG_VOL = 500_000
    MIN_PRICE = 5.0
    MAX_PRICE = 250.0
    COOLDOWN_DAYS = 30
    VOL_DRY_UP = 0.90
    VOL_SURGE_MAX = 2.0
    ROC_CAP = 1.00
    RSI_CAP = 70.0
    ADR_MIN = 0.03
    ADR_CHANGE_CAP = 0.90
    MARKET_TICKER = "SPY.US"
    # Extra calendar days of SPY history so its 200d SMA is warm for the
    # earliest ticker bar (200 trading days ~ 290 calendar days).
    MARKET_SMA_WARMUP_DAYS = 300

    def __init__(
        self,
        bars_history: DailyBarsQueryRepository,
        ranking_strategy: RankingStrategy,
        time_frame_unit: TimeFrameUnit = TimeFrameUnit.DAY,
        warmup_period: int = 730,  # 2 years: covers 252d ROC lookback + 50d windows + shift
        min_bars: int = 300,  # backtest's minimum-history rule
    ):
        """
        Initialize the Qullamaggie breakout strategy.

        Args:
            bars_history: Repository for accessing historical bar data
            ranking_strategy: Strategy for ranking signals
            time_frame_unit: Time frame for analysis (DAY expected)
            warmup_period: Number of days of historical data needed for indicators
            min_bars: Minimum number of bars required for analysis
        """
        super().__init__(bars_history, ranking_strategy, time_frame_unit, warmup_period, min_bars)
        self._regime_dates: set[date] = set()
        self._regime_dates_key: tuple[date, date] | None = None

    def get_universe(self, ticker_repo: TickerQueryRepository, limit: int | None = None) -> list[str]:
        """
        Return the backtest's fundamentals-based universe instead of a symbol group.

        Args:
            ticker_repo: Repository used to query the ticker universe
            limit: Optional maximum number of symbols to return

        Returns:
            list[str]: US common stocks with market cap >= 1.5B, excluding
            Communication Services and Real Estate sectors
        """
        return ticker_repo.get_qualified_symbols(limit=limit)

    def collect_data(self, ticker: str, start_date: date, end_date: date) -> bool:
        """
        Collect ticker bars plus the SPY market-regime data for the same window.

        Args:
            ticker: The stock symbol to collect data for
            start_date: The start date for data collection
            end_date: The end date for data collection

        Returns:
            bool: True if sufficient ticker data was collected, False otherwise
        """
        if not super().collect_data(ticker, start_date, end_date):
            return False
        self._load_regime_dates(start_date, end_date)
        return True

    def _load_regime_dates(self, start_date: date, end_date: date) -> None:
        """Cache the set of dates where SPY closed above its prior-day 200d SMA.

        The result is cached per (start_date, end_date) so the runner's
        per-ticker loop over the universe fetches SPY only once.
        """
        key = (start_date, end_date)
        if self._regime_dates_key == key:
            return
        fetch_start = start_date - timedelta(days=self.warmup_period + self.MARKET_SMA_WARMUP_DAYS)
        spy = self.bars_history.get_bars_pl(self.MARKET_TICKER, fetch_start, end_date, self.time_frame_unit)
        if spy.is_empty():
            logger.warning(f"No {self.MARKET_TICKER} bars available - market-regime filter blocks all signals")
            self._regime_dates = set()
        else:
            spy = spy.sort("date").with_columns(pl.col("close").shift(1).rolling_mean(200, min_samples=200).alias("sma200"))
            self._regime_dates = set(spy.filter(pl.col("close") > pl.col("sma200"))["date"].to_list())
        self._regime_dates_key = key

    def calculate_indicators_pl(self) -> None:
        """Calculate technical indicators using the polars DataFrame (self.pl_df).

        Prices are split/dividend-adjusted first (high/low scaled by
        adjusted_close/close); the raw close column is left untouched for the
        absolute price-band filter. Adds the following columns:
        - rsi14: RSI(14) of the prior-day adjusted close (simple rolling means)
        - sma50: 50-day SMA of the prior-day adjusted close
        - avg_vol_10 / avg_vol_20 / avg_vol_50: rolling means of prior-day volume
        - max_c_50d: rolling max of the prior 50 adjusted closes (breakout level)
        - adr_pct: 20-day mean of prior-day (high-low)/low on adjusted prices
        - adr_pct_change: 10-day / 50-day ADR ratio (contraction check)
        - pct_vs_sma50: adjusted close vs sma50, as a fraction
        - roc_252d: 12-month rate of change of the adjusted close
        - max_close_20, ema_10/20/50/200, ema_volume_10, macd, macd_signal:
          raw-close indicators required by the ranking strategies (same
          definitions as MomentumStrategy)
        """
        factor = pl.col("adjusted_close") / pl.col("close")
        df = self.pl_df.with_columns(
            pl.col("adjusted_close").alias("adj_close"),
            (pl.col("high") * factor).alias("adj_high"),
            (pl.col("low") * factor).alias("adj_low"),
            pl.col("close").rolling_max(20).alias("max_close_20"),
            pl.col("close").ewm_mean(span=10, adjust=False).alias("ema_10"),
            pl.col("close").ewm_mean(span=20, adjust=False).alias("ema_20"),
            pl.col("close").ewm_mean(span=50, adjust=False).alias("ema_50"),
            pl.col("close").ewm_mean(span=200, adjust=False).alias("ema_200"),
            pl.col("volume").ewm_mean(span=10, adjust=False).alias("ema_volume_10"),
            (pl.col("close").ewm_mean(span=12, adjust=False) - pl.col("close").ewm_mean(span=26, adjust=False)).alias("macd"),
        ).with_columns(
            pl.col("macd").ewm_mean(span=9, adjust=False).alias("macd_signal"),
        )
        df = df.with_columns(
            pl.col("adj_close").shift(1).alias("_c1"),
            pl.col("volume").cast(pl.Float64).shift(1).alias("_v1"),
            ((pl.col("adj_high") - pl.col("adj_low")) / pl.col("adj_low")).shift(1).alias("_rp1"),
        )
        # RSI(14) on the prior-day close, simple rolling means (not Wilder smoothing)
        df = df.with_columns(pl.col("_c1").diff(1).alias("_diff"))
        df = df.with_columns(
            pl.when(pl.col("_diff") > 0).then(pl.col("_diff")).otherwise(0.0).alias("_gain"),
            pl.when(pl.col("_diff") < 0).then(-pl.col("_diff")).otherwise(0.0).alias("_loss"),
        )
        df = df.with_columns(
            pl.col("_gain").rolling_mean(14, min_samples=14).alias("_avg_gain"),
            pl.col("_loss").rolling_mean(14, min_samples=14).alias("_avg_loss"),
        )
        df = df.with_columns((100.0 - 100.0 / (1.0 + pl.col("_avg_gain") / pl.col("_avg_loss"))).alias("rsi14"))
        # Rolling averages and reference levels
        df = df.with_columns(
            pl.col("_c1").rolling_mean(50, min_samples=50).alias("sma50"),
            pl.col("_v1").rolling_mean(50, min_samples=50).alias("avg_vol_50"),
            pl.col("_v1").rolling_mean(20, min_samples=20).alias("avg_vol_20"),
            pl.col("_v1").rolling_mean(10, min_samples=10).alias("avg_vol_10"),
            pl.col("_c1").rolling_max(50, min_samples=50).alias("max_c_50d"),
            pl.col("_rp1").rolling_mean(20, min_samples=20).alias("adr_pct"),
            pl.col("_rp1").rolling_mean(10, min_samples=10).alias("_adr10"),
            pl.col("_rp1").rolling_mean(50, min_samples=50).alias("_adr50"),
            pl.col("_c1").shift(251).alias("_c_252d"),
        )
        df = df.with_columns(
            ((pl.col("adj_close") / pl.col("sma50")) - 1.0).alias("pct_vs_sma50"),
            (pl.col("_adr10") / pl.col("_adr50")).alias("adr_pct_change"),
            (pl.col("adj_close") / pl.col("_c_252d") - 1.0).alias("roc_252d"),
        )
        self.pl_df = df.drop(["_c1", "_v1", "_rp1", "_diff", "_gain", "_loss", "_avg_gain", "_avg_loss", "_adr10", "_adr50", "_c_252d"])

    def _get_polars_signals(self, ticker: str, start_date: date) -> list[Signal]:
        self.calculate_indicators_pl()
        candidates = self.pl_df.filter(
            pl.col("sma50").is_not_null()
            & pl.col("max_c_50d").is_not_null()
            & pl.col("rsi14").is_not_null()
            & pl.col("roc_252d").is_not_null()
            & pl.col("adr_pct_change").is_not_null()
            & (pl.col("rsi14") < self.RSI_CAP)
            & (pl.col("close") > self.MIN_PRICE)
            & (pl.col("close") < self.MAX_PRICE)
            & (pl.col("avg_vol_20") >= self.MIN_AVG_VOL)
            & (pl.col("adr_pct") >= self.ADR_MIN)
            & (pl.col("adr_pct_change") < self.ADR_CHANGE_CAP)
            & (pl.col("adj_close") > pl.col("max_c_50d"))
            & (pl.col("pct_vs_sma50") > self.SMA_THRESH)
            & (pl.col("volume").cast(pl.Float64) < self.VOL_SURGE_MAX * pl.col("avg_vol_50"))
            & (pl.col("avg_vol_10") < self.VOL_DRY_UP * pl.col("avg_vol_50"))
            & (pl.col("roc_252d") < self.ROC_CAP)
            & pl.col("date").is_in(sorted(self._regime_dates))
        ).sort("date")
        if candidates.is_empty():
            logger.debug(f"{ticker} - no candidate breakout days")
            return []

        # Cooldown runs over the full fetched window (warmup included) so a
        # trigger just before start_date suppresses an early in-range signal.
        signal_dates: list[date] = []
        last_trigger: date | None = None
        for d in candidates["date"].to_list():
            if last_trigger is not None and (d - last_trigger).days <= self.COOLDOWN_DAYS:
                continue
            last_trigger = d
            if d >= start_date:
                signal_dates.append(d)
        return [Signal(ticker=ticker, date=d, ranking=self.ranking_strategy.ranking(self.pl_df, date=d)) for d in signal_dates]
