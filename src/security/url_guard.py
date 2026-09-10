"""SSRF guard: the single choke point for outbound HTTP URLs.

Any server-side fetch whose URL is built from configuration or request data
(provider templates, webhook URLs, entity lookups) must pass through
:func:`validate_public_http_url` (or :func:`guarded_urlopen` for urllib-based
fetchers) before the request leaves the process. The guard rejects:

- non-http(s) schemes (file:, gopher:, ftp:, ...)
- URLs embedding credentials (user:pass@host)
- hosts whose resolved addresses are not globally routable (loopback,
  RFC1918 private, link-local incl. cloud metadata 169.254.169.254,
  CGNAT 100.64/10, reserved, multicast, IPv4-mapped IPv6)

Development escape hatch: ``WAYPOINT_ALLOW_PRIVATE_URLS=1`` permits private
targets (local provider stubs, docker-compose backends). The override is
read on every call so tests can toggle it without reimporting.
"""

from __future__ import annotations

import ipaddress
import os
import socket
import urllib.request
from urllib.parse import urlsplit
from urllib.error import URLError

ALLOWED_SCHEMES = ("http", "https")
_PRIVATE_OVERRIDE_ENV = "WAYPOINT_ALLOW_PRIVATE_URLS"

# Hosts that are always allowed regardless of resolution (localhost dev stubs
# when the override is on, and literal-IP providers in tests).
_METADATA_HOSTS = {"169.254.169.254", "metadata.google.internal"}


class URLBlockedError(URLError):
    """Raised when a URL fails the SSRF guard."""

    def __init__(self, url: str, reason: str):
        self.url = url
        self.reason = reason
        super().__init__(f"URL blocked by SSRF guard ({reason}): {url}")


def _private_override_enabled() -> bool:
    return os.environ.get(_PRIVATE_OVERRIDE_ENV, "").strip() == "1"


def _is_public_address(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast:
        return False
    if ip.is_reserved or ip.is_unspecified:
        return False
    # CGNAT 100.64.0.0/10 is not flagged by ipaddress.is_private on all
    # versions; check explicitly.
    if isinstance(ip, ipaddress.IPv4Address) and ip in ipaddress.ip_network("100.64.0.0/10"):
        return False
    # IPv4-mapped IPv6 (::ffff:10.0.0.1) must be judged by the embedded v4.
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        return _is_public_address(ip.ipv4_mapped)
    return True


def validate_public_http_url(
    url: str,
    *,
    allow_private: bool | None = None,
) -> str:
    """Validate ``url`` for outbound fetch and return it unchanged.

    Raises :class:`URLBlockedError` when the URL must not be fetched. Pass
    ``allow_private=True`` for explicitly-internal probes (settings health
    checks) or leave ``None`` to honor ``WAYPOINT_ALLOW_PRIVATE_URLS``.
    """
    if not isinstance(url, str) or not url.strip():
        raise URLBlockedError(url or "", "empty URL")

    try:
        parts = urlsplit(url.strip())
    except ValueError as exc:
        raise URLBlockedError(url, f"unparseable URL: {exc}") from exc

    if parts.scheme.lower() not in ALLOWED_SCHEMES:
        raise URLBlockedError(url, f"scheme {parts.scheme!r} not allowed")

    if parts.username or parts.password:
        raise URLBlockedError(url, "credentials embedded in URL")

    hostname = parts.hostname
    if not hostname:
        raise URLBlockedError(url, "missing hostname")

    if hostname.lower() in _METADATA_HOSTS and not (
        allow_private if allow_private is not None else _private_override_enabled()
    ):
        raise URLBlockedError(url, "cloud metadata host")

    effective_allow_private = (
        allow_private if allow_private is not None else _private_override_enabled()
    )
    if effective_allow_private:
        return url.strip()

    try:
        # Deny trailing-dot / weird-name bypass by resolving the actual host.
        infos = socket.getaddrinfo(
            hostname.rstrip("."),
            parts.port or (443 if parts.scheme == "https" else 80),
            proto=socket.IPPROTO_TCP,
        )
    except socket.gaierror as exc:
        raise URLBlockedError(url, f"hostname does not resolve: {hostname}") from exc

    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr.split("%", 1)[0])
        except ValueError:
            raise URLBlockedError(url, f"unparseable resolved address {addr!r}")
        if not _is_public_address(ip):
            raise URLBlockedError(url, f"resolves to non-public address {ip}")

    return url.strip()


class _GuardedRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Re-validate every redirect target against the guard."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        validate_public_http_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def guarded_urlopen(
    url: str,
    *,
    timeout: float = 10.0,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    method: str | None = None,
    allow_private: bool | None = None,
):
    """Validate then open ``url`` with redirect re-validation attached."""
    validated = validate_public_http_url(url, allow_private=allow_private)
    request = urllib.request.Request(validated, data=data, headers=headers or {}, method=method)
    opener = urllib.request.build_opener(_GuardedRedirectHandler)
    return opener.open(request, timeout=timeout)
