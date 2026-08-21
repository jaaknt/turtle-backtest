"""Ranking-hypothesis lab: candidate specs, feature transforms and the fixed judge.

`QullamaggieRanking` sums three piecewise-constant band scores. It separates 366d outcomes on
average but does not order them monotonically — 5/9 non-decreasing decile steps on the held-out
2021+ slice and at s20, against 8/9 in-sample at s12. This module is the machinery for changing
that under a protocol that cannot be gamed, described in `docs/specs/qullamaggie-ranking-loop.md`.

Three structural causes of the non-monotonicity shape what the transforms and aggregations here
offer, and each one has a matching countermeasure:

- **Compensation.** An additive score lets 40 ADR points fully offset a bottom-band SMA50
  distance, so equal scores describe populations that are not comparable. The `min` aggregation
  is the non-compensatory alternative.
- **Tie clumping.** Coarse bands leave hundreds of signals on a handful of scores — 335 s12
  signals score exactly 25 — so a decile boundary falling inside a tie group is arbitrary. `linear_clip` and `percentile_trailing`
  produce continuous scores instead.
- **Regime drift.** An ADR of 5% meant something different in 2017 than in 2021 but scores the
  same points. `percentile_trailing` normalizes against a trailing window of raised signals.

Two invariants this module exists to hold:

1. **Nothing fitted sees the test side.** `sum_then_isotonic` is the only stateful aggregation;
   `evaluate` fits it on the fold's train slice and applies it to the test slice. The stateless
   transforms are also causal — `percentile_trailing` looks strictly backwards — so they are
   fold-safe wherever they are computed.
2. **Sortino always comes from `turtlex.backtest.metrics`.** A private copy that divides
   downside deviation by the loser count instead of N reorders cohorts by win rate, which is
   precisely the variable a decile table is trying to hold still.

A note on the fold design: a 366-day hold means a train slice's *outcomes* extend up to a year
past its cutoff and overlap the test window's entries. That is unavoidable at this horizon
without discarding a year of data per fold, and it is why the acceptance rule leans on
consistency across folds and configs rather than on any single fold's margin.
"""

import json
import logging
import math
import zlib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from turtlex.backtest.metrics import compute_trade_metrics

logger = logging.getLogger(__name__)

# ── Protocol constants — the judge is fixed so candidates stay comparable ────────────────

CACHE_START = date(2010, 1, 1)
CACHE_END = date(2026, 6, 26)
EVAL_START = date(2015, 1, 1)  # portfolio replay window, matching the committed cohort studies
EVAL_END = CACHE_END

# Walk-forward: train on entries before the cutoff, test on the two years after it. Test
# windows overlap between folds; they are six views of the same history, not six
# independent samples, which is why the acceptance rule requires agreement across configs too.
FOLD_CUTOFFS = [date(y, 1, 1) for y in (2019, 2020, 2021, 2022, 2023, 2024)]
TEST_YEARS = 2
# Entries on or after this date are never scored inside the loop. Opened once, at promotion.
HOLDOUT_START = date(2025, 1, 1)

CONFIGS: list[tuple[str, float]] = [("s12", 0.12), ("s16", 0.16), ("s20", 0.20)]
HOLD_CAL = 366
N_DECILES = 10
MIN_LOSERS = 5  # below this a bucket's Sortino is nan and the step is skipped, not counted
MIN_TRAILING_N = 20  # fewer prior signals in the window than this scores the neutral midpoint
MAX_SPREAD_GIVEBACK = 0.35  # absolute D10-D1 Sortino a config may lose; ~10% of a typical 3.4 spread
# Decile boundaries that land inside a tie group are arbitrary, and a coarse band table puts
# hundreds of signals on one score -- the whole of s12's D1 sits in a single tie block. Cutting
# it by row order would also bias the judge towards continuous transforms, which have no ties
# to cut: they would score a cleaner monotonicity for free. Ties are broken at random and the
# fold's metrics averaged over this many redraws instead.
N_TIE_DRAWS = 10
DECILE_SEED = 20260820

TRANSFORMS = ("bands", "linear_clip", "percentile_trailing", "grid2d")
# Every key a spec may carry. Unknown keys are rejected rather than ignored: `"tpo": 40` instead
# of `"top": 40` would otherwise load clean and score the best band 0, inverting the dimension.
SPEC_KEYS = frozenset({"id", "hypothesis", "parent", "aggregate", "terms"})
TERM_KEYS = frozenset(
    {"transform", "feature", "features", "weight", "bands", "top", "lo", "hi", "direction", "window_days", "x_bounds", "y_bounds", "points"}
)
# Transforms that actually read `direction`; declaring it elsewhere is a silent no-op.
DIRECTIONAL_TRANSFORMS = ("linear_clip", "percentile_trailing")
AGGREGATIONS = ("sum", "min", "sum_then_isotonic")

# Built once by `scripts/qullamaggie-ranking-lab.py --build-cache`, then read by every study
# that needs the signal universe without paying for a 16-year database load. Gitignored.
CACHE_DIR = Path(__file__).resolve().parents[2] / ".cache" / "ranking-lab"


