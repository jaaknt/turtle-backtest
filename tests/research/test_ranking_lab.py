"""Unit and parity tests for the ranking-hypothesis lab.

The anchor is `test_c000_reproduces_production_scores`: the seed baseline spec must score every
signal exactly as the shipped `QullamaggieRanking` does. Every verdict the loop records is a
comparison against that baseline, so if the spec drifts from production the whole ledger
silently becomes a comparison against something that was never shipped.

The rest guard the pieces that would fail quietly rather than loudly — a transform that is not
monotone, an isotonic fit that is not non-decreasing, a Spearman that mishandles ties, and the
spec loader accepting a typo'd feature name that would score a dimension 0 everywhere.
"""

import json
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from turtlex.research import ranking_lab as rl
from turtlex.strategy.ranking.qullamaggie import QullamaggieRanking

CANDIDATE_DIR = Path(__file__).resolve().parents[2] / "docs" / "research" / "ranking-lab" / "candidates"


@pytest.fixture
def production_spec() -> rl.CandidateSpec:
    return rl.load_spec(CANDIDATE_DIR / "c000-production.json")


def _signal_frame(rows: list[tuple[float, float, float]], start: date = date(2020, 1, 1)) -> pl.DataFrame:
    """Frame of (adr_pct, pct_vs_sma50, raw_close) triples on consecutive dates."""
    return pl.DataFrame(
        {
            "date": [start + timedelta(days=i) for i in range(len(rows))],
            "adr_pct": [r[0] for r in rows],
            "pct_vs_sma50": [r[1] for r in rows],
            "raw_close": [r[2] for r in rows],
        }
    )


# ── Parity with production ───────────────────────────────────────────────────────────────


def test_c000_reproduces_production_scores(production_spec: rl.CandidateSpec) -> None:
    """The seed baseline scores identically to the shipped ranking, band edges included."""
    ranker = QullamaggieRanking()
    rng = np.random.default_rng(7)
    rows = [
        (float(a), float(s), float(p))
        for a, s, p in zip(rng.uniform(0.02, 0.12, 400), rng.uniform(0.08, 0.45, 400), rng.uniform(4.0, 260.0, 400), strict=True)
    ]
    # Every band edge exactly, where a `<` and a `<=` disagree.
    rows += [(a, 0.20, 50.0) for a in (0.03, 0.035, 0.04, 0.045, 0.05, 0.07, 0.08)]
    rows += [(0.05, s, 50.0) for s in (0.10, 0.12, 0.15, 0.17, 0.20, 0.30)]
    rows += [(0.05, 0.20, p) for p in (10.0, 20.0, 50.0, 100.0, 250.0)]

    sig = _signal_frame(rows)
    got = rl.raw_scores(sig, production_spec)
    for i, row in enumerate(sig.iter_rows(named=True)):
        one = pl.DataFrame(
            [{"date": row["date"], "close": row["raw_close"], "adr_pct": row["adr_pct"], "pct_vs_sma50": row["pct_vs_sma50"]}]
        )
        assert got[i] == pytest.approx(ranker.ranking(one, row["date"])), f"row {i} {row} scored {got[i]}"


def test_missing_value_scores_the_term_zero(production_spec: rl.CandidateSpec) -> None:
    """A null feature costs its whole term, exactly as production's fallback does."""
    sig = _signal_frame([(0.09, 0.35, 8.0)]).with_columns(pl.lit(None, dtype=pl.Float64).alias("adr_pct"))
    assert rl.raw_scores(sig, production_spec)[0] == pytest.approx(35 + 25)


# ── Spec loading ─────────────────────────────────────────────────────────────────────────


