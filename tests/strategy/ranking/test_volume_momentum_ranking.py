import warnings
from datetime import date, datetime, timedelta
from turtle.strategy.ranking.base import RankingStrategy
from turtle.strategy.ranking.volume_momentum import VolumeMomentumRanking

import numpy as np
import polars as pl

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="pkg_resources")


def create_test_data(length: int = 100) -> pl.DataFrame:
    """Create test OHLCV data for ranking tests."""
    start = date(2024, 1, 1)
    dates = [start + timedelta(days=i) for i in range(length)]

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

    return pl.DataFrame({
        "date": dates, "open": opens.tolist(), "high": highs.tolist(),
        "low": lows.tolist(), "close": closes.tolist(), "volume": volumes.tolist(),
    })


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
    dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(100)]

    # Strong uptrending prices to meet new selectivity requirements
    prices = np.linspace(80, 120, 100)  # 50% gain over period for stronger momentum

    # Higher volume on recent days (volume confirmation) - meet new 1.2x threshold
    volumes = np.concatenate(
        [
            np.full(50, 1000000),  # Lower volume early
            np.full(50, 2500000),  # Higher volume later (2.5x increase)
        ]
    )

    df = pl.DataFrame({
        "date": dates, "open": prices.tolist(), "high": (prices * 1.01).tolist(),
        "low": (prices * 0.99).tolist(), "close": prices.tolist(), "volume": volumes.tolist(),
    })
    momentum_score = ranking._volume_weighted_momentum(df)

    assert momentum_score > 0  # Should be positive for uptrending + volume
    assert momentum_score <= 25  # Max score is 25


def test_volatility_adjusted_strength_component() -> None:
    """Test volatility-adjusted strength calculation."""
    ranking = VolumeMomentumRanking()

    # Create stable uptrending data (good risk-adjusted return)
    dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(100)]

    # Steady uptrend with low volatility
    prices = np.linspace(90, 110, 100)
    small_noise = np.random.normal(0, 0.005, 100)  # Very low volatility
    prices = prices + small_noise

    df = pl.DataFrame({
        "date": dates, "open": prices.tolist(), "high": (prices * 1.005).tolist(),
        "low": (prices * 0.995).tolist(), "close": prices.tolist(), "volume": [1000000] * 100,
    })
    strength_score = ranking._volatility_adjusted_strength(df)

    assert strength_score > 0  # Steady uptrend should score positively
    assert strength_score <= 25  # Max score is 25


def test_liquidity_quality_component() -> None:
    """Test liquidity quality calculation."""
    ranking = VolumeMomentumRanking()

    # Create data with good liquidity
    dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(100)]
    prices = [100.0] * 100

    # Consistent high volume (good liquidity) - meet new $5M+ requirement
    volumes = np.abs(np.random.normal(6000000, 500000, 100)).tolist()  # $600M daily volume

    df = pl.DataFrame({"date": dates, "open": prices, "high": prices, "low": prices, "close": prices, "volume": volumes})
    liquidity_score = ranking._liquidity_quality(df)

    assert liquidity_score > 0  # Should be positive for good liquidity
    assert liquidity_score <= 25  # Max score is 25


def test_technical_confluence_component() -> None:
    """Test technical confluence calculation."""
    ranking = VolumeMomentumRanking()

    # Create data suitable for technical analysis
    dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(100)]

    # Gradual uptrend for positive technical signals
    base_prices = np.linspace(90, 110, 100)
    noise = np.random.normal(0, 0.01, 100)
    prices = base_prices + noise

    df = pl.DataFrame({
        "date": dates, "open": prices.tolist(), "high": (prices * 1.01).tolist(),
        "low": (prices * 0.99).tolist(), "close": prices.tolist(), "volume": [1000000] * 100,
    })
    confluence_score = ranking._technical_confluence(df)

    assert confluence_score >= 0  # Should be non-negative
    assert confluence_score <= 25  # Max score is 25


def test_rsi_calculation() -> None:
    """Test RSI calculation component."""
    ranking = VolumeMomentumRanking()

    # Create oscillating data for RSI test
    dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(50)]

    # Create data that should result in RSI around 50 (neutral)
    prices = (100 + np.sin(np.linspace(0, 4 * np.pi, 50)) * 5).tolist()

    df = pl.DataFrame({"date": dates, "open": prices, "high": prices, "low": prices, "close": prices, "volume": [1000000] * 50})
    rsi_score = ranking._calculate_rsi_score(df)

    assert 0 <= rsi_score <= 100  # RSI score should be in valid range


