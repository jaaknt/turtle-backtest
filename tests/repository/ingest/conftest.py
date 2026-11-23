"""Shared fixtures for the ingest repository tests."""

from collections.abc import Callable
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.compiler import SQLCompiler
from sqlalchemy.sql.dml import UpdateBase


def _compile_executed(conn: MagicMock) -> SQLCompiler:
    statement: UpdateBase = conn.execute.call_args.args[0]
    compiled = statement.compile(dialect=postgresql.dialect())  # type: ignore[no-untyped-call]  # dialect constructors are unannotated
    # compile() is typed as the Compiled base, whose params may be None; a DML statement always
    # compiles to an SQLCompiler, whose params are a dict
    assert isinstance(compiled, SQLCompiler)
    return compiled


@pytest.fixture
def compile_statement() -> Callable[[MagicMock], SQLCompiler]:
    """Compile, for PostgreSQL, the insert or update a repository last handed to a mocked connection."""
    return _compile_executed


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def session() -> AsyncMock:
    s = AsyncMock()
    s.execute = AsyncMock()
    s.commit = AsyncMock()
    return s