def test_every_committed_candidate_loads() -> None:
    """No committed spec has a typo'd transform, an unsorted band table or a bad grid."""
    paths = sorted(CANDIDATE_DIR.glob("*.json"))
    assert paths, "no candidate specs found"
    for p in paths:
        spec = rl.load_spec(p)
        assert spec.id == p.stem, f"{p.name}: id {spec.id!r} does not match its filename"


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"aggregate": "average"}, "unknown aggregate"),
        ({"terms": [{"feature": "adr_pct", "transform": "polynomial"}]}, "unknown transform"),
        ({"terms": [{"feature": "adr_pct", "transform": "bands", "bands": [[0.05, 1], [0.03, 2]], "top": 5}]}, "not ascending"),
        ({"terms": [{"feature": "adr_pct", "transform": "bands", "bands": [[0.03, 0], [0.05, 15]]}]}, "without an explicit 'top'"),
        ({"terms": [{"feature": "adr_pct", "transform": "bands", "bands": [[0.03, 0]], "top": 5, "tpo": 40}]}, "unknown keys"),
        ({"terms": [{"feature": "adr_pct", "transform": "bands", "bands": [[0.03, 0]], "top": 5, "direction": "lower"}]}, "ignores it"),
        ({"parent": "x", "spec_typo": 1}, "unknown spec keys"),
        (
            {
                "terms": [
                    {
                        "features": ["adr_pct", "raw_close"],
                        "transform": "grid2d",
                        "x_bounds": [3.0, 1.0],
                        "y_bounds": [2.0],
                        "points": [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]],
                    }
                ]
            },
            "x_bounds are not ascending",
        ),
        (
            {
                "terms": [
                    {
                        "features": ["adr_pct", "raw_close"],
                        "transform": "grid2d",
                        "x_bounds": [1.0],
                        "y_bounds": [2.0],
                        "points": [[1.0, 2.0], [3.0]],
                    }
                ]
            },
            "differing lengths",
        ),
        ({"terms": [{"feature": "adr_pct", "transform": "linear_clip", "lo": 1.0, "hi": 0.5, "weight": 10}]}, "needs hi > lo"),
        ({"terms": [{"feature": "adr_pct", "transform": "percentile_trailing", "weight": 0}]}, "needs a positive weight"),
        (
            {
                "terms": [
                    {
                        "features": ["adr_pct", "raw_close"],
                        "transform": "grid2d",
                        "x_bounds": [1.0],
                        "y_bounds": [2.0],
                        "points": [[1.0, 2.0]],
                    }
                ]
            },
            "but its bounds imply",
        ),
    ],
)
def test_load_spec_rejects_malformed_specs(tmp_path: Path, mutation: dict, message: str) -> None:
    """A malformed spec fails at load, not by silently scoring a dimension 0 everywhere."""
    raw = {
        "id": "c999-bad",
        "hypothesis": "x",
        "aggregate": "sum",
        "terms": [{"feature": "adr_pct", "transform": "bands", "bands": [[0.03, 0]]}],
    }
    raw.update(mutation)
    path = tmp_path / "c999-bad.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        rl.load_spec(path)


def test_unknown_feature_name_raises(production_spec: rl.CandidateSpec) -> None:
    """Scoring a frame that lacks a spec's column fails loudly rather than scoring 0."""
    sig = _signal_frame([(0.09, 0.35, 8.0)]).drop("raw_close")
    with pytest.raises(ValueError, match="no column 'raw_close'"):
        rl.raw_scores(sig, production_spec)


# ── Transforms ───────────────────────────────────────────────────────────────────────────


def test_linear_clip_is_monotone_and_bounded() -> None:
    """A higher feature value never scores fewer points, and the ramp saturates at its weight."""
    term = rl.Term(transform="linear_clip", features=("adr_pct",), weight=40.0, lo=0.03, hi=0.10)
    sig = _signal_frame([(v, 0.2, 20.0) for v in (0.01, 0.03, 0.05, 0.07, 0.10, 0.30)])
    pts = rl.apply_term(sig, term)
    assert list(pts) == sorted(pts)
    assert pts[0] == pytest.approx(0.0)
    assert pts[-1] == pytest.approx(40.0)


def test_linear_clip_direction_lower_inverts() -> None:
    """`direction: lower` scores cheap entries higher, the shape price needs."""
    term = rl.Term(transform="linear_clip", features=("raw_close",), weight=25.0, lo=5.0, hi=250.0, direction="lower")
    sig = _signal_frame([(0.05, 0.2, p) for p in (5.0, 50.0, 250.0)])
    pts = rl.apply_term(sig, term)
    assert pts[0] > pts[1] > pts[2]


def test_percentile_trailing_is_causal() -> None:
    """A signal is ranked only against earlier ones, so appending later rows cannot change it.

    This is the property that makes the transform fold-safe: if a later signal could move an
    earlier one's score, computing scores once for every fold would leak the test side.
    """
    term = rl.Term(transform="percentile_trailing", features=("adr_pct",), weight=35.0, window_days=3650)
    rows = [(0.03 + 0.001 * i, 0.2, 20.0) for i in range(60)]
    early = rl.apply_term(_signal_frame(rows[:40]), term)
    late = rl.apply_term(_signal_frame(rows), term)
    assert np.allclose(early, late[:40])