def load_cache() -> tuple[dict[str, pl.DataFrame], pl.DataFrame, list[date]]:
    """Read the cached signals, prices and trading calendar.

    Returns:
        `(signals by config name, prices, ascending trading days)`.

    Raises:
        FileNotFoundError: When the cache has not been built yet.
    """
    if not (CACHE_DIR / "prices.parquet").exists():
        raise FileNotFoundError(f"No cache at {CACHE_DIR}. Run scripts/qullamaggie-ranking-lab.py --build-cache first.")
    signals = {name: pl.read_parquet(CACHE_DIR / f"signals-{name}.parquet") for name, _ in CONFIGS}
    prices = pl.read_parquet(CACHE_DIR / "prices.parquet")
    return signals, prices, sorted(pl.read_parquet(CACHE_DIR / "calendar.parquet")["date"].to_list())


# ── Candidate features computed on the cached universe frame ─────────────────────────────


def add_lab_features(df: pl.DataFrame, spy: pl.DataFrame) -> pl.DataFrame:
    """Add the Stage-B candidate feature columns to an indicator frame.

    Rolling inputs (SMAs, rolling max/min, lagged closes) are computed on the *prior* close via
    `shift(1)`, exactly as `turtlex.research.qullamaggie.add_indicators` does. The ratios then
    compare the signal bar's **own** `adj_close` against them — so `pct_off_52w_high`, `rs_63d`,
    `rs_126d`, `sma_stack`, `pct_vs_sma200` and `breadth_sma50` all read the signal-day close,
    and `close_in_range`, `gap_pct` and `breakout_vol_ratio` additionally read that bar's own
    high/low/open/volume. None of it is look-ahead: a Qullamaggie signal is evaluated at that
    day's close and entered at the next open, so every one of those values is known at decision
    time. This docstring is the leakage audit trail, so it lists all of them rather than a
    representative few.

    `adr_rel` and `breadth_sma50` are cross-sectional over whatever symbols the frame holds, so
    this must run on the full qualified universe before any signal filter is applied — running
    it on a signal frame would compute the median over the survivors instead of the universe.

    Args:
        df: Indicator frame from `turtlex.research.qullamaggie.add_indicators`
        spy: Frame with date and adj_close for the market ticker, used for relative strength

    Returns:
        The frame with the candidate feature columns added.
    """
    if df.is_empty():
        return df

    spy_rs = spy.sort("date").select(
        "date",
        (pl.col("adj_close") / pl.col("adj_close").shift(63) - 1.0).alias("_spy_63"),
        (pl.col("adj_close") / pl.col("adj_close").shift(126) - 1.0).alias("_spy_126"),
    )

    df = df.sort(["symbol", "date"]).with_columns(
        pl.col("adj_close").shift(1).over("symbol").alias("_c1"),
        pl.int_range(pl.len()).over("symbol").alias("_row"),
    )
    df = df.with_columns(
        pl.col("_c1").rolling_max(252, min_samples=252).over("symbol").alias("_max_252"),
        pl.col("_c1").rolling_max(50, min_samples=50).over("symbol").alias("_max_50"),
        pl.col("_c1").rolling_min(50, min_samples=50).over("symbol").alias("_min_50"),
        pl.col("_c1").rolling_mean(10, min_samples=10).over("symbol").alias("_sma10"),
        pl.col("_c1").rolling_mean(20, min_samples=20).over("symbol").alias("_sma20"),
        pl.col("_c1").rolling_mean(200, min_samples=200).over("symbol").alias("_sma200"),
        # Plain shifts, not shifts of _c1: _c1 is already shift(1), so shifting it 63 more would
        # span 64 bars against the SPY leg's 63 and inject a day of the symbol's own drift into a
        # feature whose entire purpose is a like-for-like comparison.
        pl.col("adj_close").shift(63).over("symbol").alias("_c_63"),
        pl.col("adj_close").shift(126).over("symbol").alias("_c_126"),
    )
    # Bars since the prior close last set its own 50-day high: forward-fill the row index of
    # the bars that did, then subtract. A rolling arg-max would need a Python-level window.
    df = df.with_columns(
        pl.when(pl.col("_c1") >= pl.col("_max_50"))
        .then(pl.col("_row"))
        .otherwise(None)
        .forward_fill()
        .over("symbol")
        .alias("_last_high_row")
    )
    # Re-sort after the join: the shift(20) below is order-dependent and a join is not
    # guaranteed to preserve the left frame's row order.
    df = df.join(spy_rs, on="date", how="left").sort(["symbol", "date"])

    df = df.with_columns(
        (pl.col("adj_close") / pl.col("_max_252") - 1.0).alias("pct_off_52w_high"),
        ((pl.col("adj_close") / pl.col("_c_63") - 1.0) - pl.col("_spy_63")).alias("rs_63d"),
        ((pl.col("adj_close") / pl.col("_c_126") - 1.0) - pl.col("_spy_126")).alias("rs_126d"),
        (
            (pl.col("adj_close") > pl.col("_sma10")).cast(pl.Int32)
            + (pl.col("_sma10") > pl.col("_sma20")).cast(pl.Int32)
            + (pl.col("_sma20") > pl.col("sma50")).cast(pl.Int32)
            + (pl.col("sma50") > pl.col("_sma200")).cast(pl.Int32)
        ).alias("sma_stack"),
        (pl.col("adj_close") / pl.col("_sma200") - 1.0).alias("pct_vs_sma200"),
        (pl.col("_sma200") / pl.col("_sma200").shift(20).over("symbol") - 1.0).alias("sma200_slope_20d"),
        ((pl.col("_max_50") - pl.col("_min_50")) / pl.col("_max_50")).alias("base_depth_50d"),
        (pl.col("_row") - pl.col("_last_high_row")).cast(pl.Float64).alias("days_since_50d_high"),
        (pl.col("avg_vol_10") / pl.col("avg_vol_50")).alias("vol_dryup"),
        (pl.col("volume").cast(pl.Float64) / pl.col("avg_vol_50")).alias("breakout_vol_ratio"),
        pl.when(pl.col("adj_high") > pl.col("adj_low"))
        .then((pl.col("adj_close") - pl.col("adj_low")) / (pl.col("adj_high") - pl.col("adj_low")))
        .otherwise(0.5)
        .alias("close_in_range"),
        (pl.col("adj_open") / pl.col("_c1") - 1.0).alias("gap_pct"),
        (pl.col("adr_pct") / pl.col("adr_pct").median().over("date")).alias("adr_rel"),
        (pl.col("adj_close") > pl.col("sma50")).cast(pl.Float64).mean().over("date").alias("breadth_sma50"),
    )
    return df.drop(
        [
            "_c1",
            "_row",
            "_max_252",
            "_max_50",
            "_min_50",
            "_sma10",
            "_sma20",
            "_sma200",
            "_c_63",
            "_c_126",
            "_last_high_row",
            "_spy_63",
            "_spy_126",
        ]
    )


