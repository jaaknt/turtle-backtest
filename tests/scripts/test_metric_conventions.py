"""Guard the canonical trade-metric convention across `scripts/`.

Ten cohort studies each grew their own Sortino by copy-paste, and every copy divided the
downside deviation by the number of *losers* instead of by N. That is not a rescaling: the
two differ by `sqrt(N / n_losers)`, which depends on each cohort's own win rate, so it
silently reorders cohorts — 17 of 255 pairwise comparisons flipped when they were migrated.
Cohorting exists to compare buckets that differ in win rate, which is exactly the variable
the losers-only denominator cancels out.

These tests do not re-derive the metric; `tests/backtest/test_metrics.py` covers the maths.
They exist so the *next* study cannot reintroduce a private copy unnoticed.
"""

import re
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"

# A file that reports a Sortino but never imports the shared helper is computing its own.
_SORTINO_MENTION = re.compile(r"sortino", re.IGNORECASE)
_CANONICAL_IMPORT = "compute_trade_metrics"

# Studies that still carry a private Sortino. Each entry is recorded technical debt, not an
# exemption on principle — the list may shrink, never grow. Migrating one means regenerating
# its result doc, so they are handled deliberately rather than in bulk.
#
# Trade-level — same losers-only bug the cohort studies had; these should move to
# `compute_trade_metrics` and have their docs regenerated:
#   qullamaggie-sma200.py, qullamaggie-longterm-monthly.py, qullamaggie-ranking-validation.py
# Daily equity-curve — Sortino over a daily return series annualized by sqrt(252), which
# `compute_trade_metrics` deliberately does not cover (see its module docstring: equity-curve
# metrics belong in turtlex/portfolio/analytics.py). They share the losers-only flaw but need
# a daily-series helper, not this one:
#   qullamaggie-portfolio-sim.py, qullamaggie-ranking-weights.py
# Already correct, merely hand-rolled — divides by all N, so its numbers are right:
#   qullamaggie-relax-sweep.py
#
# Not covered by this check: a script that imports the helper for its trade metrics *and*
# keeps a private daily-series Sortino passes, because the rule is import-based.
# qullamaggie-exit-sweep.py is that case — its `sortino_of` is still losers-only.
KNOWN_PRIVATE_SORTINO = frozenset(
    {
        "qullamaggie-sma200.py",
        "qullamaggie-longterm-monthly.py",
        "qullamaggie-ranking-validation.py",
        "qullamaggie-portfolio-sim.py",
        "qullamaggie-ranking-weights.py",
        "qullamaggie-relax-sweep.py",
    }
)


def _scripts_with_private_sortino() -> set[str]:
    """Names of `scripts/*.py` that report a Sortino without importing the shared helper."""
    offenders: set[str] = set()
    for path in SCRIPTS_DIR.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        if _SORTINO_MENTION.search(source) and _CANONICAL_IMPORT not in source:
            offenders.add(path.name)
    return offenders


def test_no_new_private_sortino() -> None:
    """A new study must use `compute_trade_metrics`, not a private copy."""
    new = _scripts_with_private_sortino() - KNOWN_PRIVATE_SORTINO
    assert not new, (
        f"{sorted(new)} report a Sortino without importing {_CANONICAL_IMPORT}. "
        "Use turtlex.backtest.metrics.compute_trade_metrics — a private copy that divides "
        "downside deviation by the loser count instead of N reorders cohorts by win rate."
    )


def test_known_private_sortino_list_has_no_stale_entries() -> None:
    """The allowlist shrinks as studies migrate; a stale entry means it was never pruned."""
    stale = KNOWN_PRIVATE_SORTINO - _scripts_with_private_sortino()
    assert not stale, f"{sorted(stale)} now use the shared helper — remove them from KNOWN_PRIVATE_SORTINO."


@pytest.mark.parametrize("path", sorted(SCRIPTS_DIR.glob("qullamaggie-cohorts-*.py")), ids=lambda p: p.name)
def test_cohort_studies_use_canonical_metrics(path: Path) -> None:
    """Every cohort study uses the shared helper — no allowlist, this is settled."""
    assert _CANONICAL_IMPORT in path.read_text(encoding="utf-8"), f"{path.name} must compute metrics via {_CANONICAL_IMPORT}."
