import json
import logging

from app.core.logging import JsonFormatter, setup_logging


def test_json_formatter_emits_parseable_line():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello world",
        args=(),
        exc_info=None,
    )

    payload = json.loads(formatter.format(record))

    assert "timestamp" in payload
    assert payload["level"] == "INFO"
    assert payload["message"] == "hello world"


def test_setup_logging_applies_json_formatter_to_root(capsys):
    setup_logging()
    logging.getLogger("activia-trace-test").info("structured event")

    captured = capsys.readouterr()
    line = captured.err.strip()
    payload = json.loads(line)

    assert payload["message"] == "structured event"
    assert payload["level"] == "INFO"