LAB_FEATURES = (
    "pct_off_52w_high",
    "rs_63d",
    "rs_126d",
    "sma_stack",
    "pct_vs_sma200",
    "sma200_slope_20d",
    "base_depth_50d",
    "days_since_50d_high",
    "vol_dryup",
    "breakout_vol_ratio",
    "close_in_range",
    "gap_pct",
    "adr_rel",
    "breadth_sma50",
)


# ── Candidate spec ───────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Term:
    """One scored dimension of a candidate ranking.

    Only the fields the term's own transform reads are meaningful; the rest keep their
    defaults. `max_points` is what the `min` aggregation normalizes by.
    """

    transform: str
    features: tuple[str, ...]
    weight: float = 0.0
    bands: tuple[tuple[float, float], ...] = ()
    top: float = 0.0
    lo: float = 0.0
    hi: float = 1.0
    direction: str = "higher"
    window_days: int = 252
    x_bounds: tuple[float, ...] = ()
    y_bounds: tuple[float, ...] = ()
    points: tuple[tuple[float, ...], ...] = ()

    @property
    def max_points(self) -> float:
        """The largest score this term can award, used to normalize under `min`."""
        if self.transform == "bands":
            return max([p for _, p in self.bands] + [self.top])
        if self.transform == "grid2d":
            return max(max(row) for row in self.points)
        return self.weight


@dataclass(frozen=True)
class CandidateSpec:
    """A ranking hypothesis, loaded from `docs/research/ranking-lab/candidates/*.json`."""

    id: str
    hypothesis: str
    parent: str
    aggregate: str
    terms: tuple[Term, ...]

    @property
    def features(self) -> tuple[str, ...]:
        """Every feature column this spec reads, deduplicated in first-seen order."""
        seen: dict[str, None] = {}
        for t in self.terms:
            for f in t.features:
                seen[f] = None
        return tuple(seen)


def load_spec(path: Path) -> CandidateSpec:
    """Load and validate one candidate spec.

    Validation is strict on purpose. A typo in a transform name or a feature name would
    otherwise score that dimension 0 for every signal and quietly hand the comparison to
    whichever arm still had all its inputs — the same failure `qullamaggie-ranking-weights.py`
    guards against with its `required` column check.

    Args:
        path: Path to the candidate JSON file

    Returns:
        The parsed spec.

    Raises:
        ValueError: On an unknown transform or aggregation, a malformed term, or a
            `grid2d` points matrix whose shape does not match its bounds.
    """
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    for key in ("id", "hypothesis", "aggregate", "terms"):
        if key not in raw:
            raise ValueError(f"{path.name}: missing required key {key!r}")
    if unknown := set(raw) - SPEC_KEYS:
        raise ValueError(f"{path.name}: unknown spec keys {sorted(unknown)}; expected {sorted(SPEC_KEYS)}")
    if raw["aggregate"] not in AGGREGATIONS:
        raise ValueError(f"{path.name}: unknown aggregate {raw['aggregate']!r}; expected one of {AGGREGATIONS}")

    terms: list[Term] = []
    for i, t in enumerate(raw["terms"]):
        transform = t.get("transform")
        if transform not in TRANSFORMS:
            raise ValueError(f"{path.name}: term {i} has unknown transform {transform!r}; expected one of {TRANSFORMS}")
        if unknown := set(t) - TERM_KEYS:
            raise ValueError(f"{path.name}: term {i} has unknown keys {sorted(unknown)}; expected {sorted(TERM_KEYS)}")
        # `top` defaults to 0, so omitting it silently sends the BEST values to zero — an
        # inversion, not a degradation. 0 is a legitimate declared value, so require it explicitly.
        if transform == "bands" and "top" not in t:
            raise ValueError(
                f"{path.name}: term {i} is a bands transform without an explicit 'top'; values above the last bound would score 0"
            )
        if "direction" in t and transform not in DIRECTIONAL_TRANSFORMS:
            raise ValueError(
                f"{path.name}: term {i} declares 'direction' but {transform!r} ignores it; only {DIRECTIONAL_TRANSFORMS} read it"
            )
        features = tuple(t["features"]) if "features" in t else (t["feature"],)
        term = Term(
            transform=transform,
            features=features,
            weight=float(t.get("weight", 0.0)),
            bands=tuple((float(b), float(p)) for b, p in t.get("bands", [])),
            top=float(t.get("top", 0.0)),
            lo=float(t.get("lo", 0.0)),
            hi=float(t.get("hi", 1.0)),
            direction=str(t.get("direction", "higher")),
            window_days=int(t.get("window_days", 252)),
            x_bounds=tuple(float(x) for x in t.get("x_bounds", [])),
            y_bounds=tuple(float(y) for y in t.get("y_bounds", [])),
            points=tuple(tuple(float(p) for p in row) for row in t.get("points", [])),
        )
        _validate_term(path.name, i, term)
        terms.append(term)

    if raw["aggregate"] == "min" and len({t.weight for t in terms}) > 1:
        logger.info(
            "%s: aggregate 'min' normalizes each term by its own max, so the declared weights do not affect ordering",
            path.name,
        )
    return CandidateSpec(
        id=str(raw["id"]),
        hypothesis=str(raw["hypothesis"]),
        parent=str(raw.get("parent", "")),
        aggregate=str(raw["aggregate"]),
        terms=tuple(terms),
    )