def test_percentile_trailing_scores_neutral_without_enough_history() -> None:
    """The first rows have no window to rank against and score the midpoint, not an extreme."""
    term = rl.Term(transform="percentile_trailing", features=("adr_pct",), weight=100.0, window_days=3650)
    pts = rl.apply_term(_signal_frame([(0.03 + 0.001 * i, 0.2, 20.0) for i in range(rl.MIN_TRAILING_N + 5)]), term)
    assert np.allclose(pts[: rl.MIN_TRAILING_N], 50.0)
    assert pts[-1] > 50.0


def test_grid2d_indexes_both_bounds() -> None:
    """A 2-D table picks the cell both features fall in, including the open top-right corner."""
    term = rl.Term(
        transform="grid2d",
        features=("adr_pct", "pct_vs_sma50"),
        x_bounds=(0.05,),
        y_bounds=(0.20,),
        points=((1.0, 2.0), (3.0, 4.0)),
    )
    sig = _signal_frame([(0.04, 0.1, 20.0), (0.04, 0.3, 20.0), (0.06, 0.1, 20.0), (0.06, 0.3, 20.0)])
    assert list(rl.apply_term(sig, term)) == [1.0, 2.0, 3.0, 4.0]


def test_min_aggregation_is_non_compensatory(production_spec: rl.CandidateSpec) -> None:
    """Under `min`, a top score on two dimensions cannot rescue a weak third."""
    spec = rl.CandidateSpec(id="t", hypothesis="", parent="", aggregate="min", terms=production_spec.terms)
    strong_but_cheap_only = _signal_frame([(0.031, 0.11, 8.0)])  # worst ADR band, worst SMA50 band, best price
    balanced = _signal_frame([(0.06, 0.22, 45.0)])
    assert rl.raw_scores(strong_but_cheap_only, spec)[0] < rl.raw_scores(balanced, spec)[0]


# ── Isotonic calibration ─────────────────────────────────────────────────────────────────


def test_isotonic_fit_is_non_decreasing() -> None:
    """PAVA output never decreases, whatever the input does."""
    rng = np.random.default_rng(3)
    x = np.sort(rng.uniform(0, 100, 500))
    y = np.sin(x / 10.0) + rng.normal(0, 0.5, 500)  # deliberately non-monotone
    _, values = rl.isotonic_fit(x, y)
    assert np.all(np.diff(values) >= -1e-12)


def test_isotonic_fit_leaves_monotone_data_alone() -> None:
    """An already-increasing series is its own isotonic fit."""
    x = np.arange(10, dtype=float)
    y = np.arange(10, dtype=float) * 2.0
    knots, values = rl.isotonic_fit(x, y)
    assert np.allclose(knots, x)
    assert np.allclose(values, y)


def test_isotonic_apply_rescales_to_0_100() -> None:
    """Calibrated scores span the full 0-100 range the ranking contract expects."""
    x = np.arange(20, dtype=float)
    knots, values = rl.isotonic_fit(x, x * 3.0)
    out = rl.isotonic_apply(knots, values, x)
    assert out.min() == pytest.approx(0.0)
    assert out.max() == pytest.approx(100.0)
    assert np.all(np.diff(out) >= -1e-12)


def test_isotonic_apply_handles_a_degenerate_fit() -> None:
    """A constant outcome has no ordering to calibrate and scores everything 0, not nan."""
    x = np.arange(10, dtype=float)
    knots, values = rl.isotonic_fit(x, np.ones(10))
    assert np.all(rl.isotonic_apply(knots, values, x) == 0.0)


# ── Spearman and monotonicity ────────────────────────────────────────────────────────────


def test_spearman_is_one_for_a_monotone_relation() -> None:
    """Rank correlation ignores the shape of a monotone transform."""
    x = np.arange(1, 21, dtype=float)
    assert rl.spearman(x, np.exp(x / 5.0)) == pytest.approx(1.0)
    assert rl.spearman(x, -x) == pytest.approx(-1.0)


