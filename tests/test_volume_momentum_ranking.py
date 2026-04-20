import warnings
from datetime import datetime
from turtle.strategy.ranking.base import RankingStrategy
from turtle.strategy.ranking.volume_momentum import VolumeMomentumRanking

import numpy as np
import pandas as pd
import polars as pl

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="pkg_resources")


def create_test_data(length: int = 100) -> pd.DataFrame:
    """Create test OHLCV data for ranking tests."""
    dates = pd.date_range(start="2024-01-01", periods=length, freq="D")

    # Create realistic price movement
    np.random.seed(42)  # For reproducible tests
    base_price = 100.0
    price_changes = np.random.normal(0, 0.02, length)  # 2% daily volatility
    prices = [base_price]

    for change in price_changes[1:]:
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 1.0))  # Ensure positive prices

    # Create OHLC from close prices
    closes = np.array(prices)
    highs = closes * (1 + np.abs(np.random.normal(0, 0.01, length)))
    lows = closes * (1 - np.abs(np.random.normal(0, 0.01, length)))
    opens = np.roll(closes, 1)
    opens[0] = closes[0]

    # Create volume data (higher volume on bigger moves)
    volumes = np.abs(np.random.normal(1000000, 500000, length))
    volume_multiplier = 1 + np.abs(price_changes) * 2  # Higher volume on bigger moves
    volumes = volumes * volume_multiplier

    return pd.DataFrame({"date": dates, "open": opens, "high": highs, "low": lows, "close": closes, "volume": volumes})


def test_ranking_initialization() -> None:
    """Test VolumeMomentumRanking initialization."""
    ranking = VolumeMomentumRanking()
    assert ranking.market_benchmark == "SPY"

    ranking_custom = VolumeMomentumRanking(market_benchmark="QQQ")
    assert ranking_custom.market_benchmark == "QQQ"


def test_ranking_with_insufficient_data() -> None:
    """Test ranking behavior with insufficient data."""
    ranking = VolumeMomentumRanking()

    # Test with very limited data (less than 130 required)
    short_data = create_test_data(50)
    target_date = datetime(2024, 2, 19)

    score = ranking.ranking(short_data, target_date)
    assert score == 1


def test_ranking_with_valid_data() -> None:
    """Test ranking with sufficient data."""
    ranking = VolumeMomentumRanking()

    # Create data with sufficient history
    data = create_test_data(150)
    target_date = datetime(2024, 5, 1)

    score = ranking.ranking(data, target_date)
    assert 0 <= score <= 100  # Score should be in valid range


def test_volume_weighted_momentum_component() -> None:
    """Test volume-weighted momentum calculation."""
    ranking = VolumeMomentumRanking()

    # Create trending data with volume confirmation
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")

    # Strong uptrending prices to meet new selectivity requirements
    prices = np.linspace(80, 120, 100)  # 50% gain over period for stronger momentum

    # Higher volume on recent days (volume confirmation) - meet new 1.2x threshold
    volumes = np.concatenate(
        [
            np.full(50, 1000000),  # Lower volume early
            np.full(50, 2500000),  # Higher volume later (2.5x increase)
        ]
    )

    data = pd.DataFrame({"date": dates, "open": prices, "high": prices * 1.01, "low": prices * 0.99, "close": prices, "volume": volumes})

    ranking.filtered_pl_df = pl.from_pandas(data)
    momentum_score = ranking._volume_weighted_momentum()

    assert momentum_score > 0  # Should be positive for uptrending + volume
    assert momentum_score <= 25  # Max score is 25


def test_volatility_adjusted_strength_component() -> None:
    """Test volatility-adjusted strength calculation."""
    ranking = VolumeMomentumRanking()

    # Create stable uptrending data (good risk-adjusted return)
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")

    # Steady uptrend with low volatility
    prices = np.linspace(90, 110, 100)
    small_noise = np.random.normal(0, 0.005, 100)  # Very low volatility
    prices = prices + small_noise

    data = pd.DataFrame(
        {"date": dates, "open": prices, "high": prices * 1.005, "low": prices * 0.995, "close": prices, "volume": np.full(100, 1000000)}
    )

    ranking.filtered_pl_df = pl.from_pandas(data)
    strength_score = ranking._volatility_adjusted_strength()

    assert strength_score >= 0  # Should be non-negative
    assert strength_score <= 25  # Max score is 25


