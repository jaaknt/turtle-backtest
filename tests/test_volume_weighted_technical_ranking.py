import pandas as pd
import numpy as np
import warnings
from datetime import datetime

from turtle.ranking.volume_weighted_technical import VolumeWeightedTechnicalRanking

with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore", category=DeprecationWarning, module="pkg_resources"
    )


def create_test_data(length: int = 100) -> pd.DataFrame:
    """Create test OHLCV data for ranking tests."""
    dates = pd.date_range(start='2024-01-01', periods=length, freq='D')

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

    return pd.DataFrame({
        'hdate': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes
    })


def test_ranking_initialization():
    """Test VolumeWeightedTechnicalRanking initialization."""
    ranking = VolumeWeightedTechnicalRanking()
    assert ranking.market_benchmark == "SPY"

    ranking_custom = VolumeWeightedTechnicalRanking(market_benchmark="QQQ")
    assert ranking_custom.market_benchmark == "QQQ"


def test_ranking_with_insufficient_data():
    """Test ranking behavior with insufficient data."""
    ranking = VolumeWeightedTechnicalRanking()

    # Test with very limited data (less than 130 required)
    short_data = create_test_data(50)
    target_date = datetime(2024, 2, 19)

    score = ranking.ranking(short_data, target_date)
    assert score <= 10  # Should return low score for insufficient data


def test_ranking_with_valid_data():
    """Test ranking with sufficient data."""
    ranking = VolumeWeightedTechnicalRanking()

    # Create data with sufficient history
    data = create_test_data(150)
    target_date = datetime(2024, 5, 1)

    score = ranking.ranking(data, target_date)
    assert 0 <= score <= 100  # Score should be in valid range


def test_volume_weighted_momentum_component():
    """Test volume-weighted momentum calculation."""
    ranking = VolumeWeightedTechnicalRanking()

    # Create trending data with volume confirmation
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')

    # Strong uptrending prices to meet new selectivity requirements
    prices = np.linspace(80, 120, 100)  # 50% gain over period for stronger momentum

    # Higher volume on recent days (volume confirmation) - meet new 1.2x threshold
    volumes = np.concatenate([
        np.full(50, 1000000),    # Lower volume early
        np.full(50, 2500000)     # Higher volume later (2.5x increase)
    ])

    data = pd.DataFrame({
        'hdate': dates,
        'open': prices,
        'high': prices * 1.01,
        'low': prices * 0.99,
        'close': prices,
        'volume': volumes
    })

    ranking.filtered_df = data
    momentum_score = ranking._volume_weighted_momentum()

    assert momentum_score > 0  # Should be positive for uptrending + volume
    assert momentum_score <= 25  # Max score is 25


def test_volatility_adjusted_strength_component():
    """Test volatility-adjusted strength calculation."""
    ranking = VolumeWeightedTechnicalRanking()

    # Create stable uptrending data (good risk-adjusted return)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')

    # Steady uptrend with low volatility
    prices = np.linspace(90, 110, 100)
    small_noise = np.random.normal(0, 0.005, 100)  # Very low volatility
    prices = prices + small_noise

    data = pd.DataFrame({
        'hdate': dates,
        'open': prices,
        'high': prices * 1.005,
        'low': prices * 0.995,
        'close': prices,
        'volume': np.full(100, 1000000)
    })

    ranking.filtered_df = data
    strength_score = ranking._volatility_adjusted_strength()

    assert strength_score >= 0  # Should be non-negative
    assert strength_score <= 25  # Max score is 25


def test_liquidity_quality_component():
    """Test liquidity quality calculation."""
    ranking = VolumeWeightedTechnicalRanking()

    # Create data with good liquidity
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    prices = np.full(100, 100.0)  # Stable price

    # Consistent high volume (good liquidity) - meet new $5M+ requirement
    volumes = np.random.normal(6000000, 500000, 100)  # $600M daily volume
    volumes = np.abs(volumes)  # Ensure positive

    data = pd.DataFrame({
        'hdate': dates,
        'open': prices,
        'high': prices,
        'low': prices,
        'close': prices,
        'volume': volumes
    })

    ranking.filtered_df = data
    liquidity_score = ranking._liquidity_quality()

    assert liquidity_score > 0  # Should be positive for good liquidity
    assert liquidity_score <= 25  # Max score is 25


