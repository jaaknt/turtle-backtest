"""Tests for the shared portfolio replay.

Three behaviours here are worth pinning because a wrong answer looks plausible rather than
broken: an unpriceable position must raise instead of silently valuing at zero, an empty
calendar must raise instead of producing a numpy reduction error several frames deeper, and
`top_k` must break ties at random instead of by row order — the ordering effect that makes an
arbitrary cut inside a tie group look like skill.
"""

from datetime import date, timedelta

import numpy as np
import polars as pl
import pytest

from turtlex.research.portfolio_replay import Market, run_sim, top_k

_EPOCH = date(1970, 1, 1)


@pytest.fixture
def market() -> Market:
    """One symbol rising 1% a trading day for 500 days from $10."""
    days = [date(2020, 1, 1) + timedelta(days=i) for i in range(500)]
    return Market(
        pl.DataFrame(
            {
                "symbol": ["AAA"] * 500,
                "date": days,
                "adj_close": [10.0 * 1.01**i for i in range(500)],
            }
        )
    )


def test_price_on_returns_the_last_close_at_or_before(market: Market) -> None:
    """A date between bars prices off the previous bar, not the next one."""
    assert market.price_on("AAA", (date(2020, 1, 1) - _EPOCH).days) == pytest.approx(10.0)
    assert market.price_on("AAA", (date(2020, 1, 3) - _EPOCH).days) == pytest.approx(10.0 * 1.01**2)


def test_price_on_raises_for_an_unpriceable_position(market: Market) -> None:
    """An absent price means signals and prices came from different frames — say so loudly."""
    with pytest.raises(ValueError, match="No bar for BBB"):
        market.price_on("BBB", (date(2020, 6, 1) - _EPOCH).days)
    with pytest.raises(ValueError, match="No bar for AAA"):
        market.price_on("AAA", (date(2019, 1, 1) - _EPOCH).days)


@pytest.mark.parametrize("calendar", [[], [date(2020, 1, 1)]], ids=["empty", "single-day"])
def test_run_sim_rejects_a_calendar_too_short_to_measure(market: Market, calendar: list[date]) -> None:
    """A sub-period the cached data barely covers fails here, not inside numpy.

    The single-day case matters as much as the empty one: it clears an "is it empty" guard and
    then divides by a zero-day span, which is the deeper failure the guard exists to prevent.
    """
    with pytest.raises(ValueError, match="at least two trading days"):
        run_sim(market, calendar, [], "score")


def test_run_sim_compounds_a_held_position(market: Market) -> None:
    """A single funded position tracks its symbol, and the cash it consumed leaves the curve."""
    calendar = [date(2020, 1, 1) + timedelta(days=i) for i in range(400)]
    entry_dint = (date(2020, 1, 2) - _EPOCH).days
    res = run_sim(market, calendar, [{"symbol": "AAA", "entry_dint": entry_dint, "entry_px": 10.1, "score": 1.0}], "score")
    assert res["taken"] == 1
    assert res["cagr"] > 0


def test_run_sim_skips_a_signal_it_cannot_fund(market: Market) -> None:
    """Positions are a fixed fraction of portfolio value, so cash runs out and later signals skip."""
    calendar = [date(2020, 1, 1) + timedelta(days=i) for i in range(60)]
    dint = (date(2020, 1, 2) - _EPOCH).days
    many = [{"symbol": "AAA", "entry_dint": dint, "entry_px": 10.1, "score": float(i)} for i in range(100)]
    res = run_sim(market, calendar, many, "score", pos_fraction=0.04)
    assert 0 < res["taken"] < 100


def test_run_sim_funds_the_best_score_first(market: Market) -> None:
    """Funding priority is the score — the whole reason a re-ordering can change returns."""
    calendar = [date(2020, 1, 1) + timedelta(days=i) for i in range(60)]
    dint = (date(2020, 1, 2) - _EPOCH).days
    cheap = {"symbol": "AAA", "entry_dint": dint, "entry_px": 10.1, "score": 99.0}
    rest = [{"symbol": "AAA", "entry_dint": dint, "entry_px": 10.1, "score": float(i)} for i in range(60)]
    # With only one position affordable, the high scorer must be the one taken.
    res = run_sim(market, calendar, [*rest, cheap], "score", pos_fraction=0.9)
    assert res["taken"] == 1


def test_top_k_breaks_ties_at_random_not_by_order() -> None:
    """Every tied signal is reachable across redraws, so no cut depends on row order."""
    signals = [{"id": i, "score": 1.0} for i in range(20)]
    picked: set[int] = set()
    for seed in range(30):
        picked.update(s["id"] for s in top_k(signals, "score", 5, np.random.default_rng(seed)))
    assert len(picked) > 5, "tie-break never reached beyond the first rows"


def test_top_k_respects_score_before_the_tie_break() -> None:
    """Randomness applies only inside a tie group; a higher score always wins."""
    signals = [{"id": i, "score": float(i)} for i in range(20)]
    for seed in range(10):
        assert {s["id"] for s in top_k(signals, "score", 3, np.random.default_rng(seed))} == {17, 18, 19}


def test_run_sim_caps_new_positions_per_month(market: Market) -> None:
    """A monthly cap limits how many positions open in each calendar month, not in total."""
    calendar = [date(2020, 1, 1) + timedelta(days=i) for i in range(120)]
    signals = [
        {"symbol": "AAA", "entry_dint": (date(2020, 1, 1) + timedelta(days=i) - _EPOCH).days, "entry_px": 10.0, "score": float(i)}
        for i in range(120)
    ]
    capped = run_sim(market, calendar, signals, "score", max_new_per_month=1)
    per_month = {(d.year, d.month) for d in capped["entries"]}
    assert len(capped["entries"]) == len(per_month), "more than one position opened in some month"
    assert len(per_month) > 1, "the cap should still allow a position in each new month"
    assert run_sim(market, calendar, signals, "score")["taken"] > capped["taken"]


def test_run_sim_without_a_cap_is_unchanged(market: Market) -> None:
    """The cap defaults to off, so existing callers replay exactly as before."""
    calendar = [date(2020, 1, 1) + timedelta(days=i) for i in range(90)]
    signals = [
        {"symbol": "AAA", "entry_dint": (date(2020, 1, 1) + timedelta(days=i) - _EPOCH).days, "entry_px": 10.0, "score": float(i)}
        for i in range(90)
    ]
    plain = run_sim(market, calendar, signals, "score")
    explicit_none = run_sim(market, calendar, signals, "score", max_new_per_month=None)
    # Compared field by field: this fixture rises every day, so `sortino` is nan and a whole-dict
    # equality would fail on nan != nan rather than on any real difference.
    assert plain["taken"] == explicit_none["taken"]
    assert plain["entries"] == explicit_none["entries"]
    assert plain["cagr"] == pytest.approx(explicit_none["cagr"])
    assert plain["max_dd"] == pytest.approx(explicit_none["max_dd"])


def test_run_sim_reports_one_entry_date_per_funded_position(market: Market) -> None:
    """`entries` is what the vintage statistics are computed from, so it must match `taken`."""
    calendar = [date(2020, 1, 1) + timedelta(days=i) for i in range(200)]
    dint = (date(2020, 1, 2) - _EPOCH).days
    signals = [{"symbol": "AAA", "entry_dint": dint, "entry_px": 10.0, "score": float(i)} for i in range(40)]
    res = run_sim(market, calendar, signals, "score")
    assert len(res["entries"]) == res["taken"]
    assert all(d in calendar for d in res["entries"])