def test_liquidity_quality_component() -> None:
    """Test liquidity quality calculation."""
    ranking = VolumeMomentumRanking()

    # Create data with good liquidity
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    prices = np.full(100, 100.0)  # Stable price

    # Consistent high volume (good liquidity) - meet new $5M+ requirement
    volumes = np.random.normal(6000000, 500000, 100)  # $600M daily volume
    volumes = np.abs(volumes)  # Ensure positive

    data = pd.DataFrame({"date": dates, "open": prices, "high": prices, "low": prices, "close": prices, "volume": volumes})

    ranking.filtered_pl_df = pl.from_pandas(data)
    liquidity_score = ranking._liquidity_quality()

    assert liquidity_score > 0  # Should be positive for good liquidity
    assert liquidity_score <= 25  # Max score is 25


def test_technical_confluence_component() -> None:
    """Test technical confluence calculation."""
    ranking = VolumeMomentumRanking()

    # Create data suitable for technical analysis
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")

    # Gradual uptrend for positive technical signals
    base_prices = np.linspace(90, 110, 100)
    noise = np.random.normal(0, 0.01, 100)
    prices = base_prices + noise

    data = pd.DataFrame(
        {"date": dates, "open": prices, "high": prices * 1.01, "low": prices * 0.99, "close": prices, "volume": np.full(100, 1000000)}
    )

    ranking.filtered_pl_df = pl.from_pandas(data)
    confluence_score = ranking._technical_confluence()

    assert confluence_score >= 0  # Should be non-negative
    assert confluence_score <= 25  # Max score is 25


def test_rsi_calculation() -> None:
    """Test RSI calculation component."""
    ranking = VolumeMomentumRanking()

    # Create oscillating data for RSI test
    dates = pd.date_range(start="2024-01-01", periods=50, freq="D")

    # Create data that should result in RSI around 50 (neutral)
    prices = 100 + np.sin(np.linspace(0, 4 * np.pi, 50)) * 5

    data = pd.DataFrame({"date": dates, "open": prices, "high": prices, "low": prices, "close": prices, "volume": np.full(50, 1000000)})

    ranking.filtered_pl_df = pl.from_pandas(data)
    rsi_score = ranking._calculate_rsi_score()

    assert 0 <= rsi_score <= 100  # RSI score should be in valid range


def test_moving_average_calculation() -> None:
    """Test moving average relationship scoring."""
    ranking = VolumeMomentumRanking()

    # Create uptrending data for positive MA signals
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    prices = np.linspace(80, 120, 100)  # Clear uptrend

    data = pd.DataFrame({"date": dates, "open": prices, "high": prices, "low": prices, "close": prices, "volume": np.full(100, 1000000)})

    ranking.filtered_pl_df = pl.from_pandas(data)
    ma_score = ranking._calculate_ma_score()

    assert 0 <= ma_score <= 100  # MA score should be in valid range
    assert ma_score > 50  # Should be positive for uptrending data


def test_momentum_calculation() -> None:
    """Test short-term momentum scoring."""
    ranking = VolumeMomentumRanking()

    # Create recent uptrend for positive momentum
    dates = pd.date_range(start="2024-01-01", periods=30, freq="D")

    # Strong recent momentum
    early_prices = np.full(15, 100)
    late_prices = np.linspace(100, 110, 15)  # 10% gain in last 15 days
    prices = np.concatenate([early_prices, late_prices])

    data = pd.DataFrame({"date": dates, "open": prices, "high": prices, "low": prices, "close": prices, "volume": np.full(30, 1000000)})

    ranking.filtered_pl_df = pl.from_pandas(data)
    momentum_score = ranking._calculate_momentum_score()

    assert momentum_score > 0  # Should be positive for uptrending data
    assert momentum_score <= 100  # Should be within valid range


