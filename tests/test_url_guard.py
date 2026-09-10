"""Unit tests for the SSRF URL guard and the filesystem path guard.

Mimosa remediation wave (2026-09-10): these guards are the canonical choke
points for outbound HTTP (src.security.url_guard) and file-backed store paths
(src.security.path_guard). Every producer surface routes through them.
"""

import ipaddress
from unittest.mock import patch

import pytest

from src.security.url_guard import (
    URLBlockedError,
    _is_public_address,
    validate_public_http_url,
)
from src.security.path_guard import UnsafePathError, safe_join, validate_filename


# ---------------------------------------------------------------------------
# URL guard — pure validation logic (no network)
# ---------------------------------------------------------------------------


class TestSchemeAndShape:
    def test_rejects_non_http_schemes(self):
        for url in (
            "file:///etc/passwd",
            "gopher://internal/x",
            "ftp://example.com/f",
            "dict://localhost:11211/",
        ):
            with pytest.raises(URLBlockedError):
                validate_public_http_url(url)

    def test_rejects_embedded_credentials(self):
        with pytest.raises(URLBlockedError, match="credentials"):
            validate_public_http_url("http://user:pass@example.com/x")

    def test_rejects_missing_hostname(self):
        with pytest.raises(URLBlockedError):
            validate_public_http_url("http:///path-only")

    def test_rejects_empty_url(self):
        with pytest.raises(URLBlockedError):
            validate_public_http_url("")


class TestAddressResolution:
    """Hostname resolution is mocked — no network in unit tests."""

    def test_public_hostname_passes(self):
        with patch("src.security.url_guard.socket.getaddrinfo") as mock_gai:
            mock_gai.return_value = [(None, None, None, "", ("93.184.216.34", 443))]
            assert (
                validate_public_http_url("https://example.com/path?q=1")
                == "https://example.com/path?q=1"
            )

    def test_loopback_resolution_blocked(self):
        with patch("src.security.url_guard.socket.getaddrinfo") as mock_gai:
            mock_gai.return_value = [(None, None, None, "", ("127.0.0.1", 80))]
            with pytest.raises(URLBlockedError, match="non-public"):
                validate_public_http_url("http://localhost/admin")

    def test_rfc1918_resolution_blocked(self):
        with patch("src.security.url_guard.socket.getaddrinfo") as mock_gai:
            mock_gai.return_value = [(None, None, None, "", ("192.168.1.10", 80))]
            with pytest.raises(URLBlockedError):
                validate_public_http_url("http://intranet.corp/")

    def test_cloud_metadata_host_blocked_by_name(self):
        with pytest.raises(URLBlockedError, match="metadata"):
            validate_public_http_url("http://169.254.169.254/latest/meta-data/")

    def test_ipv6_mapped_v4_blocked(self):
        assert not _is_public_address(ipaddress.ip_address("::ffff:10.0.0.1"))

    def test_cgnat_range_blocked(self):
        assert not _is_public_address(ipaddress.ip_address("100.64.0.7"))

    def test_public_addresses_pass(self):
        assert _is_public_address(ipaddress.ip_address("93.184.216.34"))
        assert _is_public_address(ipaddress.ip_address("2606:2800:220:1:248:1893:25c8:1946"))


class TestPrivateOverride:
    def test_override_env_permits_private(self, monkeypatch):
        monkeypatch.setenv("WAYPOINT_ALLOW_PRIVATE_URLS", "1")
        with patch("src.security.url_guard.socket.getaddrinfo") as mock_gai:
            mock_gai.return_value = [(None, None, None, "", ("10.0.0.5", 80))]
            assert validate_public_http_url("http://internal.local:8080/x") == (
                "http://internal.local:8080/x"
            )

    def test_explicit_allow_private_argument(self):
        with patch("src.security.url_guard.socket.getaddrinfo") as mock_gai:
            mock_gai.return_value = [(None, None, None, "", ("127.0.0.1", 80))]
            assert validate_public_http_url(
                "http://127.0.0.1:8000/health", allow_private=True
            ) == "http://127.0.0.1:8000/health"

    def test_override_off_still_blocks(self, monkeypatch):
        monkeypatch.setenv("WAYPOINT_ALLOW_PRIVATE_URLS", "0")
        with patch("src.security.url_guard.socket.getaddrinfo") as mock_gai:
            mock_gai.return_value = [(None, None, None, "", ("10.0.0.5", 80))]
            with pytest.raises(URLBlockedError):
                validate_public_http_url("http://internal.local/")


# ---------------------------------------------------------------------------
# Path guard
# ---------------------------------------------------------------------------


class TestSafeJoin:
    def test_plain_name_stays_inside_base(self, tmp_path):
        result = safe_join(tmp_path, "trip_123.json")
        assert result.parent == tmp_path
        assert result.name == "trip_123.json"

    def test_traversal_rejected(self, tmp_path):
        with pytest.raises(UnsafePathError):
            safe_join(tmp_path, "..", "escape.txt")
        with pytest.raises(UnsafePathError):
            safe_join(tmp_path, "../escape.txt")

    def test_absolute_and_separator_parts_rejected(self, tmp_path):
        with pytest.raises(UnsafePathError):
            safe_join(tmp_path, "/etc/passwd")
        with pytest.raises(UnsafePathError):
            safe_join(tmp_path, "sub/dir/file.json")
        with pytest.raises(UnsafePathError):
            safe_join(tmp_path, "back\\slash.json")
        with pytest.raises(UnsafePathError):
            safe_join(tmp_path, "")

    def test_symlink_escape_rejected(self, tmp_path):
        (tmp_path / "real.txt").write_text("x")
        link = tmp_path / "link.json"
        link.symlink_to(tmp_path / "real.txt")
        # The link itself resolves inside base, so it passes containment but
        # a link pointing OUTSIDE must fail:
        outside_dir = tmp_path.parent / "outside_dir_guard"
        outside_dir.mkdir(exist_ok=True)
        (outside_dir / "secret.txt").write_text("s")
        bad_link = tmp_path / "bad.json"
        bad_link.symlink_to(outside_dir / "secret.txt")
        with pytest.raises(UnsafePathError):
            safe_join(tmp_path, "bad.json")


class TestValidateFilename:
    def test_accepts_plain_names(self):
        assert validate_filename("trip_abc.json") == "trip_abc.json"

    def test_rejects_traversal_and_separators(self):
        for bad in ("..", ".", "../x", "a/b", "a\\b", "", "/abs"):
            with pytest.raises(UnsafePathError):
                validate_filename(bad)