def _validate_term(name: str, i: int, term: Term) -> None:
    if term.direction not in ("higher", "lower"):
        raise ValueError(f"{name}: term {i} has direction {term.direction!r}; expected 'higher' or 'lower'")
    if term.transform == "bands":
        if not term.bands:
            raise ValueError(f"{name}: term {i} is a bands transform with no bands")
        bounds = [b for b, _ in term.bands]
        if bounds != sorted(bounds):
            raise ValueError(f"{name}: term {i} band bounds are not ascending: {bounds}")
    elif term.transform == "linear_clip":
        if term.hi <= term.lo:
            raise ValueError(f"{name}: term {i} needs hi > lo, got lo={term.lo} hi={term.hi}")
    elif term.transform == "grid2d":
        if len(term.features) != 2:
            raise ValueError(f"{name}: term {i} is grid2d and needs exactly two features, got {term.features}")
        for axis, axis_bounds in (("x", term.x_bounds), ("y", term.y_bounds)):
            if list(axis_bounds) != sorted(axis_bounds):
                raise ValueError(f"{name}: term {i} grid2d {axis}_bounds are not ascending: {list(axis_bounds)}")
        want = (len(term.x_bounds) + 1, len(term.y_bounds) + 1)
        got = (len(term.points), len(term.points[0]) if term.points else 0)
        if got != want:
            raise ValueError(f"{name}: term {i} grid2d points is {got}, but its bounds imply {want}")
        # Only points[0] is measured above, so a ragged matrix would pass here and die inside
        # numpy at scoring time instead.
        if len({len(row) for row in term.points}) > 1:
            raise ValueError(f"{name}: term {i} grid2d points rows have differing lengths {[len(r) for r in term.points]}")
    if term.transform in ("linear_clip", "percentile_trailing") and term.weight <= 0:
        raise ValueError(f"{name}: term {i} uses {term.transform} and needs a positive weight")


# ── Transforms and scoring ───────────────────────────────────────────────────────────────


def _column(sig: pl.DataFrame, feature: str) -> np.ndarray:
    if feature not in sig.columns:
        raise ValueError(f"Signal frame has no column {feature!r}; available: {sorted(sig.columns)}")
    return sig[feature].cast(pl.Float64).to_numpy(allow_copy=True).astype(float)


def _bucket(values: np.ndarray, bounds: tuple[float, ...]) -> np.ndarray:
    """Index of the first bound that exceeds each value; len(bounds) for values at or above all."""
    return np.searchsorted(np.asarray(bounds, dtype=float), values, side="right")


def apply_term(sig: pl.DataFrame, term: Term) -> np.ndarray:
    """Score every signal on one term.

    A null or non-finite feature value scores 0, matching `QullamaggieRanking._band_score`.
    That fallback is not graceful — a missing column costs the term's whole weight — so
    `load_spec` and `_column` fail loudly on a name that does not exist rather than letting a
    typo silently zero a dimension.

    Args:
        sig: Signal frame, sorted ascending by date for `percentile_trailing`
        term: The term to apply

    Returns:
        Float points per signal, in the frame's row order.
    """
    if term.transform == "grid2d":
        x, y = _column(sig, term.features[0]), _column(sig, term.features[1])
        grid = np.asarray(term.points, dtype=float)
        pts = grid[np.clip(_bucket(x, term.x_bounds), 0, grid.shape[0] - 1), np.clip(_bucket(y, term.y_bounds), 0, grid.shape[1] - 1)]
        return np.where(np.isfinite(x) & np.isfinite(y), pts, 0.0)

    v = _column(sig, term.features[0])
    ok = np.isfinite(v)

    if term.transform == "bands":
        table = np.array([p for _, p in term.bands] + [term.top], dtype=float)
        return np.where(ok, table[_bucket(v, tuple(b for b, _ in term.bands))], 0.0)

    if term.transform == "linear_clip":
        t = np.clip((v - term.lo) / (term.hi - term.lo), 0.0, 1.0)
    else:  # percentile_trailing
        t = _trailing_percentile(sig["date"].to_list(), v, term.window_days)

    if term.direction == "lower":
        t = 1.0 - t
    return np.where(ok, term.weight * t, 0.0)


