import logging
from datetime import date
from turtle.strategy.ranking.base import RankingStrategy

import pandas as pd
import polars as pl

_LIQUIDITY_BANDS = [(5_000_000, 1.0), (1_000_000, 0.8), (500_000, 0.5)]

logger = logging.getLogger(__name__)


class VolumeMomentumRanking(RankingStrategy):
    """
    Volume momentum ranking strategy that evaluates stocks based on volume-confirmed momentum.

    This implementation calculates ranking scores considering:
    - Volume-confirmed momentum (higher volume on moves = higher scores)
    - Volatility-adjusted relative strength vs market benchmark
    - Liquidity quality metrics (consistent volume, trading depth)
    - Technical indicator confluence (RSI, MACD, moving averages)
    """

    def __init__(self, market_benchmark: str = "SPY", use_polars: bool = False) -> None:
        super().__init__(use_polars=use_polars)
        self.market_benchmark = market_benchmark

    def _volume_weighted_momentum(self) -> int:
        """
        Calculate momentum score weighted by volume confirmation.

        Returns:
            int: Ranking score (0-25)
        """
        if self.filtered_pl_df.height < 21:
            return 0

        current_close = self.filtered_pl_df["close"][-1]
        past_close = self.filtered_pl_df["close"][-21]

        if current_close is None or past_close is None or past_close <= 0:
            return 0

        price_momentum = (current_close - past_close) / past_close
        logger.debug(f"Volume Momentum - Price momentum: {price_momentum}")

        if self.filtered_pl_df.height >= 60:
            recent_volume: float | None = self.filtered_pl_df["volume"][-10:].mean()  # type: ignore[assignment]
            avg_volume: float | None = self.filtered_pl_df["volume"][-60:].mean()  # type: ignore[assignment]
            if recent_volume is None or avg_volume is None or avg_volume <= 0:
                volume_factor = 1.0
            else:
                volume_factor = min(recent_volume / avg_volume, 2.0)
        else:
            volume_factor = 1.0

        logger.debug(f"Volume Momentum - Volume factor: {volume_factor}")

        base_score = self._linear_rank(price_momentum, 0.05, 0.20, 25)

        if volume_factor < 1.2:
            score = int(base_score * 0.5)
        else:
            score = int(base_score * min(volume_factor, 2.0))

        return min(25, max(0, score))

    def _volatility_adjusted_strength(self) -> int:
        """
        Calculate relative strength adjusted for volatility.

        Returns:
            int: Ranking score (0-25)
        """
        if self.filtered_pl_df.height < 61:
            return 0

        current_close = self.filtered_pl_df["close"][-1]
        past_close = self.filtered_pl_df["close"][-61]

        if current_close is None or past_close is None or past_close <= 0:
            return 0

        stock_return = (current_close - past_close) / past_close

        close_series = self.filtered_pl_df["close"]
        prev_close = close_series.shift(1)
        daily_returns = ((close_series - prev_close) / prev_close).drop_nulls()

        if daily_returns.len() < 20:
            return 0

        volatility: float | None = daily_returns.std()  # type: ignore[assignment]
        if volatility is None or volatility <= 0:
            return 0

        risk_adjusted_return = stock_return / volatility

        logger.debug(f"Volatility Strength - Stock return: {stock_return}, Volatility: {volatility}, Risk-adjusted: {risk_adjusted_return}")

        return self._linear_rank(risk_adjusted_return, 0.5, 1.5, 25)

    def _liquidity_quality(self) -> int:
        """
        Evaluate trading liquidity and market depth.

        Returns:
            int: Ranking score (0-25)
        """
        if self.filtered_pl_df.height < 60:
            return 0

        volumes = self.filtered_pl_df["volume"][-60:]
        avg_volume: float | None = volumes.mean()  # type: ignore[assignment]
        volume_std: float | None = volumes.std()  # type: ignore[assignment]

        if avg_volume is None or volume_std is None or avg_volume <= 0:
            return 0

        volume_cv = volume_std / avg_volume
        consistency_score = max(0, 1 - (volume_cv - 0.5))

        avg_price: float | None = self.filtered_pl_df["close"][-60:].mean()  # type: ignore[assignment]
        if avg_price is None or avg_price <= 0:
            return 0

        dollar_volume = avg_volume * avg_price

        volume_score = next((score for threshold, score in _LIQUIDITY_BANDS if dollar_volume >= threshold), 0.0)

        final_score = int(25 * consistency_score * volume_score)
        logger.debug(f"Liquidity Quality - Avg volume: {avg_volume}, CV: {volume_cv}, Dollar volume: {dollar_volume}, Score: {final_score}")

        return min(25, max(0, final_score))

    def _technical_confluence(self) -> int:
        """
        Multi-indicator technical analysis confluence.

        Returns:
            int: Ranking score (0-25)
        """
        if self.filtered_pl_df.height < 50:
            return 0

        rsi_score = self._calculate_rsi_score()
        ma_score = self._calculate_ma_score()
        momentum_score = self._calculate_momentum_score()

        total_score = (rsi_score + ma_score + momentum_score) / 3
        final_score = int(total_score * 25 / 100)

        logger.debug(f"Technical Confluence - RSI: {rsi_score}, MA: {ma_score}, Momentum: {momentum_score}, Final: {final_score}")

        return min(25, max(0, final_score))

    def _calculate_rsi_score(self) -> int:
        """Calculate RSI-based score (0-100)."""
        if self.filtered_pl_df.height < 15:
            return 0

        closes = self.filtered_pl_df["close"][-15:].cast(pl.Float64)
        deltas = closes.diff().fill_null(0.0)
        gains = deltas.clip(lower_bound=0.0)
        losses = (-deltas).clip(lower_bound=0.0)

        avg_gain: float | None = gains[-14:].mean()  # type: ignore[assignment]
        avg_loss: float | None = losses[-14:].mean()  # type: ignore[assignment]

        if avg_gain is None or avg_loss is None or avg_loss == 0:
            return 0

        rs = avg_gain / avg_loss
        rsi_value = 100.0 - (100.0 / (1.0 + rs))

        if 40 <= rsi_value <= 65:
            return 100
        elif 30 <= rsi_value <= 75:
            return 60
        elif rsi_value > 75:
            return max(0, 60 - int((rsi_value - 75) * 3))
        else:
            return max(0, 40 - int((30 - rsi_value) * 2))

    def _calculate_ma_score(self) -> int:
        """Calculate moving average relationship score (0-100)."""
        if self.filtered_pl_df.height < 50:
            return 0

        closes = self.filtered_pl_df["close"]
        ema_20 = closes.ewm_mean(span=20, adjust=False)[-1]
        ema_50 = closes.ewm_mean(span=50, adjust=False)[-1]
        current_price = closes[-1]

        if ema_20 is None or ema_50 is None or current_price is None:
            return 0

        score = 0

        if current_price > ema_20 and current_price > ema_50:
            score += 50
        else:
            return 0

        ema_separation = (ema_20 - ema_50) / ema_50
        if ema_separation > 0.02:
            score += 40
        elif ema_separation > 0:
            score += 20

        price_ema20_momentum = (current_price - ema_20) / ema_20
        if price_ema20_momentum > 0.01:
            score += 10

        return min(100, score)

    def _calculate_momentum_score(self) -> int:
        """Calculate short-term momentum score (0-100)."""
        if self.filtered_pl_df.height < 11:
            return 0

        current_close = self.filtered_pl_df["close"][-1]
        close_5d = self.filtered_pl_df["close"][-6]
        close_10d = self.filtered_pl_df["close"][-11]

        if current_close is None or close_5d is None or close_10d is None:
            return 0

        momentum_5d = (current_close - close_5d) / close_5d
        momentum_10d = (current_close - close_10d) / close_10d

        score = 0

        if momentum_5d <= 0 or momentum_10d <= 0:
            return 0

        if momentum_5d > 0.03:
            score += 60
        elif momentum_5d > 0.01:
            score += 30

        if momentum_10d > 0.08:
            score += 40
        elif momentum_10d > 0.03:
            score += 20

        return min(100, score)

    def ranking(self, df: pd.DataFrame | pl.DataFrame, date: date) -> int:
        """
        Calculate a combined ranking score based on volume-weighted technical analysis.

        Args:
            df: DataFrame with OHLCV data
            date: The date for which to calculate the ranking

        Returns:
            int: Combined ranking score (0-100):
                 - Volume-weighted momentum: 0-30 (increased weight)
                 - Volatility-adjusted strength: 0-30 (increased weight)
                 - Liquidity quality: 0-20 (decreased weight)
                 - Technical confluence: 0-20 (decreased weight)

        Quality gates applied for selectivity improvement.
        """
        pl_df = self._to_polars(df)
        self.filtered_pl_df = pl_df.filter(pl.col("date") <= date)

        if self.filtered_pl_df.height < 130:
            return 1

        volume_momentum = self._volume_weighted_momentum()
        volatility_strength = self._volatility_adjusted_strength()
        liquidity_quality = self._liquidity_quality()
        technical_confluence = self._technical_confluence()

        if volume_momentum < 5:
            return 1
        if volatility_strength < 5:
            return 1
        if liquidity_quality < 8:
            return 1

        weighted_volume_momentum = int(volume_momentum * 1.2)
        weighted_volatility_strength = int(volatility_strength * 1.2)
        weighted_liquidity_quality = int(liquidity_quality * 0.8)
        weighted_technical_confluence = int(technical_confluence * 0.8)

        logger.debug(
            f"Volume Momentum: {volume_momentum} -> {weighted_volume_momentum}, "
            f"Volatility Strength: {volatility_strength} -> {weighted_volatility_strength}, "
            f"Liquidity Quality: {liquidity_quality} -> {weighted_liquidity_quality}, "
            f"Technical Confluence: {technical_confluence} -> {weighted_technical_confluence}"
        )

        total_score = weighted_volume_momentum + weighted_volatility_strength + weighted_liquidity_quality + weighted_technical_confluence

        final_score = min(100, max(1, total_score))
        if final_score < 40:
            return 1

        return final_score
