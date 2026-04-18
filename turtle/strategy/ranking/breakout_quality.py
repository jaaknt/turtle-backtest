import logging
from datetime import datetime
from turtle.strategy.ranking.base import RankingStrategy

import pandas as pd

logger = logging.getLogger(__name__)


class BreakoutQualityRanking(RankingStrategy):
    """
    Breakout quality ranking strategy that scores signals based on the strength
    of the breakout event itself.

    Rather than measuring long-term momentum (like MomentumRanking) this strategy
    measures how convincingly each of the DarvasBox signal conditions is met at
    the moment of the signal:

    - Volume Conviction  (0-30 pts): breakout volume vs 10-day EMA of volume
    - Breakout Extension (0-25 pts): how far close exceeds the 20-day high
    - Trend Health       (0-25 pts): EMA stack alignment + healthy distance from EMA200
    - MACD Conviction    (0-20 pts): MACD-signal gap as % of price

    Total: 0-100
    """

    def _volume_conviction(self, row: pd.Series) -> int:
        """
        Score breakout volume relative to the 10-day EMA of volume (0-30 pts).

        A larger multiple indicates more conviction behind the move.
        """
        volume = row["volume"]
        avg_volume = row["ema_volume_10"]

        if pd.isna(volume) or pd.isna(avg_volume) or avg_volume <= 0:
            return 0

        ratio = volume / avg_volume
        if ratio >= 3.0:
            return 30
        elif ratio >= 2.5:
            return 25
        elif ratio >= 2.0:
            return 20
        elif ratio >= 1.75:
            return 15
        elif ratio >= 1.5:
            return 10
        elif ratio >= 1.25:
            return 5
        return 0

    def _breakout_extension(self, row: pd.Series) -> int:
        """
        Score how far the close exceeds the 20-day high (0-25 pts).

        A more extended breakout shows stronger conviction.
        """
        close = row["close"]
        max_close_20 = row["max_close_20"]

        if pd.isna(close) or pd.isna(max_close_20) or max_close_20 <= 0:
            return 0

        extension_pct = (close - max_close_20) / max_close_20 * 100
        if extension_pct >= 5.0:
            return 25
        elif extension_pct >= 3.0:
            return 20
        elif extension_pct >= 2.0:
            return 15
        elif extension_pct >= 1.0:
            return 10
        elif extension_pct >= 0.5:
            return 5
        return 0

    def _trend_health(self, row: pd.Series) -> int:
        """
        Score EMA stack alignment and distance above EMA200 (0-25 pts).

        Full alignment (EMA10 > EMA20 > EMA50 > EMA200) scores base points.
        Distance to EMA200 is optimal in the 5-30% band — overextension is
        penalised because stocks >30% above EMA200 are prone to reversals.
        """
        close = row["close"]
        ema_10 = row["ema_10"]
        ema_20 = row["ema_20"]
        ema_50 = row["ema_50"]
        ema_200 = row["ema_200"]

        if any(pd.isna(v) for v in [close, ema_10, ema_20, ema_50, ema_200]) or ema_200 <= 0:
            return 0

        # Alignment base points
        alignment_pts = 0
        if ema_50 > ema_200:
            alignment_pts += 5
        if ema_10 > ema_20 > ema_50 > ema_200:
            alignment_pts += 10  # full stack aligned (cumulative: 15 max)

        # Distance-from-EMA200 points (0-10): reward 5-30% above, penalise outside
        pct_above = (close - ema_200) / ema_200 * 100
        if 5.0 <= pct_above <= 30.0:
            # Linear scale: 5% → 0 pts, 17.5% → 10 pts, 30% → 0 pts (triangle)
            distance_pts = int(10 * (1.0 - abs(pct_above - 17.5) / 12.5))
            distance_pts = max(0, distance_pts)
        else:
            distance_pts = 0

        return alignment_pts + distance_pts

    def _macd_conviction(self, row: pd.Series) -> int:
        """
        Score MACD-signal gap as a percentage of price (0-20 pts).

        Normalising by price makes the score comparable across different
        price ranges.
        """
        close = row["close"]
        macd = row["macd"]
        macd_signal = row["macd_signal"]

        if any(pd.isna(v) for v in [close, macd, macd_signal]) or close <= 0:
            return 0

        gap_pct = (macd - macd_signal) / close * 100
        if gap_pct >= 0.5:
            return 20
        elif gap_pct >= 0.3:
            return 15
        elif gap_pct >= 0.2:
            return 10
        elif gap_pct >= 0.1:
            return 5
        return 0

    def ranking(self, df: pd.DataFrame, date: datetime) -> int:
        """
        Calculate breakout quality ranking score (0-100).

        Args:
            df: DataFrame with OHLCV and indicator columns up to and including
                the signal date.  Expected columns: close, volume, ema_10,
                ema_20, ema_50, ema_200, ema_volume_10, max_close_20, macd,
                macd_signal.
            date: The signal date.

        Returns:
            int: Score in range 0-100.
        """
        filtered = df[df["date"] <= date]
        if filtered.empty:
            return 0

        row = filtered.iloc[-1]

        vol_pts = self._volume_conviction(row)
        ext_pts = self._breakout_extension(row)
        trend_pts = self._trend_health(row)
        macd_pts = self._macd_conviction(row)

        score = vol_pts + ext_pts + trend_pts + macd_pts
        logger.debug(
            f"BreakoutQualityRanking date={date.date() if hasattr(date, 'date') else date} "
            f"volume={vol_pts} extension={ext_pts} trend={trend_pts} macd={macd_pts} total={score}"
        )
        return score