def _trailing_percentile(dates: list[date], values: np.ndarray, window_days: int) -> np.ndarray:
    """Percentile rank of each value among the raised signals of the preceding `window_days`.

    Strictly backwards-looking: a signal is ranked against signals raised on *earlier dates*,
    never against its own contemporaries, so the result is fold-safe wherever it is computed and
    does not depend on how same-day rows happen to be ordered. Rows with fewer than
    `MIN_TRAILING_N` predecessors in the window score the neutral 0.5 rather than an extreme —
    early history would otherwise be scored against a handful of samples and pushed to the tails.

    `window_days` is in calendar days, matching the epoch-day arithmetic below. 252 is therefore
    roughly eight months, not the trading year that number usually denotes.
    """
    dints = np.array([(d - date(1970, 1, 1)).days for d in dates], dtype=np.int64)
    order = np.argsort(dints, kind="stable")
    sorted_dints, sorted_vals = dints[order], values[order]
    out = np.full(len(values), 0.5)
    starts = np.searchsorted(sorted_dints, sorted_dints - window_days, side="left")
    # End at the first row sharing this row's date, not at the row itself: slicing to `i` ranks a
    # signal against its own same-day peers, and because callers sort by (date, symbol) that makes
    # the score depend on the ticker's alphabetical position.
    ends = np.searchsorted(sorted_dints, sorted_dints, side="left")
    for i in range(len(sorted_vals)):
        window = sorted_vals[starts[i] : ends[i]]
        window = window[np.isfinite(window)]
        if window.size < MIN_TRAILING_N or not np.isfinite(sorted_vals[i]):
            continue
        out[order[i]] = float((window < sorted_vals[i]).mean() + 0.5 * (window == sorted_vals[i]).mean())
    return out


def raw_scores(sig: pl.DataFrame, spec: CandidateSpec) -> np.ndarray:
    """Aggregate every term into one score per signal, before any isotonic calibration.

    `sum` and `sum_then_isotonic` both return the plain sum here — the calibration is applied
    per fold by `evaluate`, because it is the one piece that must be fitted on train data only.

    Args:
        sig: Signal frame
        spec: The candidate

    Returns:
        One float score per signal, in the frame's row order.
    """
    per_term = [apply_term(sig, t) for t in spec.terms]
    if spec.aggregate == "min":
        normed = [p / t.max_points if t.max_points > 0 else np.zeros_like(p) for p, t in zip(per_term, spec.terms, strict=True)]
        return 100.0 * np.min(np.vstack(normed), axis=0)
    return np.sum(np.vstack(per_term), axis=0)


# ── Isotonic calibration (PAVA) and rank correlation ─────────────────────────────────────