def test_rsi_no_losses_returns_100() -> None:
    """Monotonically rising prices → avg_loss == 0 → RSI=100 → score 100."""
    ranking = VolumeMomentumRanking()
    dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(20)]
    prices = [100.0 + i for i in range(20)]
    df = pl.DataFrame({"date": dates, "close": prices, "open": prices, "high": prices, "low": prices, "volume": [1_000_000] * 20})
    assert ranking._calculate_rsi_score(df) == 100


def test_rsi_overbought_score_below_60() -> None:
    """Series with many gains but some losses → RSI > 75 → overbought penalty → score < 60."""
    ranking = VolumeMomentumRanking()
    dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(20)]
    # 10+ up-days of +2, 3 down-days of -1 in last 14 bars → RSI ~85
    prices = [100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0, 108.0, 110.0,
              109.0, 111.0, 113.0, 115.0, 114.0, 116.0, 118.0, 120.0, 119.0, 121.0, 123.0]
    df = pl.DataFrame({"date": dates, "close": prices, "open": prices, "high": prices, "low": prices, "volume": [1_000_000] * 20})
    score = ranking._calculate_rsi_score(df)
    assert 0 <= score < 60


def test_rsi_oversold_score_below_60() -> None:
    """Monotonically falling prices → RSI very low → oversold penalty → score < 60."""
    ranking = VolumeMomentumRanking()
    dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(20)]
    prices = [max(100.0 - i * 2.0, 1.0) for i in range(20)]
    df = pl.DataFrame({"date": dates, "close": prices, "open": prices, "high": prices, "low": prices, "volume": [1_000_000] * 20})
    score = ranking._calculate_rsi_score(df)
    assert 0 <= score < 60


def test_moving_average_calculation() -> None:
    """Test moving average relationship scoring."""
    ranking = VolumeMomentumRanking()

    # Create uptrending data for positive MA signals
    dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(100)]
    prices = np.linspace(80, 120, 100).tolist()  # Clear uptrend

    df = pl.DataFrame({"date": dates, "open": prices, "high": prices, "low": prices, "close": prices, "volume": [1000000] * 100})
    ma_score = ranking._calculate_ma_score(df)

    assert 0 <= ma_score <= 100  # MA score should be in valid range
    assert ma_score > 50  # Should be positive for uptrending data


def test_ma_score_price_below_ema_returns_0() -> None:
    """Price below EMA20 (downtrend) → returns 0."""
    ranking = VolumeMomentumRanking()
    dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(100)]
    prices = np.linspace(120, 80, 100).tolist()  # clear downtrend
    df = pl.DataFrame({"date": dates, "open": prices, "high": prices, "low": prices, "close": prices, "volume": [1_000_000] * 100})
    assert ranking._calculate_ma_score(df) == 0


def test_momentum_calculation() -> None:
    """Test short-term momentum scoring."""
    ranking = VolumeMomentumRanking()

    # Create recent uptrend for positive momentum
    dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(30)]

    # Strong recent momentum
    early_prices = np.full(15, 100)
    late_prices = np.linspace(100, 110, 15)  # 10% gain in last 15 days
    prices = np.concatenate([early_prices, late_prices]).tolist()

    df = pl.DataFrame({"date": dates, "open": prices, "high": prices, "low": prices, "close": prices, "volume": [1000000] * 30})
    momentum_score = ranking._calculate_momentum_score(df)

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
    """Test ranking behavior with missing/invalid data — uses 200 rows to exercise null-handling code."""
    ranking = VolumeMomentumRanking()

    data = create_test_data(200).with_row_index("_idx").with_columns(
        pl.when(pl.col("_idx").is_between(100, 110)).then(None).otherwise(pl.col("close")).alias("close"),
        pl.when(pl.col("_idx").is_between(150, 160)).then(None).otherwise(pl.col("volume")).alias("volume"),
    ).drop("_idx")

    target_date = datetime(2024, 8, 1)  # After all 200 rows

    score = ranking.ranking(data, target_date)
    assert 0 <= score <= 100


def test_ranking_deterministic() -> None:
    """Test that ranking is deterministic for same input."""
    ranking1 = VolumeMomentumRanking()
    ranking2 = VolumeMomentumRanking()

    data = create_test_data(100)
    target_date = datetime(2024, 3, 1)

    score1 = ranking1.ranking(data, target_date)
    score2 = ranking2.ranking(data, target_date)

    assert score1 == score2  # Should be deterministic


