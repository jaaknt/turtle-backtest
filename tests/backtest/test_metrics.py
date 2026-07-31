"""Tests for the shared trade-metrics module.

Two jobs: pin the canonical definitions, and characterize how they differ from the
hand-rolled implementations they replace, so every number that moves in a regenerated
research table is explainable by a tested ratio rather than a mystery.
"""

import ast
import math
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from turtlex.backtest import metrics as metrics_module
from turtlex.backtest.metrics import compute_daily_sortino, compute_trade_metrics, metrics_from_future_trades
from turtlex.model import FutureTrade, Signal, Trade


def make_trade(ticker: str, entry_price: float, exit_price: float, holding_days: int = 30, ranking: int = 50) -> FutureTrade:
    """Build a FutureTrade with a given entry/exit price and holding period."""
    entry_date = date(2024, 1, 1)
    exit_date = entry_date + timedelta(days=holding_days)
    return FutureTrade(
        signal=Signal(ticker=ticker, date=entry_date, ranking=ranking),
        entry=Trade(ticker=ticker, date=entry_date, price=entry_price, reason="next_day_open"),
        exit=Trade(ticker=ticker, date=exit_date, price=exit_price, reason="period_end"),
        benchmark_list=[],
    )


# Reference implementations of the code this module replaces, kept here so the migration's
# behaviour changes are asserted rather than discovered.


def _legacy_service_sortino(ann_returns_pct: list[float]) -> float:
    """turtlex/service/backtest_service.py:131-132 — ratio of annualized returns, all-N denominator."""
    n = len(ann_returns_pct)
    downside_dev = math.sqrt(sum(min(a, 0.0) ** 2 for a in ann_returns_pct) / n)
    return sum(ann_returns_pct) / n / downside_dev


def _legacy_service_ann_mean(returns_pct: list[float], holding_days: int) -> float:
    """turtlex/service/backtest_service.py:121-124 — annualize each trade, then average."""
    ann = [min(((1.0 + r / 100.0) ** (365.0 / holding_days) - 1.0) * 100.0, 9999.0) for r in returns_pct]
    return sum(ann) / len(ann)


def _legacy_cohort_sortino(rets_decimal: np.ndarray, hold_cal: int) -> float:
    """scripts/qullamaggie-cohorts-adr.py:245-250 — negatives-only denominator."""
    neg = rets_decimal[rets_decimal < 0]
    dd = float(np.sqrt(np.mean(neg**2)))
    return float(np.mean(rets_decimal) * np.sqrt(365 / hold_cal) / dd)


def _legacy_v4_ann_mean(rets_decimal: np.ndarray, hold_cal: int) -> float:
    """scripts/qullamaggie-backtest-v4.py:297 — compound the mean over the fixed hold."""
    return float(((1.0 + rets_decimal.mean()) ** (365.0 / hold_cal) - 1.0) * 100)


class TestGoldenValues:
    """Cases lifted from the retired BacktestService._compute_group_metrics suite.

    All use 365-day holds, where every annualization convention collapses to identity, so
    these values must survive the migration untouched.
    """

    def test_empty_list_returns_none(self) -> None:
        assert metrics_from_future_trades([]) is None
        assert compute_trade_metrics([], 365) is None

    def test_all_winning_trades_pf_is_inf_and_sortino_is_nan(self) -> None:
        trades = [
            make_trade("AAA", 100.0, 110.0, holding_days=365),
            make_trade("BBB", 100.0, 105.0, holding_days=365),
        ]
        result = metrics_from_future_trades(trades)

        assert result is not None
        assert result.profit_factor == float("inf")
        assert math.isnan(result.sortino)

    def test_known_returns_match_hand_computed_stats(self) -> None:
        """4 trades at +10%/+20%/-10%/-5%, all 365-day holds."""
        trades = [
            make_trade("AAA", 100.0, 110.0, holding_days=365),
            make_trade("BBB", 100.0, 120.0, holding_days=365),
            make_trade("CCC", 100.0, 90.0, holding_days=365),
            make_trade("DDD", 100.0, 95.0, holding_days=365),
        ]
        result = metrics_from_future_trades(trades)

        assert result is not None
        assert result.n == 4
        assert result.mean_pct == pytest.approx(3.75)
        assert result.ann_mean_pct == pytest.approx(3.75)
        assert result.win_pct == pytest.approx(50.0)
        # PF = gross_win / gross_loss = (10 + 20) / (10 + 5) = 2.0
        assert result.profit_factor == pytest.approx(2.0)
        # downside_dev = sqrt(mean([0, 0, 10**2, 5**2])) = sqrt(125 / 4)
        assert result.sortino == pytest.approx(3.75 / math.sqrt(125 / 4))
        # CVaR95%: n=4 -> k=max(1, floor(0.2))=1 -> worst single return
        assert result.cvar95_pct == pytest.approx(-10.0)

    def test_cvar_uses_worst_five_percent_of_larger_group(self) -> None:
        """n=20 -> k=max(1, floor(1.0))=1 -> CVaR95 is just the single worst return."""
        trades = [make_trade(f"T{i}", 100.0, 100.0 + i, holding_days=365) for i in range(-10, 10)]
        result = metrics_from_future_trades(trades)

        assert result is not None
        assert result.n == 20
        assert result.cvar95_pct == pytest.approx(-10.0)