def test_spearman_averages_tied_ranks() -> None:
    """Ties share their average rank, so a coarse score is not silently ordered by row order."""
    assert rl.spearman(np.array([1.0, 1.0, 2.0, 2.0]), np.array([1.0, 1.0, 2.0, 2.0])) == pytest.approx(1.0)
    assert np.isnan(rl.spearman(np.ones(5), np.arange(5, dtype=float)))


def test_monotone_steps_skips_nan_pairs() -> None:
    """A thin decile with no reportable Sortino is not counted as a violation."""
    assert rl.monotone_steps([1.0, 2.0, 3.0]) == (2, 2)
    assert rl.monotone_steps([1.0, float("nan"), 3.0]) == (0, 0)
    assert rl.monotone_steps([3.0, 2.0, 1.0]) == (0, 2)


# ── Protocol ─────────────────────────────────────────────────────────────────────────────


def test_no_fold_reaches_the_holdout() -> None:
    """Every fold's test window stops at the frozen holdout boundary."""
    windows = rl.fold_windows()
    assert windows
    for _, test_start, test_end in windows:
        assert test_end <= rl.HOLDOUT_START
        assert test_start < test_end


def test_required_margin_rises_with_the_search() -> None:
    """A candidate found after many attempts has to clear a wider margin than an early one."""
    assert rl.required_margin(10) == pytest.approx(0.01)
    assert rl.required_margin(80) > rl.required_margin(10)
    assert rl.required_margin(0) == pytest.approx(0.01)


def _card(mono: float, rho: float, spread: float) -> rl.Scorecard:
    folds = [
        rl.FoldResult(
            config=config,
            cutoff=cutoff,
            n_train=500,
            n_test=200,
            mono_sortino=mono,
            mono_mean=6 / 9,
            spearman=rho,
            spread=spread,
            top_decile_sortino=4.0,
        )
        for config, _ in rl.CONFIGS
        for cutoff, _, _ in rl.fold_windows()
    ]
    return rl.Scorecard(spec_id="t", folds=folds)


def test_judge_accepts_a_clear_improvement() -> None:
    """Better monotonicity plus rho beyond the margin, with no config giving up spread, passes."""
    verdict = rl.judge(_card(8 / 9, 0.15, 3.0), _card(5 / 9, 0.10, 3.0), n_tested=10)
    assert verdict.accepted, verdict.reasons


def test_judge_rejects_a_rho_gain_inside_the_margin() -> None:
    """A rho improvement smaller than the multiple-testing margin is not an improvement."""
    verdict = rl.judge(_card(8 / 9, 0.105, 3.0), _card(5 / 9, 0.10, 3.0), n_tested=10)
    assert not verdict.accepted
    assert any("spearman" in r for r in verdict.reasons)


def test_judge_rejects_a_collapsed_spread() -> None:
    """A scheme can be monotone and useless; giving up more than MAX_SPREAD_GIVEBACK fails.

    The give-back is absolute, not the proportional "90% of baseline" rule this gate started
    with — see `test_judge_allows_a_small_loss_against_a_negative_baseline_spread` for why that
    one had to go.
    """
    verdict = rl.judge(_card(8 / 9, 0.15, 2.0), _card(5 / 9, 0.10, 3.0), n_tested=10)
    assert not verdict.accepted
    assert any("spread" in r for r in verdict.reasons)


def test_judge_rejects_worse_monotonicity() -> None:
    """The gate the loop exists for: monotonicity may not regress, however good rho looks."""
    verdict = rl.judge(_card(4 / 9, 0.30, 3.0), _card(5 / 9, 0.10, 3.0), n_tested=10)
    assert not verdict.accepted
    assert any("mono_sortino" in r for r in verdict.reasons)


