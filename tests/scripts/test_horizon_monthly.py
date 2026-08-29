"""The marginal decomposition has one property worth guarding: it must chain back to the whole.

`monthly_marks` anchors month 1 on the entry fill and every later month on the previous month's
close, so an off-by-one in either end silently rescales the whole curve without making any single
cell look wrong. The product of the 18 marginal returns has to equal the 18-month cumulative
return exactly, and that is the check that catches it.

`add_months` is tested separately because the clamping case (Jan 31 + 1 month) is the one place
exact calendar arithmetic can raise instead of returning, and it only shows up on a handful of
entry dates a year.

The script is loaded by path because `scripts/` holds hyphenated files that are not importable
as modules.
"""

import importlib.util
from datetime import date
from math import prod
from pathlib import Path
from types import ModuleType

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "qullamaggie-horizon-monthly.py"

_EPOCH = date(1970, 1, 1)


@pytest.fixture(scope="module")
def study() -> ModuleType:
    """The script module, imported by path."""
    spec = importlib.util.spec_from_file_location("qullamaggie_horizon_monthly", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _daily_series(start: date, days: int, step: float) -> tuple[np.ndarray, np.ndarray]:
    """A gap-free daily series compounding at `step` per day, so every month resolves a mark."""
    start_int = (start - _EPOCH).days
    dates = np.arange(start_int, start_int + days, dtype=np.int64)
    closes = 100.0 * np.power(1.0 + step, np.arange(days, dtype=np.float64))
    return dates, closes


def test_add_months_clamps_to_the_shorter_month(study: ModuleType) -> None:
    assert study.add_months(date(2021, 1, 31), 1) == date(2021, 2, 28)
    assert study.add_months(date(2020, 1, 31), 1) == date(2020, 2, 29)  # leap year
    assert study.add_months(date(2021, 3, 31), 1) == date(2021, 4, 30)


def test_add_months_rolls_the_year_over(study: ModuleType) -> None:
    assert study.add_months(date(2021, 6, 15), 0) == date(2021, 6, 15)
    assert study.add_months(date(2021, 6, 15), 12) == date(2022, 6, 15)
    assert study.add_months(date(2021, 6, 15), 18) == date(2022, 12, 15)


def test_marginal_returns_chain_back_to_the_cumulative_return(study: ModuleType) -> None:
    """prod(1 + ret[M]) must equal mark[18] / entry_price — the whole point of the decomposition."""
    entry = date(2021, 1, 15)
    dates, closes = _daily_series(entry, days=700, step=0.001)
    entry_price = 97.5  # a fill below the first close, as an adjusted open would be

    marks = study.monthly_marks(entry, entry_price, dates, closes)
    rets = study.marginal_returns(marks)

    assert all(r is not None for r in rets), "a gap-free 700-day series should mark all 18 months"
    assert marks[0] == entry_price
    assert prod(1.0 + r for r in rets) == pytest.approx(marks[study.MAX_MONTH] / entry_price)


def test_month_one_is_measured_from_the_entry_fill_not_the_first_close(study: ModuleType) -> None:
    entry = date(2021, 1, 15)
    dates, closes = _daily_series(entry, days=700, step=0.001)
    entry_price = 50.0

    marks = study.monthly_marks(entry, entry_price, dates, closes)
    rets = study.marginal_returns(marks)

    # The mark is the first bar on or after entry + 1 month, and month 1 runs from the fill.
    target = (study.add_months(entry, 1) - _EPOCH).days
    expected_mark = float(closes[int(np.searchsorted(dates, target))])
    assert marks[1] == pytest.approx(expected_mark)
    assert rets[0] == pytest.approx(expected_mark / entry_price - 1.0)


def test_a_thin_cell_is_withheld_from_the_mean_but_still_counted(study: ModuleType) -> None:
    """Below MIN_CELL_N a Mean% cell prints `·`, while the year's `Sig` count still reports it.

    The tight gates (R>=70, R>=80) drop thin years to one or two names, where an average is that
    name's story. Suppression has to be one-sided: hiding the count as well would make a withheld
    cell indistinguishable from a year with no signals at all.
    """
    thin_n = study.MIN_CELL_N - 1
    thin = [{"year": 2018, "month": 1, "ret": 0.6, "ranking": 90}] * thin_n
    fat = [{"year": 2019, "month": 1, "ret": 0.1, "ranking": 90}] * study.MIN_CELL_N
    signals = [{"year": 2018, "ranking": 90}] * thin_n + [{"year": 2019, "ranking": 90}] * study.MIN_CELL_N

    text = "\n".join(study.build_tables(thin + fat, signals))
    thin_row = next(ln for ln in text.splitlines() if ln.strip().startswith("2018"))
    fat_row = next(ln for ln in text.splitlines() if ln.strip().startswith("2019"))

    assert "+60.0" not in thin_row, "a cell below the floor must not print a mean"
    assert "·" in thin_row
    # One-sided: the Sig column still reports the real count, so `·` is distinguishable from "none".
    assert thin_row.rstrip().endswith(str(thin_n))
    assert "+10.0" in fat_row, "a cell at the floor is reported normally"


def test_summary_carries_the_sample_size_beside_the_returns(study: ModuleType) -> None:
    """The gate comparison must show N and the thinnest years, not returns alone.

    A rising Mean% next to a collapsing sample is selectivity eating its own evidence. The table
    exists to make that visible, so the sample columns are part of its contract.
    """
    records = [{"year": 2020, "month": m, "ret": 0.02, "ranking": r} for m in range(1, 19) for r in (30, 90)]
    records += [{"year": 2018, "month": m, "ret": 0.02, "ranking": 30} for m in range(1, 19)]
    signals = [{"year": 2020, "ranking": 30}, {"year": 2020, "ranking": 90}, {"year": 2018, "ranking": 30}]

    table = study.build_summary(records, signals)
    assert "| Gate |" in table and "Signals" in table and "N@M18" in table and "Thinnest years" in table
    # The `|---|` separator does not match, so the filtered list is [header, *data rows].
    rows = [ln for ln in table.splitlines() if ln.startswith("| ")][1:]
    assert rows[0].startswith("| ungated |"), "loosest treatment leads, so tightening reads downward"
    assert "(live)" in table, "the live gate is marked"
    # The ungated row counts every signal; a tighter gate counts fewer.
    assert "| 3 |" in rows[0]


def test_a_series_that_ends_early_marks_none_from_that_month_on(study: ModuleType) -> None:
    """A delisted symbol contributes the months it covers and drops out of the rest."""
    entry = date(2021, 1, 15)
    dates, closes = _daily_series(entry, days=200, step=0.001)  # ~6.5 months of bars

    marks = study.monthly_marks(entry, 100.0, dates, closes)
    rets = study.marginal_returns(marks)

    assert marks[6] is not None
    assert marks[7] is None
    assert rets[5] is not None  # month 6 has both ends
    assert all(r is None for r in rets[6:])