class TestLegacyCharacterization:
    """Pin where the canonical definitions agree with the old ones, and by how much they differ."""

    RETURNS_PCT = [10.0, 20.0, -10.0, -5.0]

    def test_matches_legacy_service_sortino_at_365_day_holds(self) -> None:
        """At a 365-day hold the old service formula and the canonical one coincide exactly."""
        result = compute_trade_metrics(self.RETURNS_PCT, 365)

        assert result is not None
        assert result.sortino == pytest.approx(_legacy_service_sortino(self.RETURNS_PCT))

    def test_matches_legacy_v4_ann_mean_when_every_hold_equals_hold_cal(self) -> None:
        rets = np.array([r / 100.0 for r in self.RETURNS_PCT])
        result = compute_trade_metrics(self.RETURNS_PCT, [60.0] * 4)

        assert result is not None
        assert result.ann_mean_pct == pytest.approx(_legacy_v4_ann_mean(rets, 60))

    def test_sortino_exceeds_the_negatives_only_cohort_formula_by_sqrt_n_over_n_neg(self) -> None:
        """The 11 cohort scripts divide by RMS(losers); canonical divides by RMS(min(r,0)) over all N.

        The ratio is exactly sqrt(N / n_neg), so every Sortino in a regenerated cohort table
        must move by that factor and nothing else.
        """
        rets = np.array([r / 100.0 for r in self.RETURNS_PCT])
        n, n_neg = len(rets), int((rets < 0).sum())
        result = compute_trade_metrics(self.RETURNS_PCT, 60.0)

        assert result is not None
        assert result.sortino == pytest.approx(_legacy_cohort_sortino(rets, 60) * math.sqrt(n / n_neg))

    def test_ann_mean_diverges_from_the_legacy_service_average_of_annualized_trades(self) -> None:
        """Averaging per-trade annualized returns is dominated by short trades; compounding the mean is not."""
        result = compute_trade_metrics(self.RETURNS_PCT, 60)
        legacy = _legacy_service_ann_mean(self.RETURNS_PCT, 60)

        assert result is not None
        assert result.ann_mean_pct == pytest.approx(25.10, abs=0.01)
        assert legacy == pytest.approx(51.90, abs=0.01)  # the old column read roughly double