def test_evaluate_fits_isotonic_on_train_only() -> None:
    """The isotonic map is fitted per fold; a test-side outcome cannot shape its own score.

    Flipping the sign of every test-side return must leave the fitted calibration — and so the
    scores — unchanged. If the fit ever saw the test slice, the two runs would diverge.
    """
    rng = np.random.default_rng(11)
    n = 2400
    dates = [date(2014, 1, 1) + timedelta(days=int(i * 1.5)) for i in range(n)]
    frame = pl.DataFrame(
        {
            "date": dates,
            "symbol": [f"T{i % 40}" for i in range(n)],
            "entry_date": [d + timedelta(days=1) for d in dates],
            "adr_pct": rng.uniform(0.03, 0.12, n),
            "pct_vs_sma50": rng.uniform(0.12, 0.5, n),
            "raw_close": rng.uniform(6.0, 240.0, n),
            "ret": rng.normal(0.2, 0.8, n),
        }
    )
    frame = frame.with_columns((pl.col("ret") - pl.col("ret").mean().over(pl.col("entry_date").dt.year())).alias("ret_demeaned"))
    spec = rl.CandidateSpec(
        id="iso",
        hypothesis="",
        parent="",
        aggregate="sum_then_isotonic",
        terms=rl.load_spec(CANDIDATE_DIR / "c000-production.json").terms,
    )

    cutoff = rl.FOLD_CUTOFFS[0]
    flipped = frame.with_columns(
        pl.when(pl.col("entry_date") >= cutoff).then(-pl.col("ret_demeaned")).otherwise(pl.col("ret_demeaned")).alias("ret_demeaned")
    )
    base = [f for f in rl.evaluate(spec, {"s12": frame}).folds if f.cutoff == cutoff]
    other = [f for f in rl.evaluate(spec, {"s12": flipped}).folds if f.cutoff == cutoff]
    assert base and other
    # Decile *score* means depend only on the calibrated scores, never on the returns that
    # sorted into each bucket -- so they are equal if and only if the fit ignored the test side.
    assert [d["score"] for d in base[0].deciles] == pytest.approx([d["score"] for d in other[0].deciles])


def test_compute_deciles_breaks_ties_at_random_when_given_an_rng() -> None:
    """A tie group cut by row order would favour continuous scores; random cuts remove that.

    Every signal here shares one score, so the split into deciles is entirely a tie-break. With
    no rng the cut is row order and D1 is always the first rows; with one it moves between draws.
    """
    scores = np.zeros(200)
    returns = np.arange(200, dtype=float) / 100.0  # return rises with row order
    fixed = rl.compute_deciles(scores, returns)
    assert fixed[0]["mean"] < fixed[-1]["mean"], "row-order cut puts the earliest rows in D1"

    rng = np.random.default_rng(0)
    d1_means = {round(rl.compute_deciles(scores, returns, rng)[0]["mean"], 6) for _ in range(10)}
    assert len(d1_means) > 1, "random tie-break produced an identical D1 every draw"


def test_evaluate_averages_over_tie_draws() -> None:
    """A fold's monotonicity is a fraction averaged over redraws, not a single arbitrary cut."""
    rng = np.random.default_rng(5)
    n = 2400
    dates = [date(2014, 1, 1) + timedelta(days=int(i * 1.5)) for i in range(n)]
    frame = pl.DataFrame(
        {
            "date": dates,
            "symbol": [f"T{i % 40}" for i in range(n)],
            "entry_date": [d + timedelta(days=1) for d in dates],
            "adr_pct": rng.uniform(0.03, 0.12, n),
            "pct_vs_sma50": rng.uniform(0.12, 0.5, n),
            "raw_close": rng.uniform(6.0, 240.0, n),
            "ret": rng.normal(0.2, 0.8, n),
        }
    )
    frame = frame.with_columns((pl.col("ret") - pl.col("ret").mean().over(pl.col("entry_date").dt.year())).alias("ret_demeaned"))
    card = rl.evaluate(rl.load_spec(CANDIDATE_DIR / "c000-production.json"), {"s12": frame})
    assert card.folds
    for f in card.folds:
        assert 0.0 <= f.mono_sortino <= 1.0


def test_decile_seed_does_not_depend_on_process_hashing() -> None:
    """Tie-break seeds must be stable across processes, or no scorecard is reproducible.

    Python randomizes `hash()` on strings per process, so a seed derived from it gives the same
    candidate different deciles on every run — and since the baseline is re-scored on every
    `--eval`, both sides of every comparison would drift. Pinning the first draw to a constant
    catches any switch back to a process-dependent source.
    """
    first = rl._decile_rng("s12", date(2021, 1, 1)).random()
    assert first == pytest.approx(0.4058085201930347), "decile tie-break seed changed"
    assert rl._decile_rng("s12", date(2021, 1, 1)).random() == pytest.approx(first)
    assert rl._decile_rng("s16", date(2021, 1, 1)).random() != pytest.approx(first)
    assert rl._decile_rng("s12", date(2022, 1, 1)).random() != pytest.approx(first)


