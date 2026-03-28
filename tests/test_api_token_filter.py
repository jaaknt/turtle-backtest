import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.download_eodhd_data import _ApiTokenFilter


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


class TestApiTokenFilter:
    def setup_method(self) -> None:
        self.f = _ApiTokenFilter()

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
