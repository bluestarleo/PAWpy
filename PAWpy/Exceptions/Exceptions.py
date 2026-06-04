"""Exception hierarchy for PAWpy.

Mirrors the spirit of TM1py's exception design: a single base exception
(`PAWException`) with specialised subclasses so callers can catch broadly or
narrowly. HTTP failures carry the status code, the request method/url, and the
(possibly truncated) response body to make debugging against a remote PAW
instance practical.
"""

from __future__ import annotations

from typing import Optional


class PAWException(Exception):
    """Base class for every error raised by PAWpy."""


class PAWConfigException(PAWException):
    """Raised when PAWpy is constructed with an invalid/incomplete configuration."""


class PAWAuthenticationException(PAWException):
    """Raised when login / token acquisition fails."""


class PAWTimeoutException(PAWException):
    """Raised when a request exceeds the configured timeout."""

    def __init__(self, method: str, url: str, timeout: float):
        self.method = method
        self.url = url
        self.timeout = timeout
        super().__init__(f"Request '{method} {url}' timed out after {timeout}s")


class PAWRestException(PAWException):
    """Raised when PAW returns a non-2xx HTTP status code."""

    def __init__(
        self,
        status_code: int,
        reason: str,
        method: str,
        url: str,
        response_body: Optional[str] = None,
    ):
        self.status_code = status_code
        self.reason = reason
        self.method = method
        self.url = url
        self.response_body = response_body
        body_preview = ""
        if response_body:
            body_preview = response_body if len(response_body) <= 2000 else response_body[:2000] + "…"
            body_preview = f"\nResponse body: {body_preview}"
        super().__init__(
            f"PAW REST request failed: {method} {url} -> {status_code} {reason}{body_preview}"
        )


class PAWNotFoundException(PAWRestException):
    """Raised on HTTP 404 — the requested asset/resource does not exist."""
