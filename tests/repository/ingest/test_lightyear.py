"""Tests for turtlex/repository/ingest/lightyear.py LightyearRepository."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

from sqlalchemy.dialects import postgresql

from turtlex.model import LightyearTransaction
from turtlex.repository.ingest import LightyearRepository


def _make_engine_mock(returned: int) -> tuple[MagicMock, MagicMock]:
    """Mock an Engine whose insert RETURNING clause yields `returned` rows."""
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [MagicMock() for _ in range(returned)]
    # rowcount is deliberately unusable: the real driver reports -1 here, and reading it
    # instead of the RETURNING rows is the regression this guards against.
    mock_result.rowcount = -1
    mock_conn = MagicMock()
    mock_conn.execute.return_value = mock_result
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_engine = MagicMock()
    mock_engine.begin.return_value = mock_conn
    return mock_engine, mock_conn


def _transaction(reference: str = "OR-AAA", ticker_code: str = "DUOL.US") -> LightyearTransaction:
    return LightyearTransaction(
        reference=reference,
        transacted_at=datetime(2026, 7, 30, 14, 5, 3),
        ticker_code=ticker_code,
        isin="US26603R1068",
        transaction_type="buy",
        quantity=Decimal("8.000000000"),
        currency="USD",
        price=Decimal("131.500000000"),
        gross_amount=Decimal("1053.00"),
        fee=Decimal("1.00"),
        tax=Decimal("0"),
        net_amount=Decimal("1052.00"),
        source_file="statement.csv",
    )


def test_insert_transactions_empty_returns_zero() -> None:
    engine, conn = _make_engine_mock(0)
    repo = LightyearRepository(engine)
    assert repo.insert_transactions([]) == 0
    engine.begin.assert_not_called()
    conn.execute.assert_not_called()


def test_insert_transactions_counts_returned_rows() -> None:
    engine, conn = _make_engine_mock(2)
    repo = LightyearRepository(engine)
    assert repo.insert_transactions([_transaction("OR-AAA"), _transaction("OR-BBB")]) == 2
    conn.execute.assert_called_once()


def test_insert_transactions_skipped_conflicts_are_not_counted() -> None:
    # Two rows sent, one already stored: ON CONFLICT DO NOTHING returns only the new one
    engine, _ = _make_engine_mock(1)
    repo = LightyearRepository(engine)
    assert repo.insert_transactions([_transaction("OR-AAA"), _transaction("OR-BBB")]) == 1


def test_insert_transactions_uses_on_conflict_do_nothing_with_returning() -> None:
    engine, conn = _make_engine_mock(1)
    repo = LightyearRepository(engine)
    repo.insert_transactions([_transaction()])

    compiled = str(conn.execute.call_args.args[0].compile(dialect=postgresql.dialect()))
    assert "ON CONFLICT (reference) DO NOTHING" in compiled
    assert "RETURNING turtle.lightyear_transaction.reference" in compiled


def test_insert_transactions_payload_omits_db_owned_timestamps() -> None:
    engine, conn = _make_engine_mock(1)
    repo = LightyearRepository(engine)
    repo.insert_transactions([_transaction()])

    compiled = conn.execute.call_args.args[0].compile(dialect=postgresql.dialect())
    inserted = {c.name for c in compiled.statement.table.columns} & {key.rsplit("_m0", 1)[0] for key in compiled.params}
    assert "created_at" not in inserted
    assert "modified_at" not in inserted
    assert compiled.params["reference_m0"] == "OR-AAA"
    assert compiled.params["transaction_type_m0"] == "buy"
    assert compiled.params["quantity_m0"] == Decimal("8.000000000")