def test_ranking_score_bounds() -> None:
    """Test that ranking scores are always within bounds."""
    ranking = VolumeMomentumRanking()

    # Test with various data scenarios
    for _ in range(10):
        data = create_test_data(150)
        target_date = datetime(2024, 4, 1)

        score = ranking.ranking(data, target_date)
        assert 0 <= score <= 100, f"Score {score} is out of bounds"


def test_ranking_with_missing_data() -> None:
    """Test ranking behavior with missing/invalid data."""
    ranking = VolumeMomentumRanking()

    # Create data with some NaN values
    data = create_test_data(100)
    data.loc[50:60, "close"] = np.nan  # Insert missing data
    data.loc[70:80, "volume"] = np.nan

    target_date = datetime(2024, 3, 1)

    # Should handle missing data gracefully
    score = ranking.ranking(data, target_date)
    assert 0 <= score <= 100  # Should still return valid score


def test_ranking_deterministic() -> None:
    """Test that ranking is deterministic for same input."""
    ranking1 = VolumeMomentumRanking()
    ranking2 = VolumeMomentumRanking()

    data = create_test_data(100)
    target_date = datetime(2024, 3, 1)

    score1 = ranking1.ranking(data, target_date)
    score2 = ranking2.ranking(data, target_date)

    assert score1 == score2  # Should be deterministic


# ---------------------------------------------------------------------------
# _linear_rank
# ---------------------------------------------------------------------------


def test_linear_rank_at_ceiling_returns_max_score() -> None:
    assert RankingStrategy._linear_rank(0.20, 0.05, 0.20, 25) == 25


def test_linear_rank_above_ceiling_returns_max_score() -> None:
    assert RankingStrategy._linear_rank(0.50, 0.05, 0.20, 25) == 25


def test_linear_rank_at_floor_returns_0() -> None:
    assert RankingStrategy._linear_rank(0.05, 0.05, 0.20, 25) == 0


def test_linear_rank_below_floor_returns_0() -> None:
    assert RankingStrategy._linear_rank(0.04, 0.05, 0.20, 25) == 0


def test_linear_rank_midpoint_momentum_params() -> None:
    # midpoint of [0.05, 0.20] = 0.125 → int(25 * 0.5) = 12
    assert RankingStrategy._linear_rank(0.125, 0.05, 0.20, 25) == 12


def test_linear_rank_at_ceiling_volatility_params() -> None:
    assert RankingStrategy._linear_rank(1.5, 0.5, 1.5, 25) == 25


def test_linear_rank_at_floor_volatility_params() -> None:
    assert RankingStrategy._linear_rank(0.5, 0.5, 1.5, 25) == 0


def test_linear_rank_midpoint_volatility_params() -> None:
    # midpoint of [0.5, 1.5] = 1.0 → int(25 * 0.5) = 12
    assert RankingStrategy._linear_rank(1.0, 0.5, 1.5, 25) == 12


def test_linear_rank_floor_equals_ceiling_at_value_returns_max_score() -> None:
    # value >= ceiling short-circuits before the division, so no ZeroDivisionError
    assert RankingStrategy._linear_rank(0.5, 0.5, 0.5) == 20


def test_linear_rank_floor_equals_ceiling_below_value_returns_0() -> None:
    assert RankingStrategy._linear_rank(0.4, 0.5, 0.5) == 0


# ---------------------------------------------------------------------------
# _liquidity_quality band coverage
# ---------------------------------------------------------------------------


def _make_constant_df(n: int, price: float, volume: float) -> pl.DataFrame:
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    prices = np.full(n, price)
    volumes = np.full(n, volume)
    df = pd.DataFrame({"date": dates, "open": prices, "high": prices, "low": prices, "close": prices, "volume": volumes})
    return pl.from_pandas(df)


def test_liquidity_quality_band_1m_to_5m() -> None:
    # dollar_volume = 10.0 * 200_000 = 2_000_000 → volume_score = 0.8
    # constant volumes → cv = 0 → consistency_score = 1.5
    # final = min(25, int(25 * 1.5 * 0.8)) = min(25, 30) = 25
    ranking = VolumeMomentumRanking()
    ranking.filtered_pl_df = _make_constant_df(60, price=10.0, volume=200_000)
    assert ranking._liquidity_quality() == 25


