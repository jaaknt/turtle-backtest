"""The fixed-hold portfolio simulator behind scripts/qullamaggie-portfolio-sim.py."""

from datetime import date, timedelta

import numpy as np
import polars as pl
import pytest

from turtlex.research import qullamaggie as qm
from turtlex.research.portfolio_sim import SimMarket, SimParams, gate_signals, month_end_returns, run_sim, to_dint, year_metrics

START = date(2024, 1, 1)
CAL = [START + timedelta(days=i) for i in range(10)]


def _market(closes: dict[str, list[float]], opens: dict[str, list[float]] | None = None) -> SimMarket:
    """A market with one bar per calendar day for each symbol."""
    rows = [
        {"symbol": sym, "date": CAL[i], "adj_close": c, "adj_open": (opens or {}).get(sym, cs)[i]}
        for sym, cs in closes.items()
        for i, c in enumerate(cs)
    ]
    return SimMarket.from_bars(pl.DataFrame(rows), CAL)


def _signal(sym: str, day: int, ranking: int, entry_px: float) -> dict:
    return {"symbol": sym, "date": CAL[day - 1], "ranking": ranking, "entry_dint": to_dint(CAL[day]), "entry_px": entry_px}


class TestSimMarket:
    def test_price_on_carries_the_last_close_forward(self) -> None:
        market = _market({"AAA": [10.0 + i for i in range(10)]})
        assert market.price_on("AAA", to_dint(CAL[3])) == 13.0
        assert market.price_on("AAA", to_dint(CAL[0]) - 1) is None
        assert market.price_on("ZZZ", to_dint(CAL[3])) is None

    def test_next_open_skips_non_positive_opens(self) -> None:
        opens = [10.0, 0.0, -1.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0]
        market = _market({"AAA": [10.0] * 10}, {"AAA": opens})
        assert market.next_open("AAA", to_dint(CAL[0])) == (to_dint(CAL[3]), 12.0)

    def test_next_open_gives_up_after_the_search_window(self) -> None:
        """The only tradeable open is one day past the window, so there is no fill."""
        opens = [0.0] * 10
        opens[qm.ENTRY_SEARCH_DAYS + 1] = 12.0
        market = _market({"AAA": [10.0] * 10}, {"AAA": opens})
        assert market.next_open("AAA", to_dint(CAL[0])) is None
        assert market.next_open("AAA", to_dint(CAL[1])) == (to_dint(CAL[qm.ENTRY_SEARCH_DAYS + 1]), 12.0)


class TestGateSignals:
    def test_counts_gate_drops_and_unfilled_separately(self) -> None:
        resolved: list[dict] = [
            {"ranking": 30, "entry_dint": 1},
            {"ranking": 60, "entry_dint": None},
            {"ranking": 60, "entry_dint": 5},
            {"ranking": 50, "entry_dint": 5},
        ]
        by_day, n_rank, n_unfilled = gate_signals(resolved, 44)
        assert (n_rank, n_unfilled) == (1, 1)
        assert by_day == {5: [resolved[2], resolved[3]]}


class TestRunSim:
    def test_a_position_is_closed_at_the_time_cap(self) -> None:
        market = _market({"AAA": [10.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0]})
        res = run_sim(market, {to_dint(CAL[1]): [_signal("AAA", 1, 60, 10.0)]}, SimParams(0.5, 1000.0, hold_cal=3))

        # 500 at 10.0 buys 50 shares, closed on day 4 at 13.0: +150.
        assert res["taken"] == 1
        assert res["trades"] == [{"entry_date": CAL[1], "sig_date": CAL[0], "symbol": "AAA", "ret": pytest.approx(0.3), "ranking": 60}]
        assert res["final"] == pytest.approx(1150.0)

    def test_an_open_position_is_marked_to_market_at_period_end(self) -> None:
        market = _market({"AAA": [10.0] * 9 + [20.0]})
        res = run_sim(market, {to_dint(CAL[1]): [_signal("AAA", 1, 60, 10.0)]}, SimParams(0.5, 1000.0))

        assert res["final"] == pytest.approx(1500.0)
        assert res["trades"][0]["ret"] == pytest.approx(1.0)

    def test_same_day_signals_are_funded_best_ranked_first(self) -> None:
        """Cash covers one position; the higher-ranked signal gets it, and the other is skipped."""
        market = _market({"LOW": [10.0] * 10, "HIGH": [10.0] * 10})
        sigs = {to_dint(CAL[1]): [_signal("LOW", 1, 45, 10.0), _signal("HIGH", 1, 90, 10.0)]}

        ranked = run_sim(market, sigs, SimParams(0.6, 1000.0))
        arrival = run_sim(market, sigs, SimParams(0.6, 1000.0, rank_funding=False))

        assert [t["symbol"] for t in ranked["trades"]] == ["HIGH"]
        assert [t["symbol"] for t in arrival["trades"]] == ["LOW"]
        assert (ranked["taken"], ranked["skipped"]) == (1, 1)
        assert ranked["skips"] == [CAL[1]]

    def test_without_signals_equity_stays_flat(self) -> None:
        res = run_sim(_market({"AAA": [10.0] * 10}), {}, SimParams(0.03, 1000.0))
        assert res["final"] == 1000.0
        assert res["max_dd"] == 0.0
        assert res["avg_uninv_pct"] == 100.0


def test_month_end_returns_base_the_first_month_on_the_starting_equity() -> None:
    dates = [date(2024, 1, 30), date(2024, 1, 31), date(2024, 2, 29)]
    eom = month_end_returns(dates, np.array([1000.0, 1100.0, 1210.0]), 1000.0)
    assert eom["ret"].to_list() == pytest.approx([0.1, 0.1])


def test_year_metrics_split_returns_and_counts_by_calendar_year() -> None:
    dates = [date(2023, 12, 28), date(2023, 12, 29), date(2024, 1, 2), date(2024, 1, 3)]
    r = {
        "dates": dates,
        "eq": np.array([100.0, 110.0, 121.0, 99.0]),
        "cash": np.array([100.0, 50.0, 50.0, 50.0]),
        "entries": [date(2023, 12, 29), date(2024, 1, 2), date(2024, 1, 3)],
        "skips": [date(2024, 1, 2)],
    }
    rows = year_metrics(r)

    assert [y["year"] for y in rows] == [2023, 2024]
    assert rows[0]["ret"] == pytest.approx(0.1)  # against the opening equity
    assert rows[1]["ret"] == pytest.approx(99.0 / 110.0 - 1.0)  # against 2023's close
    assert rows[1]["max_dd"] == pytest.approx(99.0 / 121.0 - 1.0)
    assert [(y["taken"], y["skipped"]) for y in rows] == [(1, 0), (2, 1)]