class TestDefinitions:
    def test_zero_returns_are_not_wins(self) -> None:
        result = compute_trade_metrics([0.0, 0.0, 10.0, -10.0], 30)

        assert result is not None
        assert result.win_pct == pytest.approx(25.0)

    def test_median_of_even_and_odd_counts(self) -> None:
        even = compute_trade_metrics([1.0, 2.0, 3.0, 10.0], 30)
        odd = compute_trade_metrics([1.0, 2.0, 30.0], 30)

        assert even is not None and odd is not None
        assert even.median_pct == pytest.approx(2.5)
        assert odd.median_pct == pytest.approx(2.0)

    @pytest.mark.parametrize(("n", "expected_k"), [(4, 1), (20, 1), (100, 5)])
    def test_cvar_k_selection(self, n: int, expected_k: int) -> None:
        returns = [float(i) for i in range(-n // 2, n // 2)]
        result = compute_trade_metrics(returns, 30)

        assert result is not None
        assert result.cvar95_pct == pytest.approx(sum(sorted(returns)[:expected_k]) / expected_k)

    def test_sortino_is_nan_below_min_losers_but_the_row_still_returns(self) -> None:
        result = compute_trade_metrics([10.0, 20.0, -5.0], 30, min_losers=3)

        assert result is not None  # the caller's table keeps the row
        assert math.isnan(result.sortino)
        assert result.n == 3
        assert result.mean_pct == pytest.approx(25.0 / 3)

    def test_holding_days_zero_skips_annualization(self) -> None:
        """Open positions marked to the latest price have no meaningful holding period."""
        result = compute_trade_metrics([10.0, -5.0], 0)

        assert result is not None
        assert result.ann_mean_pct == pytest.approx(result.mean_pct)
        # mean 2.5 / RMS(min(r,0)) = sqrt(mean([0, 25])), with no sqrt(365/hold) factor applied
        assert result.sortino == pytest.approx(2.5 / math.sqrt(12.5))

    def test_total_loss_clamps_to_minus_100(self) -> None:
        result = compute_trade_metrics([-100.0, -100.0], 30)

        assert result is not None
        assert result.ann_mean_pct == pytest.approx(-100.0)

    def test_variable_holding_periods_use_the_mean(self) -> None:
        result = compute_trade_metrics([10.0, 10.0], [30.0, 90.0])
        fixed = compute_trade_metrics([10.0, 10.0], 60.0)

        assert result is not None and fixed is not None
        assert result.ann_mean_pct == pytest.approx(fixed.ann_mean_pct)

    def test_trade_drawdowns_are_averaged_when_supplied_and_none_otherwise(self) -> None:
        with_dd = compute_trade_metrics([10.0, -5.0], 30, trade_drawdowns_pct=[4.0, 12.0])
        without_dd = compute_trade_metrics([10.0, -5.0], 30)

        assert with_dd is not None and without_dd is not None
        assert with_dd.mean_trade_mdd_pct == pytest.approx(8.0)
        assert without_dd.mean_trade_mdd_pct is None


class TestScaleInvariance:
    """Guardrail against the percent/decimal mixup this migration risks introducing."""

    @pytest.mark.parametrize("factor", [0.01, 100.0])
    def test_ratios_are_unchanged_by_rescaling_returns(self, factor: float) -> None:
        base = compute_trade_metrics([10.0, 20.0, -10.0, -5.0], 60)
        scaled = compute_trade_metrics([10.0 * factor, 20.0 * factor, -10.0 * factor, -5.0 * factor], 60)

        assert base is not None and scaled is not None
        assert scaled.sortino == pytest.approx(base.sortino)
        assert scaled.profit_factor == pytest.approx(base.profit_factor)
        assert scaled.win_pct == pytest.approx(base.win_pct)


class TestAdapterEquivalence:
    def test_future_trade_adapter_matches_the_sequence_api(self) -> None:
        trades = [
            make_trade("AAA", 100.0, 110.0, holding_days=30),
            make_trade("BBB", 100.0, 90.0, holding_days=90),
            make_trade("CCC", 100.0, 105.0, holding_days=45),
        ]

        assert metrics_from_future_trades(trades) == compute_trade_metrics(
            [t.realized_pct for t in trades], [float(t.holding_days) for t in trades]
        )


class TestDailySortino:
    """The daily equity-curve counterpart, annualized by sqrt(252) rather than the hold."""

    def test_matches_the_definition(self) -> None:
        daily = [0.01, -0.02, 0.03, -0.01, 0.005]
        downside = math.sqrt(sum(min(r, 0.0) ** 2 for r in daily) / len(daily))

        expected = (sum(daily) / len(daily)) / downside * math.sqrt(252)
        assert compute_daily_sortino(daily) == pytest.approx(expected)

    def test_denominator_spans_all_days_not_just_down_days(self) -> None:
        """The bug this helper replaced: dividing by the down-day count inflates by sqrt(N/n_down)."""
        daily = [0.01, 0.01, 0.01, -0.02]
        losers_only = (sum(daily) / len(daily)) / math.sqrt(0.02**2 / 1) * math.sqrt(252)

        assert compute_daily_sortino(daily) == pytest.approx(losers_only * math.sqrt(len(daily) / 1))

    def test_periods_per_year_scales_the_annualization(self) -> None:
        daily = [0.01, -0.02, 0.03]

        assert compute_daily_sortino(daily, periods_per_year=1) == pytest.approx(compute_daily_sortino(daily) / math.sqrt(252))

    @pytest.mark.parametrize("factor", [0.01, 100.0])
    def test_is_scale_invariant(self, factor: float) -> None:
        daily = [0.01, -0.02, 0.03, -0.01]

        assert compute_daily_sortino([r * factor for r in daily]) == pytest.approx(compute_daily_sortino(daily))

    @pytest.mark.parametrize("series", [[], [0.01, 0.02], [0.0, 0.0]])
    def test_nan_without_a_down_day(self, series: list[float]) -> None:
        assert math.isnan(compute_daily_sortino(series))


class TestImportContainment:
    def test_module_imports_neither_pandas_nor_quantstats(self) -> None:
        """Per CLAUDE.md pandas stays in portfolio/analytics.py, and trades never enter quantstats."""
        tree = ast.parse(Path(metrics_module.__file__).read_text())
        roots = {
            (node.module or "").split(".")[0] if isinstance(node, ast.ImportFrom) else alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import | ast.ImportFrom)
            for alias in node.names
        }

        assert "pandas" not in roots
        assert "quantstats" not in roots