def test_liquidity_quality_band_500k_to_1m() -> None:
    # dollar_volume = 10.0 * 70_000 = 700_000 → volume_score = 0.5
    # final = min(25, int(25 * 1.5 * 0.5)) = 18
    ranking = VolumeMomentumRanking()
    ranking.filtered_pl_df = _make_constant_df(60, price=10.0, volume=70_000)
    assert ranking._liquidity_quality() == 18


def test_liquidity_quality_below_all_bands() -> None:
    # dollar_volume = 5.0 * 40_000 = 200_000 → volume_score = 0.0 → score = 0
    ranking = VolumeMomentumRanking()
    ranking.filtered_pl_df = _make_constant_df(60, price=5.0, volume=40_000)
    assert ranking._liquidity_quality() == 0


def _make_alternating_df(n: int, price: float, vol_low: float, vol_high: float) -> pl.DataFrame:
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    prices = np.full(n, price)
    volumes = np.tile([vol_low, vol_high], n // 2 + 1)[:n].astype(float)
    df = pd.DataFrame({"date": dates, "open": prices, "high": prices, "low": prices, "close": prices, "volume": volumes})
    return pl.from_pandas(df)


def test_liquidity_quality_band_above_5m_exceeds_1m_band() -> None:
    # Both use alternating [20_000, 180_000] → avg_volume=100_000, CV≈0.807, consistency≈0.693
    # price=100 → dollar_volume=10M → vol_score=1.0 → int(25*0.693*1.0) = 17
    # price=20  → dollar_volume=2M  → vol_score=0.8 → int(25*0.693*0.8) = 13
    ranking_5m = VolumeMomentumRanking()
    ranking_5m.filtered_pl_df = _make_alternating_df(60, price=100.0, vol_low=20_000, vol_high=180_000)
    score_5m = ranking_5m._liquidity_quality()

    ranking_1m = VolumeMomentumRanking()
    ranking_1m.filtered_pl_df = _make_alternating_df(60, price=20.0, vol_low=20_000, vol_high=180_000)
    score_1m = ranking_1m._liquidity_quality()

    assert score_5m == 17
    assert score_1m == 13
    assert score_5m > score_1m


# ---------------------------------------------------------------------------
# interpolation paths for refactored methods
# ---------------------------------------------------------------------------


def test_volume_weighted_momentum_interpolation_path() -> None:
    # price_momentum = (110 - 100) / 100 = 0.10, in (0.05, 0.20)
    # height=21 < 60 → volume_factor = 1.0 < 1.2 → score = int(base * 0.5)
    # base = _linear_rank(0.10, 0.05, 0.20, 25) = int(25 * 0.05/0.15) = 8
    # score = int(8 * 0.5) = 4
    ranking = VolumeMomentumRanking()
    prices = [100.0] * 20 + [110.0]
    dates = pd.date_range("2024-01-01", periods=21, freq="D")
    df = pd.DataFrame({"date": dates, "open": prices, "high": prices, "low": prices, "close": prices, "volume": np.full(21, 1_000_000)})
    ranking.filtered_pl_df = pl.from_pandas(df)
    assert ranking._volume_weighted_momentum() == 4


def test_volatility_adjusted_strength_interpolation_path() -> None:
    # Alternating prices create ~2% daily vol; linear drift gives ~1.8% 60-day return.
    # risk_adjusted_return ≈ 0.018 / 0.020 ≈ 0.9 → in (0.5, 1.5) → score in (0, 25)
    ranking = VolumeMomentumRanking()
    n = 65
    i = np.arange(n)
    prices = 100.0 + (i % 2) * 2.0 + i * 0.03  # alternating ±2 + small upward drift
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    df = pd.DataFrame({"date": dates, "open": prices, "high": prices, "low": prices, "close": prices, "volume": np.full(n, 1_000_000)})
    ranking.filtered_pl_df = pl.from_pandas(df)
    score = ranking._volatility_adjusted_strength()
    assert 0 < score < 25
