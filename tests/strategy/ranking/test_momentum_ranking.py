from datetime import date
from turtle.strategy.ranking.momentum import MomentumRanking

import polars as pl


def _base_row(**overrides) -> dict:
    """Return a minimal valid row for MomentumRanking."""
    row = {
        "date": date(2024, 6, 1),
        "open": 50.0,
        "high": 52.0,
        "low": 49.0,
        "close": 50.0,
        "volume": 1_000_000,
        "ema_200": 48.0,
    }
    row.update(overrides)
    return row


def _df(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(rows)


def _df_with_row(**overrides) -> pl.DataFrame:
    return _df([_base_row(**overrides)])


def _make_df(n: int, close: float = 50.0, ema_200: float = 48.0, **overrides) -> pl.DataFrame:
    """Build an n-row DataFrame with sequential dates."""
    rows = [
        _base_row(
            date=date(2024, 1, 1).__class__.fromordinal(date(2024, 1, 1).toordinal() + i),
            close=close,
            ema_200=ema_200,
            **overrides,
        )
        for i in range(n)
    ]
    return _df(rows)


# ---------------------------------------------------------------------------
# _price_to_ranking
# ---------------------------------------------------------------------------


def test_price_to_ranking_zero_returns_1() -> None:
    r = MomentumRanking()
    assert r._price_to_ranking(0.0) == 1


def test_price_to_ranking_negative_returns_1() -> None:
    r = MomentumRanking()
    assert r._price_to_ranking(-5.0) == 1


def test_price_to_ranking_band_0_to_10() -> None:
    r = MomentumRanking()
    assert r._price_to_ranking(5.0) == 20
    assert r._price_to_ranking(10.0) == 20


def test_price_to_ranking_band_10_to_20() -> None:
    r = MomentumRanking()
    assert r._price_to_ranking(10.01) == 16
    assert r._price_to_ranking(20.0) == 16


def test_price_to_ranking_band_20_to_60() -> None:
    r = MomentumRanking()
    assert r._price_to_ranking(40.0) == 12
    assert r._price_to_ranking(60.0) == 12


def test_price_to_ranking_band_60_to_240() -> None:
    r = MomentumRanking()
    assert r._price_to_ranking(100.0) == 8
    assert r._price_to_ranking(240.0) == 8


def test_price_to_ranking_band_240_to_1000() -> None:
    r = MomentumRanking()
    assert r._price_to_ranking(500.0) == 4
    assert r._price_to_ranking(1000.0) == 4


def test_price_to_ranking_above_1000_returns_1() -> None:
    r = MomentumRanking()
    assert r._price_to_ranking(2000.0) == 1


# ---------------------------------------------------------------------------
# _linear_rank
# ---------------------------------------------------------------------------


def test_linear_rank_at_ceiling_returns_20() -> None:
    assert MomentumRanking._linear_rank(0.10, 0.00, 0.10) == 20


def test_linear_rank_above_ceiling_returns_20() -> None:
    assert MomentumRanking._linear_rank(0.50, 0.00, 0.10) == 20


def test_linear_rank_at_floor_returns_0() -> None:
    assert MomentumRanking._linear_rank(0.00, 0.00, 0.10) == 0


def test_linear_rank_below_floor_returns_0() -> None:
    assert MomentumRanking._linear_rank(-0.01, 0.00, 0.10) == 0


def test_linear_rank_midpoint_1month() -> None:
    # pct=0.05, floor=0.0, ceiling=0.10 → 50% → 10
    assert MomentumRanking._linear_rank(0.05, 0.00, 0.10) == 10


def test_linear_rank_midpoint_3month() -> None:
    # pct=0.075, floor=-0.05, ceiling=0.20 → 50% → 10
    assert MomentumRanking._linear_rank(0.075, -0.05, 0.20) == 10


def test_linear_rank_midpoint_6month() -> None:
    # pct=0.10, floor=-0.10, ceiling=0.30 → 50% → 10
    assert MomentumRanking._linear_rank(0.10, -0.10, 0.30) == 10


def test_linear_rank_3month_at_floor() -> None:
    assert MomentumRanking._linear_rank(-0.05, -0.05, 0.20) == 0


def test_linear_rank_3month_below_floor_returns_0() -> None:
    assert MomentumRanking._linear_rank(-0.10, -0.05, 0.20) == 0


def test_linear_rank_6month_at_floor() -> None:
    assert MomentumRanking._linear_rank(-0.10, -0.10, 0.30) == 0


# ---------------------------------------------------------------------------
# _ranking_ema200_* min-height guards
# ---------------------------------------------------------------------------


def test_ranking_ema200_1month_insufficient_data_returns_0() -> None:
    r = MomentumRanking()
    assert r._ranking_ema200_1month(_make_df(20)) == 0


def test_ranking_ema200_1month_exact_min_height_proceeds() -> None:
    r = MomentumRanking()
    # 21 rows, last ema_200 == first ema_200 → 0% change → score 0 (not guard 0)
    result = r._ranking_ema200_1month(_make_df(21, ema_200=48.0))
    assert isinstance(result, int)


def test_ranking_ema200_3month_insufficient_data_returns_0() -> None:
    r = MomentumRanking()
    assert r._ranking_ema200_3month(_make_df(65)) == 0


def test_ranking_ema200_3month_exact_min_height_proceeds() -> None:
    r = MomentumRanking()
    result = r._ranking_ema200_3month(_make_df(66, ema_200=48.0))
    assert isinstance(result, int)


def test_ranking_ema200_6month_insufficient_data_returns_0() -> None:
    r = MomentumRanking()
    assert r._ranking_ema200_6month(_make_df(130)) == 0


def test_ranking_ema200_6month_exact_min_height_proceeds() -> None:
    r = MomentumRanking()
    result = r._ranking_ema200_6month(_make_df(131, ema_200=48.0))
    assert isinstance(result, int)


# ---------------------------------------------------------------------------
# _ranking_ema200_* scoring
# ---------------------------------------------------------------------------


def test_ranking_ema200_1month_max_score() -> None:
    """EMA200 grew >= 10% over 20 days → 20 pts."""
    r = MomentumRanking()
    ema_vals = [40.0] * 20 + [50.0]  # 50/40 - 1 = 25% → clearly above 10% ceiling
    rows = [_base_row(date=date.fromordinal(date(2024, 1, 1).toordinal() + i), ema_200=v) for i, v in enumerate(ema_vals)]
    assert r._ranking_ema200_1month(_df(rows)) == 20


def test_ranking_ema200_1month_zero_growth() -> None:
    """Flat EMA200 → 0 pts."""
    r = MomentumRanking()
    assert r._ranking_ema200_1month(_make_df(21, ema_200=48.0)) == 0


def test_ranking_ema200_1month_negative_growth() -> None:
    """EMA200 declined → 0 pts."""
    r = MomentumRanking()
    ema_vals = [52.0] * 20 + [48.0]
    rows = [_base_row(date=date.fromordinal(date(2024, 1, 1).toordinal() + i), ema_200=v) for i, v in enumerate(ema_vals)]
    assert r._ranking_ema200_1month(_df(rows)) == 0


def test_ranking_ema200_3month_max_score() -> None:
    """EMA200 grew >= 20% over 65 days → 20 pts."""
    r = MomentumRanking()
    ema_vals = [40.0] * 65 + [48.0]  # 48/40 - 1 = 20%
    rows = [_base_row(date=date.fromordinal(date(2024, 1, 1).toordinal() + i), ema_200=v) for i, v in enumerate(ema_vals)]
    assert r._ranking_ema200_3month(_df(rows)) == 20


def test_ranking_ema200_6month_max_score() -> None:
    """EMA200 grew >= 30% over 130 days → 20 pts."""
    r = MomentumRanking()
    ema_vals = [40.0] * 130 + [52.0]  # 52/40 - 1 = 30%
    rows = [_base_row(date=date.fromordinal(date(2024, 1, 1).toordinal() + i), ema_200=v) for i, v in enumerate(ema_vals)]
    assert r._ranking_ema200_6month(_df(rows)) == 20


# ---------------------------------------------------------------------------
# _ranking_period_high
# ---------------------------------------------------------------------------


def test_ranking_period_high_insufficient_data_returns_0() -> None:
    r = MomentumRanking()
    assert r._ranking_period_high(_make_df(1)) == 0


def test_ranking_period_high_not_period_max_returns_0() -> None:
    """Current close below a prior close → 0."""
    r = MomentumRanking()
    rows = (
        [_base_row(date=date(2024, 1, 1), close=60.0)]
        + [_base_row(date=date.fromordinal(date(2024, 1, 1).toordinal() + i + 1), close=50.0) for i in range(10)]
    )
    assert r._ranking_period_high(_df(rows)) == 0


def test_ranking_period_high_null_close_returns_0() -> None:
    """All-null close column returns 0."""
    r = MomentumRanking()
    df = _make_df(5).with_columns(pl.lit(None).cast(pl.Float64).alias("close"))
    assert r._ranking_period_high(df) == 0


def test_ranking_period_high_full_365_days_returns_20() -> None:
    """Current close is the max over a full 365-day lookback → score 20."""
    r = MomentumRanking()
    assert r._ranking_period_high(_make_df(365)) == 20


def test_ranking_period_high_short_history_returns_low_score() -> None:
    """Current close is max but only 50 days of history → low score."""
    r = MomentumRanking()
    # 50 rows all at same close → days_as_high = 50 → int(20 * 50/365) = 2
    score = r._ranking_period_high(_make_df(50))
    assert 1 <= score < 20


# ---------------------------------------------------------------------------
# ranking() integration
# ---------------------------------------------------------------------------


def test_ranking_empty_df_returns_0() -> None:
    r = MomentumRanking()
    df = pl.DataFrame([_base_row()]).clear()
    assert r.ranking(df, date(2024, 6, 1)) == 0


def test_ranking_returns_int() -> None:
    r = MomentumRanking()
    assert isinstance(r.ranking(_df_with_row(), date(2024, 6, 1)), int)


def test_ranking_date_filter_excludes_future_rows() -> None:
    r = MomentumRanking()
    rows = [
        _base_row(date=date(2024, 5, 31), close=50.0),
        _base_row(date=date(2024, 6, 1), close=50.0),
        _base_row(date=date(2024, 6, 2), close=9999.0),  # future — must be excluded
    ]
    score_with_future = r.ranking(_df(rows), date(2024, 6, 1))
    score_without_future = r.ranking(_df(rows[:2]), date(2024, 6, 1))
    assert score_with_future == score_without_future


def test_ranking_price_component_only_for_short_df() -> None:
    """With only 1 row all EMA and period-high components are 0; only price contributes."""
    r = MomentumRanking()
    # close=5.0 → price band score=20; all other components=0
    score = r.ranking(_df_with_row(close=5.0), date(2024, 6, 1))
    assert score == 20


def test_ranking_in_valid_range() -> None:
    r = MomentumRanking()
    score = r.ranking(_df_with_row(), date(2024, 6, 1))
    assert 0 <= score <= 100