def isotonic_fit(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Fit a non-decreasing step function of `y` on `x` by pool-adjacent-violators.

    This is what makes `sum_then_isotonic` worth testing: the fitted map is monotone *by
    construction* on the training slice, so whether the test slice stays monotone is a genuine
    out-of-sample question rather than a restatement of the fit.

    Implemented here rather than imported because the project carries neither scipy nor
    scikit-learn, and PAVA is twenty lines.

    Args:
        x: Raw scores to calibrate
        y: Outcome to calibrate against, e.g. year-demeaned forward return

    Returns:
        `(knots, values)` — ascending unique x values and the fitted non-decreasing y at each,
        suitable for `isotonic_apply`. Both are empty when no finite pair was supplied.
    """
    ok = np.isfinite(x) & np.isfinite(y)
    if not ok.any():
        return np.array([]), np.array([])
    xs, ys = x[ok], y[ok]
    order = np.argsort(xs, kind="stable")
    xs, ys = xs[order], ys[order]

    knots: list[float] = []
    sums: list[float] = []
    counts: list[int] = []
    for xi, yi in zip(xs, ys, strict=True):
        if knots and xi == knots[-1]:  # tie: pool into the current block
            sums[-1] += yi
            counts[-1] += 1
        else:
            knots.append(float(xi))
            sums.append(float(yi))
            counts.append(1)
        # Pool backwards while the running means violate monotonicity. Pop first, then add
        # into the new last block -- `sums[-2] += sums.pop()` would resolve `sums[-2]` against
        # the already-shortened list and corrupt the block one further back.
        while len(sums) > 1 and sums[-2] / counts[-2] > sums[-1] / counts[-1]:
            block_sum, block_count = sums.pop(), counts.pop()
            sums[-1] += block_sum
            counts[-1] += block_count
            knots.pop(-2)  # the merged block is represented at its largest x
    return np.array(knots), np.array([s / c for s, c in zip(sums, counts, strict=True)])


def isotonic_apply(knots: np.ndarray, values: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Map raw scores through a fitted isotonic step function, rescaled to 0-100.

    Args:
        knots: Ascending x breakpoints from `isotonic_fit`
        values: Fitted non-decreasing y at each knot
        x: Raw scores to map

    Returns:
        Calibrated scores in 0-100; all zeros if the fit was degenerate or empty.
    """
    if knots.size == 0:
        return np.zeros_like(x)
    # Step, never interpolate. Each knot is a pooled block's LARGEST x, so `np.interp` would ramp
    # across the block and separate the very values PAVA just pooled — restoring their original
    # order and making the calibration a rank-preserving no-op. Since every metric here is
    # rank-based, that reads as "isotonic changed nothing" when in fact it was never applied.
    mapped = values[np.clip(np.searchsorted(knots, x, side="left"), 0, len(values) - 1)]
    lo, hi = float(values.min()), float(values.max())
    if hi <= lo:
        return np.zeros_like(x)
    return 100.0 * (mapped - lo) / (hi - lo)


def _rank(a: np.ndarray) -> np.ndarray:
    """Average ranks, ties shared — the ranking Spearman's rho is defined on."""
    order = np.argsort(a, kind="stable")
    ranks = np.empty(len(a), dtype=float)
    ranks[order] = np.arange(1, len(a) + 1, dtype=float)
    sorted_a = a[order]
    i = 0
    while i < len(sorted_a):
        j = i
        while j + 1 < len(sorted_a) and sorted_a[j + 1] == sorted_a[i]:
            j += 1
        if j > i:
            ranks[order[i : j + 1]] = ranks[order[i : j + 1]].mean()
        i = j + 1
    return ranks


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    """Spearman rank correlation, computed as Pearson on average ranks.

    Args:
        a: First series
        b: Second series, same length

    Returns:
        The correlation, or nan when fewer than three finite pairs exist or either series is
        constant (an all-ties score has no ordering to correlate).
    """
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 3:
        return float("nan")
    ra, rb = _rank(a[ok]), _rank(b[ok])
    sa, sb = ra.std(), rb.std()
    if sa == 0 or sb == 0:
        return float("nan")
    return float(((ra - ra.mean()) * (rb - rb.mean())).mean() / (sa * sb))


# ── Decile tables and monotonicity ───────────────────────────────────────────────────────


def compute_deciles(scores: np.ndarray, returns: np.ndarray, rng: np.random.Generator | None = None) -> list[dict]:
    """Bucket signals into `N_DECILES` equal-size groups by ascending score, D1 lowest.

    Args:
        scores: One score per signal
        returns: Forward return per signal as a fraction (0.25 for +25%)
        rng: Tie-break source. Without one, signals sharing a score are cut by row order, which
            makes a decile boundary inside a tie group arbitrary and hands continuous scores an
            advantage they have not earned. Pass one; `evaluate` does, and redraws.

    Returns:
        One dict per non-empty decile with n, score, med, mean, win, sortino and pf.
    """
    order = np.argsort(scores, kind="stable") if rng is None else np.lexsort((rng.random(len(scores)), scores))
    edges = np.linspace(0, len(scores), N_DECILES + 1).astype(int)
    out: list[dict] = []
    for d in range(N_DECILES):
        idx = order[edges[d] : edges[d + 1]]
        if idx.size == 0:
            continue
        m = compute_trade_metrics(returns[idx] * 100.0, HOLD_CAL, min_losers=MIN_LOSERS)
        if m is None:
            continue
        out.append(
            {
                "n": m.n,
                "score": float(scores[idx].mean()),
                "med": m.median_pct,
                "mean": m.mean_pct,
                "win": m.win_pct,
                "sortino": m.sortino,
                "pf": m.profit_factor,
            }
        )
    return out


def monotone_steps(values: list[float]) -> tuple[int, int]:
    """Count non-decreasing steps between consecutive deciles, skipping nan pairs.

    Returns `(steps, comparable)` rather than a bare fraction: a fold whose thin deciles fall
    below `MIN_LOSERS` has fewer than nine comparable steps, and reporting 4/9 for it when only
    five steps could be judged would read as a much worse result than it is.

    Args:
        values: One metric per decile, ascending by score

    Returns:
        `(non-decreasing steps, comparable steps)`.
    """
    steps = comparable = 0
    for i in range(1, len(values)):
        a, b = values[i - 1], values[i]
        if math.isnan(a) or math.isnan(b):
            continue
        comparable += 1
        if b >= a:
            steps += 1
    return steps, comparable


# ── Fold evaluation ──────────────────────────────────────────────────────────────────────


def _decile_rng(config: str, cutoff: date) -> np.random.Generator:
    """Tie-break generator for one (config, fold) cell.

    Seeded from a CRC of the config name, never `hash()`: Python randomizes string hashing per
    process unless PYTHONHASHSEED is pinned, so a `hash()`-derived seed would give the same
    candidate a different scorecard on every run — and the baseline is re-scored on every
    `--eval`, so both sides of every comparison would drift between runs.

    Args:
        config: Entry-filter config name, e.g. "s12"
        cutoff: The fold's train/test cutoff
    """
    return np.random.default_rng([DECILE_SEED, zlib.crc32(config.encode()), cutoff.toordinal()])


def _fraction(steps: int, comparable: int) -> float:
    """Non-decreasing steps as a fraction of the comparable ones, or nan when none were."""
    return steps / comparable if comparable else float("nan")


def _nanmean(values: list[float]) -> float:
    """Mean of the finite values, nan when there are none."""
    finite = [v for v in values if not math.isnan(v)]
    return float(np.mean(finite)) if finite else float("nan")


@dataclass(frozen=True)
class FoldResult:
    """One candidate scored on one (config, cutoff) fold's held-out slice.

    Every metric here is a mean over `N_TIE_DRAWS` random decile tie-breaks, so a fold's
    monotonicity is a fraction rather than a count of steps — two schemes with very different
    tie structure stay comparable.
    """

    config: str
    cutoff: date
    n_train: int
    n_test: int
    mono_sortino: float
    mono_mean: float
    spearman: float
    spread: float
    top_decile_sortino: float
    deciles: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class Scorecard:
    """Every fold of one candidate, plus the aggregates the acceptance rule reads."""

    spec_id: str
    folds: list[FoldResult]
    # Folds evaluate() could not measure. Kept on the scorecard rather than only in a debug log,
    # because no script under scripts/ bootstraps logging, so those lines go nowhere.
    skipped: list[tuple[str, date, str]] = field(default_factory=list)

    def _mean(self, attr: str, config: str | None = None) -> float:
        vals = [float(getattr(f, attr)) for f in self.folds if config is None or f.config == config]
        vals = [v for v in vals if not math.isnan(v)]
        return float(np.mean(vals)) if vals else float("nan")

    def count(self, attr: str, config: str | None = None) -> int:
        """How many folds actually contributed to an aggregate.

        `_mean` drops nan folds per attribute independently, so two metrics of the same config
        can be averaged over different fold sets — s20's spread is a 5-fold mean while its
        monotonicity is a 6-fold mean. Comparing a candidate's aggregate against a baseline's
        without checking this compares unpaired samples, so `judge` reads it.

        Args:
            attr: `FoldResult` field name
            config: Restrict to one entry-filter config, or None for all
        """
        return sum(1 for f in self.folds if (config is None or f.config == config) and not math.isnan(float(getattr(f, attr))))

    @property
    def mono_sortino(self) -> float:
        """Fold-mean fraction of non-decreasing Sortino decile steps, all configs."""
        return self._mean("mono_sortino")

    @property
    def spearman(self) -> float:
        """Fold-mean Spearman rho between score and year-demeaned forward return."""
        return self._mean("spearman")

    @property
    def spread(self) -> float:
        """Fold-mean D10 minus D1 Sortino."""
        return self._mean("spread")

    def by_config(self, config: str) -> dict[str, float]:
        """Fold-mean monotonicity, rho and spread restricted to one entry-filter config.

        Args:
            config: One of the `CONFIGS` names, e.g. "s12"
        """
        return {
            "mono_sortino": self._mean("mono_sortino", config),
            "spearman": self._mean("spearman", config),
            "spread": self._mean("spread", config),
        }


def fold_windows() -> list[tuple[date, date, date]]:
    """The walk-forward folds as `(cutoff, test_start, test_end)`, test end exclusive.

    The last fold's test window is clipped at `HOLDOUT_START` so no fold ever scores an entry
    the loop is not allowed to see.
    """
    out = []
    for cutoff in FOLD_CUTOFFS:
        test_end = min(date(cutoff.year + TEST_YEARS, cutoff.month, cutoff.day), HOLDOUT_START)
        if test_end > cutoff:
            out.append((cutoff, cutoff, test_end))
    return out


def evaluate(spec: CandidateSpec, signals: dict[str, pl.DataFrame]) -> Scorecard:
    """Score a candidate on every (config, fold) cell of the fixed protocol.

    `sum_then_isotonic` is fitted on each fold's train slice — entries strictly before the
    cutoff — and applied to the test slice. Everything else is stateless and causal, so the
    same raw scores serve every fold.

    Args:
        spec: The candidate to judge
        signals: Cached signal frames keyed by config name, each carrying `entry_date`,
            `ret` and `ret_demeaned`

    Returns:
        The candidate's scorecard.
    """
    folds: list[FoldResult] = []
    skipped: list[tuple[str, date, str]] = []
    for config, sig in signals.items():
        sig = sig.sort(["date", "symbol"])
        raw = raw_scores(sig, spec)
        entry = np.array([(d - date(1970, 1, 1)).days for d in sig["entry_date"].to_list()], dtype=np.int64)
        ret = sig["ret"].to_numpy(allow_copy=True).astype(float)
        demeaned = sig["ret_demeaned"].to_numpy(allow_copy=True).astype(float)

        for cutoff, test_start, test_end in fold_windows():
            train = entry < (cutoff - date(1970, 1, 1)).days
            test = (entry >= (test_start - date(1970, 1, 1)).days) & (entry < (test_end - date(1970, 1, 1)).days)
            if test.sum() < N_DECILES * 2 or train.sum() < 100:
                logger.debug("Skipping %s @ %s: train=%d test=%d", config, cutoff, train.sum(), test.sum())
                skipped.append((config, cutoff, f"train={int(train.sum())} test={int(test.sum())}"))
                continue

            scores = raw
            if spec.aggregate == "sum_then_isotonic":
                knots, values = isotonic_fit(raw[train], demeaned[train])
                # A fit that pools everything into one block returns all zeros, and constant
                # scores make compute_deciles a purely random partition — whose monotonicity is
                # a coin flip that would be averaged in as though it were measured.
                if knots.size == 0 or float(values.max()) <= float(values.min()):
                    logger.debug("Skipping %s @ %s: isotonic fit degenerate", config, cutoff)
                    skipped.append((config, cutoff, "degenerate isotonic fit"))
                    continue
                scores = isotonic_apply(knots, values, raw)

            rng = _decile_rng(config, cutoff)
            draws = [compute_deciles(scores[test], ret[test], rng) for _ in range(N_TIE_DRAWS)]
            draws = [d for d in draws if len(d) == N_DECILES]
            if not draws:
                logger.debug("Skipping %s @ %s: deciles never resolved", config, cutoff)
                skipped.append((config, cutoff, "deciles never resolved"))
                continue
            mono_s = [_fraction(*monotone_steps([d["sortino"] for d in dec])) for dec in draws]
            mono_m = [_fraction(*monotone_steps([d["mean"] for d in dec])) for dec in draws]
            folds.append(
                FoldResult(
                    config=config,
                    cutoff=cutoff,
                    n_train=int(train.sum()),
                    n_test=int(test.sum()),
                    mono_sortino=_nanmean(mono_s),
                    mono_mean=_nanmean(mono_m),
                    spearman=spearman(scores[test], demeaned[test]),
                    spread=_nanmean([dec[-1]["sortino"] - dec[0]["sortino"] for dec in draws]),
                    top_decile_sortino=_nanmean([dec[-1]["sortino"] for dec in draws]),
                    deciles=draws[0],
                )
            )
    return Scorecard(spec_id=spec.id, folds=folds, skipped=skipped)


# ── Acceptance rule ──────────────────────────────────────────────────────────────────────


def required_margin(n_tested: int) -> float:
    """Spearman improvement a candidate must clear, given how many have been tried.

    Search over enough hypotheses and one will beat any fixed bar by chance, so the bar rises
    with the size of the search. The shape is deliberately gentle — doubling the number of
    attempts adds 0.002 rho — because the acceptance rule's real defence is agreement across
    folds and configs, not this number.

    Args:
        n_tested: Hypotheses already recorded in the ledger

    Returns:
        The rho margin required on top of the baseline.
    """
    return 0.01 + 0.002 * math.log2(max(1.0, n_tested / 10.0))


@dataclass(frozen=True)
class Verdict:
    """Every reason a candidate did not replace the baseline; empty means it did.

    `accepted` is derived rather than stored. It used to be a field, and callers that appended
    to a mutable `reasons` list — which `frozen=True` does not prevent — left it stale and true
    for a candidate that had just been rejected.
    """

    reasons: tuple[str, ...] = ()

    @property
    def accepted(self) -> bool:
        """True when no gate reported a failure."""
        return not self.reasons


def judge(candidate: Scorecard, baseline: Scorecard, n_tested: int) -> Verdict:
    """Apply the monotonicity half of the acceptance rule.

    Portfolio confirmation is deliberately *not* checked here: it is the expensive half, so
    the caller runs it only for candidates that clear these gates, then folds its own verdict
    in. A candidate passing `judge` has not yet been accepted.

    Args:
        candidate: The candidate's scorecard
        baseline: The reigning baseline's scorecard, from the same protocol
        n_tested: Hypotheses already recorded, for the multiple-testing margin

    Returns:
        A verdict whose `reasons` list every failed gate, empty when all passed.
    """
    reasons: list[str] = []
    margin = required_margin(n_tested)

    def gate(value: float, bound: float, what: str) -> None:
        """Record a failure when `value` is below `bound`, or when either is unmeasurable.

        Every gate routes through here so nan is handled the same way everywhere. `nan < x` is
        False, so a bare comparison silently *passes* a gate it could not evaluate — which is
        the wrong default for an acceptance rule: "could not be measured" must never read as
        "fine". This is live, not hypothetical: the s20 2024 fold already yields a nan spread.
        """
        if math.isnan(value) or math.isnan(bound):
            reasons.append(f"{what} unmeasurable (candidate {value:.4f}, bound {bound:.4f})")
        elif value < bound:
            reasons.append(f"{what} {value:.4f} < {bound:.4f}")

    gate(candidate.mono_sortino, baseline.mono_sortino, "mono_sortino")
    gate(candidate.spearman, baseline.spearman + margin, f"spearman (margin {margin:.4f})")

    for config, _ in CONFIGS:
        c, b = candidate.by_config(config), baseline.by_config(config)
        # Aggregates averaged over different fold sets are not paired samples, so comparing them
        # would penalise whichever arm produced more measurable folds. Refuse instead. `spearman`
        # is checked here too, even though its only gate is the overall one above: `_mean` drops
        # nan folds per attribute, and `spearman` returns nan for a fold whose scores are all tied,
        # so a candidate that ties on one hard fold would have that fold silently dropped from its
        # rho mean while the baseline kept all six — clearing the margin by being measured on an
        # easier subset. The overall mean is these per-config folds pooled, so checking parity per
        # config covers it.
        for attr in ("mono_sortino", "spearman", "spread"):
            n_c, n_b = candidate.count(attr, config), baseline.count(attr, config)
            if n_c != n_b:
                reasons.append(f"{config}: {attr} averaged over {n_c} candidate folds vs {n_b} baseline folds — not comparable")
        # One decile step out of nine is 0.111; a config may give up that much but no more.
        gate(c["mono_sortino"], b["mono_sortino"] - 1.0 / 9.0, f"{config}: mono_sortino")
        # An absolute give-back, not 90% of the baseline: a proportional rule inverts when the
        # baseline spread is negative (0.9 * -2.0 = -1.8 demands the candidate *beat* -2.0), and
        # individual folds do go negative — s16 2022 is -3.177.
        gate(c["spread"], b["spread"] - MAX_SPREAD_GIVEBACK, f"{config}: spread")

    return Verdict(tuple(reasons))
