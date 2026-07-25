import logging
from collections.abc import Iterator

import pytest

from turtlex.config.logging import _THIRD_PARTY_LEVELS, ApiTokenFilter, setup_logging


def _make_record(msg: str, args: tuple = ()) -> logging.LogRecord:
    record = logging.LogRecord(
        name="httpx._client",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=msg,
        args=args,
        exc_info=None,
    )
    return record


@pytest.fixture
def restore_root_logger() -> Iterator[None]:
    """Snapshot and restore root handlers/level so setup_logging cannot leak into other tests."""
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    third_party = {name: logging.getLogger(name).level for name in _THIRD_PARTY_LEVELS}
    yield
    root.handlers[:] = handlers
    root.setLevel(level)
    for name, saved in third_party.items():
        logging.getLogger(name).setLevel(saved)


class TestApiTokenFilter:
    def setup_method(self) -> None:
        self.f = ApiTokenFilter()

    def test_redacts_token_in_msg(self) -> None:
        record = _make_record("GET https://example.com?api_token=secret123&fmt=json")
        self.f.filter(record)
        assert "secret123" not in record.msg
        assert "api_token=***" in record.msg

    def test_redacts_token_in_args(self) -> None:
        record = _make_record(
            "HTTP Request: %s %s",
            ("GET", "https://example.com?api_token=secret123&fmt=json"),
        )
        self.f.filter(record)
        assert isinstance(record.args, tuple)
        assert all("secret123" not in str(a) for a in record.args)
        assert any("api_token=***" in str(a) for a in record.args)

    def test_leaves_clean_msg_unchanged(self) -> None:
        record = _make_record("HTTP Request: GET https://example.com/api/data")
        self.f.filter(record)
        assert record.msg == "HTTP Request: GET https://example.com/api/data"

    def test_leaves_clean_args_unchanged(self) -> None:
        record = _make_record("HTTP Request: %s %s", ("GET", "https://example.com/api/data"))
        self.f.filter(record)
        assert record.args == ("GET", "https://example.com/api/data")

    def test_non_string_arg_without_token_preserved(self) -> None:
        record = _make_record("HTTP Request: %s %s %d", ("GET", "https://example.com", 200))
        self.f.filter(record)
        assert record.args[2] == 200

    def test_filter_always_returns_true(self) -> None:
        record = _make_record("some message")
        assert self.f.filter(record) is True

    def test_single_non_tuple_arg(self) -> None:
        record = _make_record("url: %s", "https://example.com?api_token=secret&x=1")  # type: ignore[arg-type]
        self.f.filter(record)
        assert isinstance(record.args, tuple)
        assert "secret" not in str(record.args[0])


@pytest.mark.usefixtures("restore_root_logger")
class TestSetupLogging:
    def test_installs_single_stdout_handler_with_redaction(self) -> None:
        setup_logging()

        root = logging.getLogger()
        assert len(root.handlers) == 1
        assert any(isinstance(f, ApiTokenFilter) for f in root.handlers[0].filters)

    def test_is_idempotent(self) -> None:
        setup_logging()
        setup_logging()

        assert len(logging.getLogger().handlers) == 1

    def test_replaces_preexisting_handlers(self) -> None:
        logging.getLogger().addHandler(logging.NullHandler())

        setup_logging()

        assert len(logging.getLogger().handlers) == 1

    def test_default_level_is_info(self) -> None:
        setup_logging()

        assert logging.getLogger().level == logging.INFO

    def test_verbose_sets_root_to_debug(self) -> None:
        setup_logging(verbose=True)

        assert logging.getLogger().level == logging.DEBUG

    def test_verbose_leaves_third_party_loggers_pinned(self) -> None:
        setup_logging(verbose=True)

        assert logging.getLogger("httpx").level == logging.WARNING
        assert logging.getLogger("sqlalchemy.engine").level == logging.WARNING
        assert logging.getLogger("matplotlib").level == logging.INFO