def test_technical_confluence_component():
    """Test technical confluence calculation."""
    ranking = VolumeWeightedTechnicalRanking()

    # Create data suitable for technical analysis
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')

    # Gradual uptrend for positive technical signals
    base_prices = np.linspace(90, 110, 100)
    noise = np.random.normal(0, 0.01, 100)
    prices = base_prices + noise

    data = pd.DataFrame({
        'hdate': dates,
        'open': prices,
        'high': prices * 1.01,
        'low': prices * 0.99,
        'close': prices,
        'volume': np.full(100, 1000000)
    })

    ranking.filtered_df = data
    confluence_score = ranking._technical_confluence()

    assert confluence_score >= 0  # Should be non-negative
    assert confluence_score <= 25  # Max score is 25


def test_rsi_calculation():
    """Test RSI calculation component."""
    ranking = VolumeWeightedTechnicalRanking()

    # Create oscillating data for RSI test
    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')

    # Create data that should result in RSI around 50 (neutral)
    prices = 100 + np.sin(np.linspace(0, 4*np.pi, 50)) * 5

    data = pd.DataFrame({
        'hdate': dates,
        'open': prices,
        'high': prices,
        'low': prices,
        'close': prices,
        'volume': np.full(50, 1000000)
    })

    ranking.filtered_df = data
    rsi_score = ranking._calculate_rsi_score()

    assert 0 <= rsi_score <= 100  # RSI score should be in valid range


def test_moving_average_calculation():
    """Test moving average relationship scoring."""
    ranking = VolumeWeightedTechnicalRanking()

    # Create uptrending data for positive MA signals
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    prices = np.linspace(80, 120, 100)  # Clear uptrend

    data = pd.DataFrame({
        'hdate': dates,
        'open': prices,
        'high': prices,
        'low': prices,
        'close': prices,
        'volume': np.full(100, 1000000)
    })

    ranking.filtered_df = data
    ma_score = ranking._calculate_ma_score()

    assert 0 <= ma_score <= 100  # MA score should be in valid range
    assert ma_score > 50  # Should be positive for uptrending data


def test_momentum_calculation():
    """Test short-term momentum scoring."""
    ranking = VolumeWeightedTechnicalRanking()

    # Create recent uptrend for positive momentum
    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')

    # Strong recent momentum
    early_prices = np.full(15, 100)
    late_prices = np.linspace(100, 110, 15)  # 10% gain in last 15 days
    prices = np.concatenate([early_prices, late_prices])

    data = pd.DataFrame({
        'hdate': dates,
        'open': prices,
        'high': prices,
        'low': prices,
        'close': prices,
        'volume': np.full(30, 1000000)
    })

    ranking.filtered_df = data
    momentum_score = ranking._calculate_momentum_score()

    assert momentum_score > 0  # Should be positive for uptrending data
    assert momentum_score <= 100  # Should be within valid range


def test_ranking_score_bounds():
    """Test that ranking scores are always within bounds."""
    ranking = VolumeWeightedTechnicalRanking()

    # Test with various data scenarios
    for _ in range(10):
        data = create_test_data(150)
        target_date = datetime(2024, 4, 1)

        score = ranking.ranking(data, target_date)
        assert 0 <= score <= 100, f"Score {score} is out of bounds"


def test_ranking_with_missing_data():
    """Test ranking behavior with missing/invalid data."""
    ranking = VolumeWeightedTechnicalRanking()

    # Create data with some NaN values
    data = create_test_data(100)
    data.loc[50:60, 'close'] = np.nan  # Insert missing data
    data.loc[70:80, 'volume'] = np.nan

    target_date = datetime(2024, 3, 1)

    # Should handle missing data gracefully
    score = ranking.ranking(data, target_date)
    assert 0 <= score <= 100  # Should still return valid score


def test_ranking_deterministic():
    """Test that ranking is deterministic for same input."""
    ranking1 = VolumeWeightedTechnicalRanking()
    ranking2 = VolumeWeightedTechnicalRanking()

    data = create_test_data(100)
    target_date = datetime(2024, 3, 1)

    score1 = ranking1.ranking(data, target_date)
    score2 = ranking2.ranking(data, target_date)

    assert score1 == score2  # Should be deterministic
