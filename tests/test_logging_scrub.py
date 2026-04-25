import logging

from spine_api.core.logging_filter import SensitiveDataFilter, install_sensitive_data_filter


def _capture_log(msg: str) -> str:
    logger = logging.getLogger("test.scrub")
    logger.setLevel(logging.DEBUG)
    handler = logging.handlers = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    records: list[str] = []

    class Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(self.format(record))

    cap = Capture()
    cap.setFormatter(logging.Formatter("%(message)s"))
    filt = SensitiveDataFilter()
    cap.addFilter(filt)
    logger.addHandler(cap)
    logger.handlers = [cap]

    logger.info(msg)
    return records[0] if records else ""


def test_scrubs_access_token_value():
    result = _capture_log("user logged in access_token=eyJhbGciOiJIUzI1NiJ9.payload.sig")
    assert "eyJhbGciOiJIUzI1NiJ9" not in result
    assert "[REDACTED]" in result


def test_scrubs_authorization_header():
    result = _capture_log("Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig")
    assert "eyJhbGciOiJIUzI1NiJ9" not in result
    assert "[REDACTED]" in result


def test_scrubs_cookie_header():
    result = _capture_log("Cookie: access_token=secret123; theme=dark")
    assert "secret123" not in result
    assert "[REDACTED]" in result


def test_scrubs_set_cookie():
    result = _capture_log("Set-Cookie: access_token=secretval; HttpOnly; Path=/")
    assert "secretval" not in result
    assert "[REDACTED]" in result


def test_preserves_non_sensitive():
    result = _capture_log("User john@example.com logged in successfully")
    assert result == "User john@example.com logged in successfully"


def test_install_adds_filter_to_root():
    root = logging.getLogger()
    install_sensitive_data_filter()
    assert any(isinstance(f, SensitiveDataFilter) for f in root.filters)


def test_install_idempotent():
    root = logging.getLogger()
    before = sum(1 for f in root.filters if isinstance(f, SensitiveDataFilter))
    install_sensitive_data_filter()
    install_sensitive_data_filter()
    after = sum(1 for f in root.filters if isinstance(f, SensitiveDataFilter))
    assert after == before or after == 1