def test_evaluate_repeats_itself() -> None:
    """The same spec on the same frame produces the same scorecard, call after call."""
    rng = np.random.default_rng(21)
    n = 2400
    dates = [date(2014, 1, 1) + timedelta(days=int(i * 1.5)) for i in range(n)]
    frame = pl.DataFrame(
        {
            "date": dates,
            "symbol": [f"T{i % 40}" for i in range(n)],
            "entry_date": [d + timedelta(days=1) for d in dates],
            "adr_pct": rng.uniform(0.03, 0.12, n),
            "pct_vs_sma50": rng.uniform(0.12, 0.5, n),
            "raw_close": rng.uniform(6.0, 240.0, n),
            "ret": rng.normal(0.2, 0.8, n),
        }
    )
    frame = frame.with_columns((pl.col("ret") - pl.col("ret").mean().over(pl.col("entry_date").dt.year())).alias("ret_demeaned"))
    spec = rl.load_spec(CANDIDATE_DIR / "c000-production.json")
    a, b = rl.evaluate(spec, {"s12": frame}), rl.evaluate(spec, {"s12": frame})
    assert [f.mono_sortino for f in a.folds] == pytest.approx([f.mono_sortino for f in b.folds])
    assert a.spread == pytest.approx(b.spread)


# ── Regression tests for the review findings ─────────────────────────────────────────────


def test_isotonic_apply_holds_pooled_blocks_flat() -> None:
    """Values PAVA pooled must receive the SAME calibrated score.

    This is the property that makes `sum_then_isotonic` a real hypothesis. Interpolating between
    knots instead of stepping re-separates pooled values in their original order, which makes the
    calibration a rank-preserving no-op — and since every judged metric is rank-based, the
    candidate then scores its own baseline and the hypothesis is never tested.
    """
    raw = np.array([10.0, 20.0, 30.0, 40.0], dtype=float)
    # 20 and 30 violate monotonicity, so PAVA pools them into one block.
    knots, values = rl.isotonic_fit(raw, np.array([0.0, 5.0, 1.0, 9.0]))
    out = rl.isotonic_apply(knots, values, raw)
    assert out[1] == pytest.approx(out[2]), "pooled block was re-separated — apply is interpolating"
    assert out[0] < out[1] < out[3]


def test_isotonic_calibration_changes_ranks() -> None:
    """A correct calibration introduces ties, so it is not a rank-preserving identity.

    This is the difference between "isotonic cannot help" and "isotonic was never applied". A
    weakly-monotone step function pools locally non-monotone levels into one score, which does
    change decile composition; a linear interpolation preserves every rank and cannot.
    """
    raw = np.repeat(np.array([10.0, 20.0, 30.0, 40.0, 50.0]), 40)
    # 20 and 30 are locally inverted, so PAVA pools exactly that pair and leaves the rest.
    y = np.repeat(np.array([0.0, 5.0, 1.0, 6.0, 10.0]), 40)
    knots, values = rl.isotonic_fit(raw, y)
    calibrated = rl.isotonic_apply(knots, values, raw)
    assert 0.0 < rl.spearman(raw, calibrated) < 1.0, "expected a partial pooling, not identity and not collapse"


def test_percentile_trailing_ignores_same_day_peers() -> None:
    """Same-day rows must not rank against each other.

    Callers sort by (date, symbol), so ranking within a day would make the score depend on the
    ticker's alphabetical position — an arbitrary ordering effect in the very module that builds
    random tie-breaking to remove arbitrary ordering effects.
    """
    term = rl.Term(transform="percentile_trailing", features=("adr_pct",), weight=100.0, window_days=3650)
    warmup = [(date(2020, 1, 1) + timedelta(days=i), 0.02 + 0.0001 * i) for i in range(rl.MIN_TRAILING_N + 5)]
    same_day = [(date(2021, 6, 1), 0.03 + 0.001 * i) for i in range(8)]

    def build(rows: list[tuple[date, float]]) -> pl.DataFrame:
        return pl.DataFrame({"date": [r[0] for r in rows], "adr_pct": [r[1] for r in rows]})

    forward = rl.apply_term(build(warmup + same_day), term)[-8:]
    reverse = rl.apply_term(build(warmup + same_day[::-1]), term)[-8:]
    assert np.allclose(forward, reverse[::-1]), "score depends on within-day row order"
    assert len(set(np.round(forward, 6))) == 1, "same-day signals should share one percentile"


