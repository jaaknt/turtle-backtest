"""Guard the canonical metric conventions across `scripts/`.

Ten cohort studies each grew their own Sortino by copy-paste, and every copy divided the
downside deviation by the number of *losers* instead of by N. That is not a rescaling: the
two differ by `sqrt(N / n_losers)`, which depends on each cohort's own win rate, so it
silently reorders cohorts — 17 of 255 pairwise comparisons flipped when they were migrated.
Cohorting exists to compare buckets that differ in win rate, which is exactly the variable
the losers-only denominator cancels out.

Every study now computes its Sortino through `turtlex.backtest.metrics`: trade series via
`compute_trade_metrics`, daily equity-curve series via `compute_daily_sortino`.

These tests do not re-derive the metrics; `tests/backtest/test_metrics.py` covers the maths.
They exist so the *next* study cannot reintroduce a private copy unnoticed.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"

_SORTINO_MENTION = re.compile(r"sortino", re.IGNORECASE)
_CANONICAL_IMPORTS = ("compute_trade_metrics", "compute_daily_sortino")

# A study may reach the canonical helpers indirectly, through a research module that imports
# them itself — qullamaggie-ranking-lab.py gets every Sortino it prints from ranking_lab's
# decile tables and portfolio_replay's equity-curve metric, and importing the helper directly
# just to satisfy a grep would be an unused import. Delegating to one of these counts, and
# `test_delegates_are_themselves_canonical` holds them to the same rule they stand in for.
_CANONICAL_DELEGATES = {
    "turtlex.research.ranking_lab": REPO_ROOT / "turtlex" / "research" / "ranking_lab.py",
    "turtlex.research.portfolio_replay": REPO_ROOT / "turtlex" / "research" / "portfolio_replay.py",
}

# The RMS-of-a-squared-series idiom every private Sortino was built on. An import-only rule
# cannot see this: qullamaggie-exit-sweep.py imported `compute_trade_metrics` for its trade
# metrics while keeping a losers-only `sortino_of` for its daily series, and passed for it.
_RMS_IDIOM = re.compile(r"np\.sqrt\(\s*np\.mean\(")


def _scripts(name_glob: str = "*.py") -> list[Path]:
    return sorted(SCRIPTS_DIR.glob(name_glob))


@pytest.mark.parametrize("path", _scripts(), ids=lambda p: p.name)
def test_sortino_comes_from_the_shared_helpers(path: Path) -> None:
    """A study that reports a Sortino imports one of the canonical helpers."""
    source = path.read_text(encoding="utf-8")
    if not _SORTINO_MENTION.search(source):
        return
    # An import, never a mention: `mod.rsplit(".")[-1] in source` would let a study that merely
    # names ranking_lab in a comment claim delegation while hand-rolling its own Sortino.
    delegates = [mod for mod in _CANONICAL_DELEGATES if re.search(rf"(from|import)\s+[\w.]*{re.escape(mod.rsplit('.', 1)[1])}\b", source)]
    assert any(name in source for name in _CANONICAL_IMPORTS) or delegates, (
        f"{path.name} reports a Sortino without importing any of {_CANONICAL_IMPORTS} "
        f"or delegating to one of {sorted(_CANONICAL_DELEGATES)}. "
        "Use turtlex.backtest.metrics — a private copy that divides downside deviation by "
        "the loser count instead of N reorders cohorts by win rate."
    )


@pytest.mark.parametrize("module", sorted(_CANONICAL_DELEGATES), ids=lambda m: m.rsplit(".", 1)[1])
def test_delegates_are_themselves_canonical(module: str) -> None:
    """A module a study is allowed to delegate its Sortino to must use the shared helpers."""
    source = _CANONICAL_DELEGATES[module].read_text(encoding="utf-8")
    assert any(name in source for name in _CANONICAL_IMPORTS), (
        f"{module} stands in for turtlex.backtest.metrics in test_sortino_comes_from_the_shared_helpers "
        "but does not import it, so studies delegating to it are unguarded."
    )
    assert not _RMS_IDIOM.search(source), f"{module} hand-rolls a downside deviation alongside the helper it delegates to."


@pytest.mark.parametrize("path", _scripts(), ids=lambda p: p.name)
def test_no_private_downside_deviation(path: Path) -> None:
    """Importing the helper is not enough — the file must not also hand-roll one."""
    source = path.read_text(encoding="utf-8")
    if not _SORTINO_MENTION.search(source):
        return
    assert not _RMS_IDIOM.search(source), (
        f"{path.name} mentions Sortino and computes an RMS itself. Downside deviation belongs "
        "to turtlex.backtest.metrics; a second private copy alongside the imported helper is "
        "how qullamaggie-exit-sweep.py kept a losers-only daily Sortino while passing this suite."
    )


@pytest.mark.parametrize("path", _scripts("qullamaggie-cohorts-*.py"), ids=lambda p: p.name)
def test_cohort_studies_use_canonical_metrics(path: Path) -> None:
    """Every cohort study computes its trade metrics via the shared helper."""
    assert "compute_trade_metrics" in path.read_text(encoding="utf-8"), f"{path.name} must compute metrics via compute_trade_metrics."
