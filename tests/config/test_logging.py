import logging
import re
from collections.abc import Iterator

import pytest

from turtlex.config.logging import _THIRD_PARTY_LEVELS, ApiTokenFilter, LastErrorCapture, setup_logging

# Trailing UTC offset on the timestamp, e.g. the "+0300" in 2026-07-26T12:28:51+0300
_UTC_OFFSET = r"\d{2}:\d{2}:\d{2}[+-]\d{4}"


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

    def test_default_format_omits_call_site_and_utc_offset(self) -> None:
        setup_logging()

        formatted = logging.getLogger().handlers[0].format(_make_record("hello"))

        assert formatted.startswith("[INFO] ")
        assert formatted.endswith(": hello")
        assert "|" not in formatted
        assert re.search(_UTC_OFFSET, formatted) is None

    def test_verbose_format_keeps_call_site_and_utc_offset(self) -> None:
        setup_logging(verbose=True)

        formatted = logging.getLogger().handlers[0].format(_make_record("hello"))

        assert formatted.startswith("[INFO|")
        assert "|L0]" in formatted
        assert formatted.endswith(": hello")
        assert re.search(_UTC_OFFSET, formatted) is not None

    def test_verbose_leaves_third_party_loggers_pinned(self) -> None:
        setup_logging(verbose=True)

        assert logging.getLogger("httpx").level == logging.WARNING
        assert logging.getLogger("sqlalchemy.engine").level == logging.WARNING
        assert logging.getLogger("matplotlib").level == logging.INFO


class TestLastErrorCapture:
    @pytest.fixture
    def capture(self) -> Iterator[LastErrorCapture]:
        setup_logging(verbose=False)
        handler = LastErrorCapture()
        handler.attach()
        yield handler
        handler.detach()

    def test_captures_the_last_error(self, capture: LastErrorCapture) -> None:
        logging.getLogger("turtlex.x").error("first")
        logging.getLogger("turtlex.y").error("second")

        assert capture.last_message == "second"

    def test_ignores_records_below_error(self, capture: LastErrorCapture) -> None:
        # The recorder's own failures log at WARNING; they must not poison the error column
        logging.getLogger("turtlex.x").warning("just a warning")
        logging.getLogger("turtlex.x").info("just info")

        assert capture.last_message is None

    def test_interpolates_percent_style_args(self, capture: LastErrorCapture) -> None:
        logging.getLogger("turtlex.x").error("Folder does not exist: %s", "/tmp/nope")

        assert capture.last_message == "Folder does not exist: /tmp/nope"

    def test_appends_the_exception_text(self, capture: LastErrorCapture) -> None:
        # logger.exception puts the cause in exc_info, so without this a --verbose run would
        # record the bare string "Full error details:" instead of the failure
        try:
            raise RuntimeError("real cause")
        except RuntimeError:
            logging.getLogger("turtlex.x").exception("Full error details:")

        assert capture.last_message == "Full error details: real cause"

    def test_a_malformed_record_does_not_propagate(self) -> None:
        # Handler.handle() does not guard emit(); every concrete handler guards its own body.
        # Without that guard this TypeError escapes the logger.error() call site and kills the
        # job the handler exists to measure. Driven through emit() directly rather than through
        # the root logger, because pytest's own capture handler re-raises in handleError.
        handler = LastErrorCapture()
        record = logging.LogRecord(
            name="turtlex.x", level=logging.ERROR, pathname="", lineno=0, msg="%s %s", args=("only-one-arg",), exc_info=None
        )

        handler.emit(record)  # must not raise

        assert handler.last_message is None

    def test_redacts_api_token(self, capture: LastErrorCapture) -> None:
        # What this handler captures is persisted to the database, not a rotating journal
        logging.getLogger("turtlex.x").error("failed: https://eodhd.com/api?api_token=SECRET&fmt=json")

        assert capture.last_message is not None
        assert "SECRET" not in capture.last_message
        assert "api_token=***" in capture.last_message

    def test_detach_is_safe_when_not_attached(self) -> None:
        LastErrorCapture().detach()