def test_judge_rejects_an_unmeasurable_spread() -> None:
    """A gate that could not be evaluated must fail, never silently pass.

    `nan < x` is False, so a bare comparison waives the gate. The s20 2024 fold already produces
    a nan spread on the real cache, so this is live rather than hypothetical.
    """
    verdict = rl.judge(_card(8 / 9, 0.20, float("nan")), _card(5 / 9, 0.10, 3.0), n_tested=10)
    assert not verdict.accepted
    assert any("unmeasurable" in r for r in verdict.reasons)


def test_judge_allows_a_small_loss_against_a_negative_baseline_spread() -> None:
    """The spread tolerance must not invert when the baseline spread is negative.

    A proportional `0.9 * baseline` rule demands the candidate BEAT a negative baseline, so a
    candidate that is strictly better gets rejected. Individual folds do go negative.
    """
    better = rl.judge(_card(8 / 9, 0.20, -1.9), _card(5 / 9, 0.10, -2.0), n_tested=10)
    assert better.accepted, better.reasons
    worse = rl.judge(_card(8 / 9, 0.20, -3.0), _card(5 / 9, 0.10, -2.0), n_tested=10)
    assert not worse.accepted


def test_judge_refuses_to_compare_different_fold_counts() -> None:
    """Aggregates averaged over different fold sets are unpaired and must not be compared."""
    candidate = _card(8 / 9, 0.20, 3.0)
    thin = rl.Scorecard(spec_id="b", folds=[f for f in _card(5 / 9, 0.10, 3.0).folds if f.config != "s20"][:-1])
    verdict = rl.judge(candidate, thin, n_tested=10)
    assert not verdict.accepted
    assert any("not comparable" in r for r in verdict.reasons)


def test_judge_refuses_to_compare_rho_over_different_fold_counts() -> None:
    """The primary gate is rho, and a tied fold silently leaves the candidate's rho mean.

    `spearman` is nan for a fold whose scores are all tied, and `Scorecard._mean` drops nan
    folds per attribute — so without a parity check the candidate is compared on five folds
    against a baseline measured on six, and can clear the margin by having skipped the hard one.
    The value gate cannot catch this: the surviving folds still average 0.20.
    """
    full = _card(8 / 9, 0.20, 3.0)
    tied = rl.Scorecard(spec_id="c", folds=[replace(f, spearman=float("nan")) if i == 0 else f for i, f in enumerate(full.folds)])
    assert tied.spearman == pytest.approx(0.20), "the dropped fold must be invisible to the mean itself"

    verdict = rl.judge(tied, _card(5 / 9, 0.10, 3.0), n_tested=10)
    assert not verdict.accepted
    assert any("spearman" in r and "not comparable" in r for r in verdict.reasons), verdict.reasons


def test_verdict_accepted_tracks_its_reasons() -> None:
    """`accepted` is derived, so it cannot fall out of step with the reasons list."""
    assert rl.Verdict().accepted
    assert not rl.Verdict(("nope",)).accepted


def test_evaluate_skips_a_degenerate_isotonic_fold() -> None:
    """A collapsed calibration makes deciles a random partition, so the fold must be dropped.

    Constant scores still fill ten buckets under random tie-breaking, and the monotonicity of a
    random partition is a coin flip that would be averaged in as though it had been measured.
    """
    rng = np.random.default_rng(9)
    n = 1600
    dates = [date(2014, 1, 1) + timedelta(days=int(i * 2)) for i in range(n)]
    frame = pl.DataFrame(
        {
            "date": dates,
            "symbol": [f"T{i % 40}" for i in range(n)],
            "entry_date": [d + timedelta(days=1) for d in dates],
            "adr_pct": rng.uniform(0.03, 0.12, n),
            "pct_vs_sma50": rng.uniform(0.12, 0.5, n),
            "raw_close": rng.uniform(6.0, 240.0, n),
        }
    )
    spec = rl.CandidateSpec(
        id="iso", hypothesis="", parent="", aggregate="sum_then_isotonic", terms=rl.load_spec(CANDIDATE_DIR / "c000-production.json").terms
    )
    # Make the outcome the exact negative of the score, so PAVA has no choice but to pool every
    # level into one block — the collapse the guard exists to catch.
    frame = frame.with_columns(pl.Series("ret", -rl.raw_scores(frame.sort(["date", "symbol"]), spec) / 100.0))
    frame = frame.with_columns((pl.col("ret") - pl.col("ret").mean().over(pl.col("entry_date").dt.year())).alias("ret_demeaned"))
    card = rl.evaluate(spec, {"s12": frame})
    assert card.skipped, "no fold was skipped at all"
    assert any("degenerate" in why for _, _, why in card.skipped)


