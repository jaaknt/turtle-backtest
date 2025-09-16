import logging
from datetime import datetime

import pandas as pd
from turtle.ranking.base import RankingStrategy

logger = logging.getLogger(__name__)


class VolumeWeightedTechnicalRanking(RankingStrategy):
    """
    Volume-weighted technical ranking strategy that evaluates stocks based on volume and volatility.

    This implementation calculates ranking scores considering:
    - Volume-confirmed momentum (higher volume on moves = higher scores)
    - Volatility-adjusted relative strength vs market benchmark
    - Liquidity quality metrics (consistent volume, trading depth)
    - Technical indicator confluence (RSI, MACD, moving averages)
    """

    def __init__(self, market_benchmark: str = "SPY") -> None:
        """
        Initialize VolumeWeightedTechnicalRanking strategy.

        Args:
            market_benchmark: Symbol to use for relative strength comparison
        """
        self.market_benchmark = market_benchmark

    def _volume_weighted_momentum(self) -> int:
        """
        Calculate momentum score weighted by volume confirmation.

        Logic:
        - Calculate 20-day price momentum
        - Weight by recent volume vs average volume
        - Higher volume on positive moves = higher score

        Returns:
            int: Ranking score (0-25)
        """
        if len(self.filtered_df) < 21:
            return 0

        # Get current and past prices for momentum calculation
        current_close = self.filtered_df.iloc[-1]["close"]
        past_close = self.filtered_df.iloc[-21]["close"]

        # Handle invalid data
        if pd.isna(current_close) or pd.isna(past_close) or past_close <= 0:
            return 0

        # Calculate 20-day price momentum
        price_momentum = (current_close - past_close) / past_close
        logger.debug(f"Volume Momentum - Price momentum: {price_momentum}")

        # Calculate volume confirmation factor
        if len(self.filtered_df) >= 60:
            recent_volume = self.filtered_df.iloc[-10:]["volume"].mean()
            avg_volume = self.filtered_df.iloc[-60:]["volume"].mean()

            if pd.isna(recent_volume) or pd.isna(avg_volume) or avg_volume <= 0:
                volume_factor = 1.0
            else:
                # Cap volume factor at 2.0 to prevent extreme scores
                volume_factor = min(recent_volume / avg_volume, 2.0)
        else:
            volume_factor = 1.0

        logger.debug(f"Volume Momentum - Volume factor: {volume_factor}")

        # More selective momentum scoring - require stronger performance
        if price_momentum >= 0.20:  # 20% or more gain (was 15%)
            base_score = 25
        elif price_momentum >= 0.05:  # 5% to 20% gain (was 0%)
            base_score = int(25 * (price_momentum - 0.05) / 0.15)
        else:  # Less than 5% gain - no points
            base_score = 0

        # Apply volume weighting - require at least 1.2x average volume
        if volume_factor < 1.2:
            score = int(base_score * 0.5)  # Penalize low volume
        else:
            score = int(base_score * min(volume_factor, 2.0))

        return min(25, max(0, score))

    def _volatility_adjusted_strength(self) -> int:
        """
        Calculate relative strength adjusted for volatility.

        Logic:
        - Compare stock performance vs market over 60 days
        - Adjust for stock's volatility (higher vol = penalty)
        - Reward consistent outperformance

        Returns:
            int: Ranking score (0-25)
        """
        if len(self.filtered_df) < 61:
            return 0

        # Calculate 60-day returns
        current_close = self.filtered_df.iloc[-1]["close"]
        past_close = self.filtered_df.iloc[-61]["close"]

        if pd.isna(current_close) or pd.isna(past_close) or past_close <= 0:
            return 0

        stock_return = (current_close - past_close) / past_close

        # Calculate volatility (standard deviation of daily returns)
        daily_returns = self.filtered_df["close"].pct_change().dropna()
        if len(daily_returns) < 20:
            return 0

        volatility = daily_returns.std()
        if pd.isna(volatility) or volatility <= 0:
            return 0

        # Risk-adjusted return (simplified Sharpe-like ratio)
        risk_adjusted_return = stock_return / volatility

        logger.debug(f"Volatility Strength - Stock return: {stock_return}, Volatility: {volatility}, Risk-adjusted: {risk_adjusted_return}")

        # More selective volatility-adjusted scoring
        # Target: risk-adjusted return of 1.5 = 25 points (was 2.0)
        if risk_adjusted_return >= 1.5:
            return 25
        elif risk_adjusted_return >= 0.5:  # Require minimum 0.5 ratio
            return int(25 * (risk_adjusted_return - 0.5) / 1.0)
        else:
            return 0

    def _liquidity_quality(self) -> int:
        """
        Evaluate trading liquidity and market depth.

        Logic:
        - Average daily volume over 60 days
        - Volume consistency (avoid thin trading)
        - Price range analysis as bid-ask spread proxy

        Returns:
            int: Ranking score (0-25)
        """
        if len(self.filtered_df) < 60:
            return 0

        # Calculate volume metrics
        volumes = self.filtered_df.iloc[-60:]["volume"]
        avg_volume = volumes.mean()
        volume_std = volumes.std()

        if pd.isna(avg_volume) or pd.isna(volume_std) or avg_volume <= 0:
            return 0

        # Volume consistency score (lower coefficient of variation = better)
        volume_cv = volume_std / avg_volume
        consistency_score = max(0, 1 - (volume_cv - 0.5))  # Penalize CV > 0.5

        # Average daily dollar volume (proxy for liquidity)
        avg_price = self.filtered_df.iloc[-60:]["close"].mean()
        if pd.isna(avg_price) or avg_price <= 0:
            return 0

        dollar_volume = avg_volume * avg_price

        # More stringent liquidity requirements
        if dollar_volume >= 5_000_000:  # $5M+ (was $1M+)
            volume_score = 1.0
        elif dollar_volume >= 1_000_000:  # $1M - $5M
            volume_score = 0.8
        elif dollar_volume >= 500_000:  # $500K - $1M
            volume_score = 0.5
        else:  # < $500K - insufficient liquidity
            volume_score = 0.0

        # Combine scores
        final_score = int(25 * consistency_score * volume_score)
        logger.debug(f"Liquidity Quality - Avg volume: {avg_volume}, CV: {volume_cv}, Dollar volume: {dollar_volume}, Score: {final_score}")

        return min(25, max(0, final_score))

    def _technical_confluence(self) -> int:
        """
        Multi-indicator technical analysis confluence.

        Logic:
        - RSI positioning (30-70 range preferred)
        - Moving average relationships (20 EMA vs 50 EMA)
        - Price momentum confirmation

        Returns:
            int: Ranking score (0-25)
        """
        if len(self.filtered_df) < 50:
            return 0

        # Calculate RSI (14-period)
        rsi_score = self._calculate_rsi_score()

        # Calculate moving average score
        ma_score = self._calculate_ma_score()

        # Calculate price momentum score
        momentum_score = self._calculate_momentum_score()

        # Combine scores (equal weighting)
        total_score = (rsi_score + ma_score + momentum_score) / 3
        final_score = int(total_score * 25 / 100)

        logger.debug(f"Technical Confluence - RSI: {rsi_score}, MA: {ma_score}, Momentum: {momentum_score}, Final: {final_score}")

        return min(25, max(0, final_score))

    def _calculate_rsi_score(self) -> int:
        """Calculate RSI-based score (0-100)."""
        if len(self.filtered_df) < 15:
            return 0

        # Simple RSI calculation
        closes = self.filtered_df["close"].tail(15).astype(float)
        deltas = closes.diff()
        gains = deltas.where(deltas > 0.0, 0.0).rolling(window=14).mean()
        losses = (-deltas).where(deltas < 0.0, 0.0).rolling(window=14).mean()

        rs = gains / losses
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]

        if pd.isna(current_rsi):
            return 0

        # Convert to scalar for comparison
        rsi_value = float(current_rsi)

        # More selective RSI scoring - prefer rising momentum
        if 40 <= rsi_value <= 65:  # Narrower optimal range
            return 100  # Sweet spot for momentum
        elif 30 <= rsi_value <= 75:  # Acceptable range (was 30-70)
            return 60  # Reduced score for wider range
        elif rsi_value > 75:
            return max(0, 60 - int((rsi_value - 75) * 3))  # Stronger overbought penalty
        else:  # RSI < 30
            return max(0, 40 - int((30 - rsi_value) * 2))  # Oversold penalty

    def _calculate_ma_score(self) -> int:
        """Calculate moving average relationship score (0-100)."""
        if len(self.filtered_df) < 50:
            return 0

        # Calculate EMAs
        closes = self.filtered_df["close"]
        ema_20 = closes.ewm(span=20).mean().iloc[-1]
        ema_50 = closes.ewm(span=50).mean().iloc[-1]
        current_price = closes.iloc[-1]

        if pd.isna(ema_20) or pd.isna(ema_50) or pd.isna(current_price):
            return 0

        score = 0

        # More stringent MA requirements
        # Price must be above both EMAs
        if current_price > ema_20 and current_price > ema_50:
            score += 50  # Increased importance
        else:
            return 0  # Fail fast if not in uptrend

        # EMA 20 above EMA 50 with meaningful separation
        ema_separation = (ema_20 - ema_50) / ema_50
        if ema_separation > 0.02:  # Require at least 2% separation
            score += 40
        elif ema_separation > 0:
            score += 20

        # Price momentum relative to EMA20
        price_ema20_momentum = (current_price - ema_20) / ema_20
        if price_ema20_momentum > 0.01:  # Price above EMA20 by 1%+
            score += 10

        return min(100, score)

    def _calculate_momentum_score(self) -> int:
        """Calculate short-term momentum score (0-100)."""
        if len(self.filtered_df) < 10:
            return 0

        # 5-day and 10-day momentum
        current_close = self.filtered_df.iloc[-1]["close"]
        close_5d = self.filtered_df.iloc[-6]["close"]
        close_10d = self.filtered_df.iloc[-11]["close"]

        if pd.isna(current_close) or pd.isna(close_5d) or pd.isna(close_10d):
            return 0

        momentum_5d = (current_close - close_5d) / close_5d
        momentum_10d = (current_close - close_10d) / close_10d

        score = 0

        # More selective momentum requirements
        # Both 5-day and 10-day must be positive for any points
        if momentum_5d <= 0 or momentum_10d <= 0:
            return 0

        # Strong 5-day momentum (accelerating)
        if momentum_5d > 0.03:  # > 3% (was 2%)
            score += 60  # Increased weight
        elif momentum_5d > 0.01:  # 1-3%
            score += 30

        # Strong 10-day momentum (sustained)
        if momentum_10d > 0.08:  # > 8% (was 5%)
            score += 40
        elif momentum_10d > 0.03:  # 3-8%
            score += 20

        return min(100, score)

    def ranking(self, df: pd.DataFrame, date: datetime) -> int:
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
        self.filtered_df = df[df["hdate"] <= date].copy()

        if len(self.filtered_df) < 130:  # Require more data for quality analysis
            return 1

        # Calculate all ranking components
        volume_momentum = self._volume_weighted_momentum()
        volatility_strength = self._volatility_adjusted_strength()
        liquidity_quality = self._liquidity_quality()
        technical_confluence = self._technical_confluence()

        # Apply quality gates - require minimum performance in key areas
        if volume_momentum < 5:  # Must have some momentum
            return 1

        if volatility_strength < 5:  # Must have some risk-adjusted strength
            return 1

        if liquidity_quality < 8:  # Must have decent liquidity
            return 1

        # Reweight components to favor momentum and volatility-adjusted strength
        # Scale volume_momentum and volatility_strength from 0-25 to 0-30
        weighted_volume_momentum = int(volume_momentum * 1.2)  # 25 * 1.2 = 30 max
        weighted_volatility_strength = int(volatility_strength * 1.2)  # 25 * 1.2 = 30 max

        # Scale liquidity_quality and technical_confluence from 0-25 to 0-20
        weighted_liquidity_quality = int(liquidity_quality * 0.8)  # 25 * 0.8 = 20 max
        weighted_technical_confluence = int(technical_confluence * 0.8)  # 25 * 0.8 = 20 max

        logger.debug(
            f"Volume Momentum: {volume_momentum} -> {weighted_volume_momentum}, "
            f"Volatility Strength: {volatility_strength} -> {weighted_volatility_strength}, "
            f"Liquidity Quality: {liquidity_quality} -> {weighted_liquidity_quality}, "
            f"Technical Confluence: {technical_confluence} -> {weighted_technical_confluence}"
        )

        total_score = weighted_volume_momentum + weighted_volatility_strength + weighted_liquidity_quality + weighted_technical_confluence

        # Additional selectivity filter - only return scores above 40 (was 0)
        final_score = min(100, max(1, total_score))
        if final_score < 40:
            return 1

        return final_score
