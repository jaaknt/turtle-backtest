from datetime import datetime
from turtle.strategy.ranking.breakout_quality import BreakoutQualityRanking

import polars as pl


def _base_row(**overrides) -> dict:
    """Return a minimal valid row for BreakoutQualityRanking."""
    row = {
        "date": datetime(2024, 6, 1),
        "open": 100.0,
        "high": 108.0,
        "low": 99.0,
        "close": 107.0,
        "volume": 2_000_000,
        "ema_volume_10": 1_000_000,  # volume ratio = 2.0 → 20 pts
        "max_close_20": 105.0,  # extension = (107-105)/105*100 ≈ 1.9% → 10 pts
        "ema_10": 104.0,
        "ema_20": 102.0,
        "ema_50": 100.0,
        "ema_200": 95.0,  # pct_above ≈ 12.6% → in sweet spot
        "macd": 0.50,
        "macd_signal": 0.20,  # gap = 0.30/107*100 ≈ 0.28% → 15 pts
    }
    row.update(overrides)
    return row


def _df_with_row(**overrides) -> pl.DataFrame:
    return pl.DataFrame([_base_row(**overrides)])


# ---------------------------------------------------------------------------
# Instantiation
# ---------------------------------------------------------------------------


def test_instantiation() -> None:
    ranking = BreakoutQualityRanking()
    assert isinstance(ranking, BreakoutQualityRanking)


# ---------------------------------------------------------------------------
# Volume Conviction
# ---------------------------------------------------------------------------


def test_volume_conviction_max() -> None:
    ranking = BreakoutQualityRanking()
    row = _base_row(volume=3_100_000, ema_volume_10=1_000_000)
    assert ranking._volume_conviction(row) == 30


def test_volume_conviction_mid() -> None:
    ranking = BreakoutQualityRanking()
    row = _base_row(volume=1_600_000, ema_volume_10=1_000_000)
    assert ranking._volume_conviction(row) == 10


def test_volume_conviction_zero_below_threshold() -> None:
    ranking = BreakoutQualityRanking()
    row = _base_row(volume=1_100_000, ema_volume_10=1_000_000)
    assert ranking._volume_conviction(row) == 0


def test_volume_conviction_missing_data() -> None:
    ranking = BreakoutQualityRanking()
    row = _base_row(volume=None, ema_volume_10=1_000_000)
    assert ranking._volume_conviction(row) == 0


# ---------------------------------------------------------------------------
# Breakout Extension
# ---------------------------------------------------------------------------


def test_breakout_extension_max() -> None:
    ranking = BreakoutQualityRanking()
    row = _base_row(close=115.0, max_close_20=100.0)  # 15% extension
    assert ranking._breakout_extension(row) == 25


def test_breakout_extension_mid() -> None:
    ranking = BreakoutQualityRanking()
    row = _base_row(close=101.5, max_close_20=100.0)  # 1.5% extension
    assert ranking._breakout_extension(row) == 10


def test_breakout_extension_zero_at_equal() -> None:
    ranking = BreakoutQualityRanking()
    row = _base_row(close=100.0, max_close_20=100.0)  # 0% extension
    assert ranking._breakout_extension(row) == 0


def test_breakout_extension_missing_data() -> None:
    ranking = BreakoutQualityRanking()
    row = _base_row(close=None, max_close_20=100.0)
    assert ranking._breakout_extension(row) == 0


# ---------------------------------------------------------------------------
# Trend Health
# ---------------------------------------------------------------------------


def test_trend_health_full_alignment_sweet_spot() -> None:
    ranking = BreakoutQualityRanking()
    # EMA stack fully aligned, close ~17.5% above EMA200 → max distance pts
    row = _base_row(close=117.5, ema_10=115.0, ema_20=112.0, ema_50=108.0, ema_200=100.0)
    score = ranking._trend_health(row)
    assert score == 25  # 15 alignment + 10 distance


def test_trend_health_partial_alignment() -> None:
    ranking = BreakoutQualityRanking()
    # Only ema50 > ema200, not full stack; close in sweet spot
    row = _base_row(close=117.5, ema_10=108.0, ema_20=110.0, ema_50=108.0, ema_200=100.0)
    score = ranking._trend_health(row)
    assert score < 25
    assert score > 0


def test_trend_health_overextended() -> None:
    ranking = BreakoutQualityRanking()
    # Close 40% above EMA200 → overextended, 0 distance pts
    row = _base_row(close=140.0, ema_10=138.0, ema_20=135.0, ema_50=130.0, ema_200=100.0)
    score = ranking._trend_health(row)
    # Gets alignment pts but 0 distance pts
    assert score == 15  # 15 alignment + 0 distance


