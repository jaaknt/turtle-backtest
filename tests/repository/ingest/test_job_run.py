"""Tests for turtlex/repository/ingest/job_run.py JobRunRepository."""

from unittest.mock import MagicMock

from sqlalchemy.dialects import postgresql

from turtlex.repository.ingest import JobRunRepository


def _make_engine_mock(returned_id: int = 7) -> tuple[MagicMock, MagicMock]:
    """Mock an Engine whose insert RETURNING clause yields `returned_id`."""
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = returned_id
    mock_conn = MagicMock()
    mock_conn.execute.return_value = mock_result
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_engine = MagicMock()
    mock_engine.begin.return_value = mock_conn
    return mock_engine, mock_conn


def _compiled(conn: MagicMock) -> postgresql.dialect:
    return conn.execute.call_args.args[0].compile(dialect=postgresql.dialect())


class TestStartRun:
    def test_returns_the_generated_id(self) -> None:
        engine, _ = _make_engine_mock(returned_id=42)
        repo = JobRunRepository(engine)

        assert repo.start_run("signal-runner", {"cli": {}}, "1.0.0+abc1234", "host") == 42

    def test_insert_returns_the_id_column(self) -> None:
        engine, conn = _make_engine_mock()
        repo = JobRunRepository(engine)

        repo.start_run("signal-runner", {"cli": {}}, "1.0.0+abc1234", "host")

        assert "RETURNING turtle.job_runs.id" in str(_compiled(conn))

    def test_payload_omits_db_owned_columns(self) -> None:
        engine, conn = _make_engine_mock()
        repo = JobRunRepository(engine)

        repo.start_run("signal-runner", {"cli": {}}, "1.0.0+abc1234", "host")

        params = _compiled(conn).params
        # duration is generated and id is GENERATED ALWAYS AS IDENTITY: supplying either is an error
        assert "duration" not in params
        assert "id" not in params
        assert params["name"] == "signal-runner"
        assert params["version"] == "1.0.0+abc1234"
        assert params["hostname"] == "host"

    def test_status_and_start_at_come_from_column_defaults(self) -> None:
        engine, conn = _make_engine_mock()
        repo = JobRunRepository(engine)

        repo.start_run("signal-runner", {"cli": {}}, "1.0.0+abc1234", "host")

        params = _compiled(conn).params
        assert "status" not in params
        assert "start_at" not in params


class TestFinishRun:
    def test_targets_the_run_by_id(self) -> None:
        engine, conn = _make_engine_mock()
        repo = JobRunRepository(engine)

        repo.finish_run(42, "success", 0, None, {"cli": {}})

        compiled = _compiled(conn)
        assert "WHERE turtle.job_runs.id = " in str(compiled)
        assert 42 in compiled.params.values()

    def test_rewrites_parameters_so_late_sections_land(self) -> None:
        engine, conn = _make_engine_mock()
        repo = JobRunRepository(engine)
        parameters = {"cli": {"trading_strategy": "qullamaggie"}, "strategy": {"sma_thresh": 0.12}}

        repo.finish_run(42, "success", 0, None, parameters)

        assert _compiled(conn).params["parameters"] == parameters

    def test_sets_end_at_server_side_and_never_duration(self) -> None:
        engine, conn = _make_engine_mock()
        repo = JobRunRepository(engine)

        repo.finish_run(42, "failed", 1, "boom", {"cli": {}})

        compiled = _compiled(conn)
        # end_at comes from the server clock, so it cannot drift from the generated duration
        assert "CURRENT_TIMESTAMP" in str(compiled)
        assert "duration" not in compiled.params
        assert compiled.params["status"] == "failed"
        assert compiled.params["exit_code"] == 1
        assert compiled.params["error"] == "boom"
