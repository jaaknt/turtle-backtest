"""Tests for the shared cohort-study pipeline and the filter controls it adds to the research layer."""

from datetime import date, timedelta

import numpy as np
import polars as pl
import pytest

from turtlex.research import cohorts
from turtlex.research import qullamaggie as qm

D0 = date(2020, 1, 1)


def _candidate(symbol: str, day: date, **overrides: float) -> dict:
    """One indicator row that passes every production entry filter unless overridden."""
    row = {
        "symbol": symbol,
        "date": day,
        "sma50": 100.0,
        "max_c_50d": 100.0,
        "rsi14": 50.0,
        "roc_252d": 0.5,
        "adr_pct_change": 0.5,
        "raw_close": 8.0,
        "avg_vol_20": 1_000_000.0,
        "adr_pct": 0.09,
        "adj_close": 120.0,
        "pct_vs_sma50": 0.32,
        "volume": 1_000_000.0,
        "avg_vol_50": 1_000_000.0,
    }
    row.update(overrides)
    return row


def _frame(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(rows).with_columns(pl.col("date").cast(pl.Date))


class TestGetSignalsControls:
    def test_drop_removes_only_the_named_filter(self) -> None:
        df = _frame([_candidate("HOT", D0, rsi14=85.0), _candidate("COLD", D0)])
        bull = {D0}
        assert qm.get_signals(df, bull, D0)["symbol"].to_list() == ["COLD"]
        assert sorted(qm.get_signals(df, bull, D0, drop={"rsi"})["symbol"].to_list()) == ["COLD", "HOT"]

    def test_dropping_the_regime_ignores_bull_dates(self) -> None:
        df = _frame([_candidate("A", D0)])
        assert qm.get_signals(df, set(), D0).is_empty()
        assert qm.get_signals(df, set(), D0, drop={"regime"}).height == 1

    def test_unknown_filter_name_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown entry filter"):
            qm.get_signals(_frame([_candidate("A", D0)]), {D0}, D0, drop={"rsi_cap"})

    def test_extra_conditions_apply_before_the_cooldown(self) -> None:
        # Two triggers ten days apart: normally the second falls inside the first's cooldown.
        second = D0 + timedelta(days=10)
        df = _frame([_candidate("A", D0, avg_vol_10=1.0), _candidate("A", second, avg_vol_10=2.0)])
        bull = {D0, second}
        assert qm.get_signals(df, bull, D0)["date"].to_list() == [D0]
        excluded_first = qm.get_signals(df, bull, D0, extra=[pl.col("avg_vol_10") > 1.0])
        assert excluded_first["date"].to_list() == [second]


class TestForwardReturns:
    def test_exit_is_first_bar_on_or_after_the_hold_and_order_is_kept(self) -> None:
        entry = D0
        bars = _frame(
            [
                {"symbol": "A", "date": entry, "adj_close": 10.0},
                # No bar exactly at +366: the exit rolls forward to the next one.
                {"symbol": "A", "date": entry + timedelta(days=368), "adj_close": 15.0},
                {"symbol": "B", "date": entry, "adj_close": 20.0},
                {"symbol": "B", "date": entry + timedelta(days=366), "adj_close": 10.0},
                {"symbol": "B", "date": entry + timedelta(days=367), "adj_close": 99.0},
            ]
        )
        signals = _frame(
            [
                {"symbol": "B", "date": entry, "entry_date": entry, "entry_price": 20.0},
                {"symbol": "A", "date": entry, "entry_date": entry, "entry_price": 10.0},
            ]
        )
        out = cohorts.forward_returns(signals, bars)
        assert out["symbol"].to_list() == ["B", "A"]
        assert out["ret"].to_list() == pytest.approx([-0.5, 0.5])
        assert out.columns == [*signals.columns, "ret"]

    def test_signal_without_a_full_hold_is_dropped(self) -> None:
        bars = _frame(
            [
                {"symbol": "A", "date": D0, "adj_close": 10.0},
                {"symbol": "A", "date": D0 + timedelta(days=365), "adj_close": 12.0},
            ]
        )
        signals = _frame([{"symbol": "A", "date": D0, "entry_date": D0, "entry_price": 10.0}])
        assert cohorts.forward_returns(signals, bars).is_empty()


class TestCohortTrades:
    def test_ranking_gate_window_end_and_returns(self) -> None:
        signal_day = cohorts.EVAL_END
        entry_day = signal_day + timedelta(days=2)
        exit_day = entry_day + timedelta(days=qm.HOLD_CAL)
        candidates = [
            # ADR 9% + 32% above SMA50 + $8 close score 40 + 35 + 25 = 100.
            _candidate("HIGH", signal_day),
            # ADR 3.2% + 13% above SMA50 + $200 close score 4 + 7 + 9 = 20, below the gate.
            _candidate("LOW", signal_day, adr_pct=0.032, pct_vs_sma50=0.13, raw_close=200.0),
            # Clears every filter but falls after the window end.
            _candidate("LATE", signal_day + timedelta(days=1)),
        ]
        # Entry and exit bars carry no indicators, so the not-null guards keep them out of the candidates.
        later = [{"symbol": s, "date": d, "adj_close": 150.0} for s in ("HIGH", "LOW", "LATE") for d in (entry_day, exit_day)]
        df = pl.concat([_frame(candidates), _frame(later)], how="diagonal").sort("symbol", "date")
        bars = df.select("symbol", "date", pl.lit(100.0).alias("adj_open"))
        bull = {row["date"] for row in candidates}

        gated = cohorts.cohort_trades(df, bars, bull, 0.12, start=D0)
        assert gated["symbol"].to_list() == ["HIGH"]
        assert gated["ranking"].to_list() == [100]

        ungated = cohorts.cohort_trades(df, bars, bull, 0.12, start=D0, gated=False)
        assert ungated["symbol"].to_list() == ["HIGH", "LOW"]
        assert ungated["ranking"].to_list() == [100, 20]
        assert ungated["entry_date"].to_list() == [entry_day, entry_day]
        assert ungated["ret"].to_list() == pytest.approx([0.5, 0.5])


class TestTables:
    def test_bucket_groups_are_half_open(self) -> None:
        trades = pl.DataFrame({"x": [0.0, 1.0, 2.0], "ret": [0.1, 0.2, 0.3]})
        groups = cohorts.bucket_groups(trades, "x", [("lo", 0.0, 1.0), ("hi", 1.0, float("inf"))])
        assert [(label, rets.tolist()) for label, rets in groups] == [("lo", [0.1]), ("hi", [0.2, 0.3])]

    def test_render_table_rows(self) -> None:
        rets = np.array([0.1, -0.2, 0.3, -0.1, 0.2, 0.05])
        lines = cohorts.render_table("arm", [("big", rets), ("small", rets[:2])], [("ALL", rets), ("tiny", rets[:1])], label_width=8)
        assert lines[0] == "### arm"
        assert lines[2].startswith("Cohort  ")
        assert lines[4].startswith("big     ")
        assert lines[5] == f"{'small':<8}  {2:>5}  {'—':>7}  {'—':>7}  {'—':>6}  {'—':>8}  {'—':>6}  {'—':>8}"
        assert lines[6] == lines[3]  # closing rule
        assert lines[7].startswith("ALL     ")
        assert lines[-1] == ""
        assert not any(line.startswith("tiny") for line in lines)

    def test_render_table_without_footer_has_no_closing_rule(self) -> None:
        rets = np.array([0.1, -0.2, 0.3, -0.1, 0.2])
        lines = cohorts.render_table("arm", [("row", rets)], [], label_header="Regime")
        assert lines[2].startswith("Regime")
        assert lines[3:] == [lines[3], lines[4], ""]
        assert lines.count(lines[3]) == 1


class TestConfigRows:
    def test_override_omit_and_insert(self) -> None:
        rows = cohorts.config_rows(
            {
                "Cohort variable": "x",
                "Filter under study": "y",
                "⚠ Note": "z",
                "Fixed filters": "f",
                "Market regime": None,
            }
        )
        names = [name for name, _ in rows]
        assert names.index("⚠ Note") == names.index("Filter under study") + 1
        assert "Market regime" not in names
        assert names[0] == "Period"
        assert dict(rows)["Cohort variable"] == "x"

    def test_leading_new_row_goes_first(self) -> None:
        rows = cohorts.config_rows({"Period": None, "Periods": "p", "Cohort variable": "x", "Fixed filters": "f"})
        assert rows[0] == ("Periods", "p")