def test_trend_health_missing_ema200() -> None:
    ranking = BreakoutQualityRanking()
    row = _base_row(ema_200=None)
    assert ranking._trend_health(row) == 0


# ---------------------------------------------------------------------------
# MACD Conviction
# ---------------------------------------------------------------------------


def test_macd_conviction_max() -> None:
    ranking = BreakoutQualityRanking()
    row = _base_row(close=100.0, macd=1.0, macd_signal=0.0)  # gap = 1.0%
    assert ranking._macd_conviction(row) == 20


def test_macd_conviction_mid() -> None:
    ranking = BreakoutQualityRanking()
    row = _base_row(close=100.0, macd=0.25, macd_signal=0.0)  # gap = 0.25%
    assert ranking._macd_conviction(row) == 10


def test_macd_conviction_zero_negative_gap() -> None:
    ranking = BreakoutQualityRanking()
    row = _base_row(close=100.0, macd=0.05, macd_signal=0.10)  # negative gap
    assert ranking._macd_conviction(row) == 0


def test_macd_conviction_missing_data() -> None:
    ranking = BreakoutQualityRanking()
    row = _base_row(macd=None)
    assert ranking._macd_conviction(row) == 0


# ---------------------------------------------------------------------------
# Full ranking() method
# ---------------------------------------------------------------------------


def test_ranking_returns_int() -> None:
    ranking = BreakoutQualityRanking()
    df = _df_with_row()
    score = ranking.ranking(df, datetime(2024, 6, 1))
    assert isinstance(score, int)


def test_ranking_in_valid_range() -> None:
    ranking = BreakoutQualityRanking()
    df = _df_with_row()
    score = ranking.ranking(df, datetime(2024, 6, 1))
    assert 0 <= score <= 100


def test_ranking_empty_df_returns_zero() -> None:
    ranking = BreakoutQualityRanking()
    df = pl.DataFrame([_base_row()]).clear()
    score = ranking.ranking(df, datetime(2024, 6, 1))
    assert score == 0


def test_ranking_date_filter() -> None:
    """Ensure rows after the signal date are excluded."""
    ranking = BreakoutQualityRanking()
    # Build a single-row df anchored to 2024-06-01 and get its expected score
    signal_row = _base_row(date=datetime(2024, 6, 1))
    expected_score = ranking.ranking(pl.DataFrame([signal_row]), datetime(2024, 6, 1))

    # Now add a future row with very different values that would change the score
    rows = [
        _base_row(date=datetime(2024, 5, 31), close=90.0, max_close_20=100.0),
        signal_row,
        _base_row(date=datetime(2024, 6, 2), volume=9_999_999, ema_volume_10=1_000, close=500.0, max_close_20=1.0),
    ]
    df = pl.DataFrame(rows)
    # Score on 2024-06-01 must equal the score computed without the future row
    assert ranking.ranking(df, datetime(2024, 6, 1)) == expected_score


def test_ranking_strong_signal_scores_high() -> None:
    """A signal with max values for all components should score near 100."""
    ranking = BreakoutQualityRanking()
    row = _base_row(
        volume=4_000_000,
        ema_volume_10=1_000_000,  # ratio=4 → 30 pts
        close=117.5,
        max_close_20=110.0,  # extension ≈ 6.8% → 25 pts
        ema_10=115.0,
        ema_20=112.0,
        ema_50=108.0,
        ema_200=100.0,  # full align + sweet spot → 25 pts
        macd=1.0,
        macd_signal=0.0,  # gap=0.85% → 20 pts
    )
    df = pl.DataFrame([row])
    score = ranking.ranking(df, datetime(2024, 6, 1))
    assert score >= 90


def test_ranking_weak_signal_scores_low() -> None:
    """A borderline signal (just meeting thresholds) should score low."""
    ranking = BreakoutQualityRanking()
    row = _base_row(
        volume=1_100_000,
        ema_volume_10=1_000_000,  # ratio=1.1 → 0 pts
        close=100.1,
        max_close_20=100.0,  # extension=0.1% → 0 pts
        ema_10=99.0,
        ema_20=100.0,
        ema_50=100.0,
        ema_200=100.0,  # misaligned → 0 pts
        macd=0.05,
        macd_signal=0.03,  # tiny gap → 0 pts
    )
    df = pl.DataFrame([row])
    score = ranking.ranking(df, datetime(2024, 6, 1))
    assert score <= 10
