"""Tests for turtlex/repository/ingest/signal.py SignalRepository."""

import re
from datetime import date
from unittest.mock import MagicMock

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.compiler import SQLCompiler

from turtlex.model import Signal
from turtlex.repository.ingest import SignalRepository
from turtlex.repository.ingest.signal import _parameters

SIGNAL_DATE = date(2026, 6, 1)
INDICATORS = {
    "pct_vs_sma50": 0.3084,
    "adr_pct": 0.0542,
    "adr_pct_change": 0.83,
    "vol_dry_up_ratio": 0.62,
    "rsi14": 50.5,
    "tight_range_ratio": 0.074,
    "roc_252d": 0.002,
}


def _make_engine_mock() -> tuple[MagicMock, MagicMock]:
    """Mock an Engine whose begin() yields a context-manager connection."""
    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_engine = MagicMock()
    mock_engine.begin.return_value = mock_conn
    return mock_engine, mock_conn


def _signal(ticker: str = "FA.US", signal_close: float | None = 17.07, next_open: float | None = 16.67) -> Signal:
    return Signal(
        ticker=ticker,
        date=SIGNAL_DATE,
        ranking=75,
        signal_close=signal_close,
        next_open=next_open,
        indicators=dict(INDICATORS),
    )


def _compiled(conn: MagicMock) -> SQLCompiler:
    """The insert statement the repository handed to the connection, compiled for PostgreSQL."""
    compiled: SQLCompiler = conn.execute.call_args.args[0].compile(dialect=postgresql.dialect())
    return compiled


def test_upsert_signals_empty_list_never_touches_the_engine() -> None:
    engine, _ = _make_engine_mock()
    assert SignalRepository(engine).upsert_signals([], trading_strategy="bk50d_s12_v2.0", ranking_strategy="qullamaggie") == 0
    engine.begin.assert_not_called()


def test_upsert_signals_returns_the_input_length() -> None:
    engine, _ = _make_engine_mock()
    repo = SignalRepository(engine)
    assert (
        repo.upsert_signals([_signal("FA.US"), _signal("RNG.US")], trading_strategy="bk50d_s12_v2.0", ranking_strategy="qullamaggie") == 2
    )


def test_upsert_signals_conflicts_on_the_natural_key_not_the_surrogate() -> None:
    engine, conn = _make_engine_mock()
    SignalRepository(engine).upsert_signals([_signal()], trading_strategy="bk50d_s12_v2.0", ranking_strategy="qullamaggie")

    assert "ON CONFLICT (trading_strategy, symbol, signal_date) DO UPDATE" in str(_compiled(conn))


def test_upsert_signals_updates_every_mutable_column() -> None:
    """Omitting ranking_strategy leaves the row naming the wrong scheme; omitting parameters
    freezes next_open out of the payload forever. Both pass every other assertion here.
    parameters is merged rather than assigned -- see the dedicated test below."""
    engine, conn = _make_engine_mock()
    SignalRepository(engine).upsert_signals([_signal()], trading_strategy="bk50d_s12_v2.0", ranking_strategy="qullamaggie")

    update_clause = str(_compiled(conn)).split("DO UPDATE SET", 1)[1]
    for column in ("ranking_strategy", "ranking", "signal_close"):
        assert f"{column} = excluded.{column}" in update_clause
    assert "parameters = " in update_clause


def test_upsert_signals_stores_each_signals_own_values() -> None:
    """Every row-level value, across two rows -- the column mapping and the per-row loop at once."""
    engine, conn = _make_engine_mock()
    second = Signal(ticker="RNG.US", date=date(2026, 6, 2), ranking=44, signal_close=9.5, next_open=None, indicators={"adr_pct": 0.09})
    SignalRepository(engine).upsert_signals([_signal(), second], trading_strategy="bk50d_s12_v2.0", ranking_strategy="qullamaggie")

    params = _compiled(conn).params
    assert params["symbol_m0"] == "FA.US"
    assert params["signal_date_m0"] == SIGNAL_DATE
    assert params["ranking_m0"] == 75
    assert params["signal_close_m0"] == 17.07  # the close, never next_open
    assert params["parameters_m0"] == {**INDICATORS, "next_open": 16.67}  # a dict, not a JSON string
    # the second row carries its own values, and its own missing next_open
    assert params["symbol_m1"] == "RNG.US"
    assert params["signal_date_m1"] == date(2026, 6, 2)
    assert params["ranking_m1"] == 44
    assert params["signal_close_m1"] == 9.5
    assert params["parameters_m1"] == {"adr_pct": 0.09}


