"""The bulk research signal layer must answer an empty window with an empty *frame*, not a shape.

Studies walk fixed windows and can legitimately land on one the data does not cover — a cache
chunk before the universe existed, a holdout run started early. When that happened, the whole
chain returned column-less frames, and the failure surfaced several steps later as
`ColumnNotFoundError` on whatever column the study filtered on first. These tests pin the
contract each docstring states: the columns do not depend on whether there are rows.
"""

from datetime import date, timedelta
from unittest.mock import MagicMock

import polars as pl

from turtlex.repository.query.daily_bars import UNIVERSE_BARS_SCHEMA
from turtlex.research import qullamaggie as research

START = date(2020, 1, 1)


def _universe_frame(n: int) -> pl.DataFrame:
    """`n` bars for one symbol, in the shape `get_qualified_universe_bars_pl` returns."""
    return pl.DataFrame(
        {
            "symbol": ["T.US"] * n,
            "date": [START + timedelta(days=i) for i in range(n)],
            "open": [100.0] * n,
            "high": [101.0] * n,
            "low": [99.0] * n,
            "close": [100.0] * n,
            "adjusted_close": [100.0] * n,
            "volume": [1_000_000] * n,
        },
        schema=UNIVERSE_BARS_SCHEMA,
    )


def _chain(frame: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Walk one universe frame through the whole research path, as every study does."""
    bars = research.prepare_bars(frame.rename({"close": "raw_close"}))
    indicators = research.add_indicators(bars)
    signals = research.get_signals(indicators, set(bars["date"].to_list()), START, sma_thresh=0.12)
    return bars, indicators, research.resolve_entries(signals, bars)


def test_empty_window_keeps_the_columns_a_populated_one_has() -> None:
    """The empty and populated paths must not disagree about the schema.

    Compared against a real run rather than a hardcoded list, so a column added to
    `add_indicators` cannot pass here while going missing on the empty path.
    """
    full_bars, full_indicators, full_entries = _chain(_universe_frame(340))
    empty_bars, empty_indicators, empty_entries = _chain(_universe_frame(0))

    assert not full_bars.is_empty(), "the populated arm must actually survive prepare_bars"
    assert empty_bars.is_empty()
    assert empty_bars.columns == full_bars.columns
    assert empty_indicators.columns == full_indicators.columns
    assert empty_entries.columns == full_entries.columns


def test_empty_entries_can_be_filtered_on_date() -> None:
    """The concrete failure: a study filtering entries by date raised instead of returning none."""
    _, _, entries = _chain(_universe_frame(0))

    assert entries.filter(pl.col("date") >= START).is_empty()


def test_load_bars_returns_the_documented_columns_for_an_uncovered_window() -> None:
    """`load_bars` promises adj_* columns; a window with no bars is not an exemption."""
    repo = MagicMock()
    repo.get_qualified_universe_bars_pl.return_value = pl.DataFrame(schema=UNIVERSE_BARS_SCHEMA)

    result = research.load_bars(repo, START, START + timedelta(days=30))

    assert result.is_empty()
    for column in ("symbol", "date", "raw_close", "adj_open", "adj_close", "adj_high", "adj_low", "volume"):
        assert column in result.columns