# ── add_lab_features ─────────────────────────────────────────────────────────────────────


@pytest.fixture
def lab_frame() -> tuple[pl.DataFrame, pl.DataFrame]:
    """Two symbols over 300 bars with a known shape, plus a flat SPY to subtract."""
    n = 300
    days = [date(2020, 1, 1) + timedelta(days=i) for i in range(n)]
    rows = []
    for sym, base in (("AAA", 10.0), ("BBB", 50.0)):
        for i, d in enumerate(days):
            close = base * (1.0 + 0.002 * i)
            rows.append(
                {
                    "symbol": sym,
                    "date": d,
                    "adj_close": close,
                    "adj_open": close * 0.99,
                    "adj_high": close * 1.02,
                    "adj_low": close * 0.98,
                    "volume": 1_000_000,
                    "sma50": close * 0.9,
                    "avg_vol_10": 800_000.0,
                    "avg_vol_50": 1_000_000.0,
                    "adr_pct": 0.04 if sym == "AAA" else 0.06,
                }
            )
    spy = pl.DataFrame({"date": days, "adj_close": [100.0] * n})
    return pl.DataFrame(rows), spy


def test_add_lab_features_produces_every_documented_column(lab_frame: tuple[pl.DataFrame, pl.DataFrame]) -> None:
    """Each name a candidate spec may reference actually exists after the transform."""
    out = rl.add_lab_features(*lab_frame)
    missing = [f for f in rl.LAB_FEATURES if f not in out.columns]
    assert not missing, f"add_lab_features does not produce {missing}"
    assert not [c for c in out.columns if c.startswith("_")], "temporary columns leaked into the frame"


def test_add_lab_features_values_are_computable_by_hand(lab_frame: tuple[pl.DataFrame, pl.DataFrame]) -> None:
    """Pin the ratios that a swapped numerator would leave looking perfectly valid."""
    out = rl.add_lab_features(*lab_frame).filter(pl.col("symbol") == "AAA").sort("date")
    last = out.row(-1, named=True)
    assert last["vol_dryup"] == pytest.approx(0.8)  # avg_vol_10 / avg_vol_50
    assert last["breakout_vol_ratio"] == pytest.approx(1.0)  # volume / avg_vol_50
    assert last["close_in_range"] == pytest.approx((1.0 - 0.98) / (1.02 - 0.98))
    assert last["gap_pct"] < 0, "open is below the prior close in this fixture"
    assert last["sma_stack"] == 4, "a monotonically rising series should stack every SMA"
    assert last["pct_vs_sma200"] > 0


def test_add_lab_features_relative_strength_cancels_a_matching_market(lab_frame: tuple[pl.DataFrame, pl.DataFrame]) -> None:
    """A symbol tracking the market exactly must show zero relative strength.

    This is what catches the off-by-one: if the symbol leg spans 64 bars while the SPY leg spans
    63, an identical price path leaves a residual instead of cancelling.
    """
    bars, _ = lab_frame
    spy = bars.filter(pl.col("symbol") == "AAA").select("date", "adj_close")
    out = rl.add_lab_features(bars, spy).filter(pl.col("symbol") == "AAA").sort("date")
    last = out.row(-1, named=True)
    assert last["rs_63d"] == pytest.approx(0.0, abs=1e-12)
    assert last["rs_126d"] == pytest.approx(0.0, abs=1e-12)


def test_add_lab_features_cross_sectional_columns_use_the_whole_frame(lab_frame: tuple[pl.DataFrame, pl.DataFrame]) -> None:
    """`adr_rel` divides by the universe median, so filtering the frame first changes it.

    The docstring warns this must run pre-filter; this is the assumption a future caller is most
    likely to break, and nothing else would notice.
    """
    bars, spy = lab_frame
    both = rl.add_lab_features(bars, spy).filter(pl.col("symbol") == "AAA")["adr_rel"].to_list()
    alone = rl.add_lab_features(bars.filter(pl.col("symbol") == "AAA"), spy)["adr_rel"].to_list()
    assert both[-1] != pytest.approx(alone[-1]), "adr_rel did not depend on the rest of the universe"