def test_upsert_signals_carries_next_open_over_but_nothing_else() -> None:
    """A narrower --end-date drops next_open from the payload; a plain assignment would then delete
    a value an earlier wider run had backfilled. A blanket `existing || incoming` would fix that but
    also strand every indicator the current run stopped reporting, so only next_open is carried."""
    engine, conn = _make_engine_mock()
    SignalRepository(engine).upsert_signals([_signal()], trading_strategy="bk50d_s12_v2.0", ranking_strategy="qullamaggie")

    update_clause = str(_compiled(conn)).split("DO UPDATE SET", 1)[1]
    # incoming first: it stays authoritative for every key it carries, so a retired one is dropped
    assert "parameters = jsonb_strip_nulls(excluded.parameters || jsonb_build_object(" in update_clause
    # ... except next_open, which falls back to the stored value
    assert "coalesce(excluded.parameters[" in update_clause
    assert "turtle.signal.parameters[" in update_clause
    # a blanket merge would put the stored payload on the left; that is the shape being ruled out
    assert "jsonb_strip_nulls(turtle.signal.parameters ||" not in update_clause


def test_upsert_signals_payload_omits_db_owned_columns() -> None:
    engine, conn = _make_engine_mock()
    SignalRepository(engine).upsert_signals([_signal()], trading_strategy="bk50d_s12_v2.0", ranking_strategy="qullamaggie")

    # only the VALUES binds, which SQLAlchemy suffixes `_m<row>`; the ON CONFLICT expression
    # contributes its own params (jsonb_build_object_1, parameters_1) that are not insert columns
    inserted = {m.group(1) for m in (re.fullmatch(r"(.+)_m\d+", key) for key in _compiled(conn).params) if m}
    assert inserted == {"trading_strategy", "ranking_strategy", "symbol", "signal_date", "ranking", "signal_close", "parameters"}
    assert not inserted & {"id", "created_at", "modified_at"}


def test_upsert_signals_labels_come_from_the_arguments() -> None:
    engine, conn = _make_engine_mock()
    SignalRepository(engine).upsert_signals([_signal()], trading_strategy="bk50d_s16_v2.0", ranking_strategy="momentum")

    params = _compiled(conn).params
    assert params["trading_strategy_m0"] == "bk50d_s16_v2.0"
    assert params["ranking_strategy_m0"] == "momentum"


def test_upsert_signals_rejects_a_signal_without_a_close() -> None:
    engine, _ = _make_engine_mock()
    repo = SignalRepository(engine)

    with pytest.raises(ValueError, match="carry no signal_close"):
        repo.upsert_signals([_signal(), _signal("MARS.US", signal_close=None)], trading_strategy="mars", ranking_strategy="momentum")

    engine.begin.assert_not_called()


def test_parameters_carries_the_indicators_and_next_open_but_not_the_close() -> None:
    params = _parameters(_signal())

    assert params == {**INDICATORS, "next_open": 16.67}
    assert "signal_close" not in params  # no reported indicator is named for it; it has a column


def test_parameters_omits_next_open_on_the_newest_bar() -> None:
    params = _parameters(_signal(next_open=None))

    assert params == INDICATORS
    assert "next_open" not in params  # absent, never null


def test_parameters_does_not_mutate_the_signal() -> None:
    signal = _signal()
    _parameters(signal)

    assert signal.indicators == INDICATORS  # the dict() copy is load-bearing


def test_parameters_is_empty_for_a_strategy_that_reports_nothing() -> None:
    bare = Signal(ticker="AA.US", date=SIGNAL_DATE, ranking=50, signal_close=12.0)

    assert _parameters(bare) == {}