def test_ranking_volume_momentum_quality_gate() -> None:
    """Flat prices produce volume_momentum=0 which fails the <5 gate → returns 1."""
    ranking = VolumeMomentumRanking()
    start = date(2024, 1, 1)
    dates = [start + timedelta(days=i) for i in range(150)]
    prices = [100.0] * 150
    data = pl.DataFrame({
        "date": dates,
        "open": prices, "high": prices, "low": prices, "close": prices,
        "volume": [1_000_000.0] * 150,
    })
    score = ranking.ranking(data, datetime(2024, 5, 1))
    assert score == 1


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


def test_linear_rank_nan_returns_0() -> None:
    assert RankingStrategy._linear_rank(float("nan"), 0.0, 1.0) == 0


# ---------------------------------------------------------------------------
# _liquidity_quality band coverage
# ---------------------------------------------------------------------------


def _make_constant_df(n: int, price: float, volume: float) -> pl.DataFrame:
    start = date(2024, 1, 1)
    dates = [start + timedelta(days=i) for i in range(n)]
    prices = [price] * n
    volumes = [volume] * n
    return pl.DataFrame({"date": dates, "open": prices, "high": prices, "low": prices, "close": prices, "volume": volumes})


def test_liquidity_quality_band_1m_to_5m() -> None:
    # dollar_volume = 10.0 * 200_000 = 2_000_000 → volume_score = 0.8
    # constant volumes → cv = 0 → consistency_score = 1.5
    # final = min(25, int(25 * 1.5 * 0.8)) = min(25, 30) = 25
    ranking = VolumeMomentumRanking()
    df = _make_constant_df(60, price=10.0, volume=200_000)
    assert ranking._liquidity_quality(df) == 25


def test_liquidity_quality_band_500k_to_1m() -> None:
    # dollar_volume = 10.0 * 70_000 = 700_000 → volume_score = 0.5
    # final = min(25, int(25 * 1.5 * 0.5)) = 18
    ranking = VolumeMomentumRanking()
    df = _make_constant_df(60, price=10.0, volume=70_000)
    assert ranking._liquidity_quality(df) == 18


def test_liquidity_quality_below_all_bands() -> None:
    # dollar_volume = 5.0 * 40_000 = 200_000 → volume_score = 0.0 → score = 0
    ranking = VolumeMomentumRanking()
    df = _make_constant_df(60, price=5.0, volume=40_000)
    assert ranking._liquidity_quality(df) == 0


def _make_alternating_df(n: int, price: float, vol_low: float, vol_high: float) -> pl.DataFrame:
    start = date(2024, 1, 1)
    dates = [start + timedelta(days=i) for i in range(n)]
    prices = [price] * n
    volumes = np.tile([vol_low, vol_high], n // 2 + 1)[:n].tolist()
    return pl.DataFrame({"date": dates, "open": prices, "high": prices, "low": prices, "close": prices, "volume": volumes})


def test_liquidity_quality_band_above_5m_exceeds_1m_band() -> None:
    # Both use alternating [20_000, 180_000] → avg_volume=100_000, CV≈0.807, consistency≈0.693
    # price=100 → dollar_volume=10M → vol_score=1.0 → int(25*0.693*1.0) = 17
    # price=20  → dollar_volume=2M  → vol_score=0.8 → int(25*0.693*0.8) = 13
    ranking_5m = VolumeMomentumRanking()
    score_5m = ranking_5m._liquidity_quality(_make_alternating_df(60, price=100.0, vol_low=20_000, vol_high=180_000))

    ranking_1m = VolumeMomentumRanking()
    score_1m = ranking_1m._liquidity_quality(_make_alternating_df(60, price=20.0, vol_low=20_000, vol_high=180_000))

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
    dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(21)]
    df = pl.DataFrame({"date": dates, "open": prices, "high": prices, "low": prices, "close": prices, "volume": [1_000_000] * 21})
    assert ranking._volume_weighted_momentum(df) == 4


def test_volatility_adjusted_strength_interpolation_path() -> None:
    # Alternating prices create ~2% daily vol; linear drift gives ~1.8% 60-day return.
    # risk_adjusted_return ≈ 0.018 / 0.020 ≈ 0.9 → in (0.5, 1.5) → score in (0, 25)
    ranking = VolumeMomentumRanking()
    n = 65
    i = np.arange(n)
    prices = (100.0 + (i % 2) * 2.0 + i * 0.03).tolist()  # alternating ±2 + small upward drift
    dates = [date(2024, 1, 1) + timedelta(days=j) for j in range(n)]
    df = pl.DataFrame({"date": dates, "open": prices, "high": prices, "low": prices, "close": prices, "volume": [1_000_000] * n})
    score = ranking._volatility_adjusted_strength(df)
    assert 0 < score < 25
