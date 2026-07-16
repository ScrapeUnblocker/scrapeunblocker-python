"""Exception hierarchy for the ScrapeUnblocker client.

Every error raised by the client derives from :class:`ScrapeUnblockerError`,
so ``except ScrapeUnblockerError`` catches everything. API responses map to
typed subclasses by status code, letting callers react to a hard block
differently than a transient upstream outage without parsing status codes by
hand.
"""

from __future__ import annotations

from typing import Optional


class ScrapeUnblockerError(Exception):
    """Base class for every error raised by this library."""


class APIError(ScrapeUnblockerError):
    """An error response returned by the ScrapeUnblocker API.

    Attributes:
        status_code: The HTTP status code of the response.
        body: The raw response body (text), useful for debugging.
    """

    def __init__(self, message: str, *, status_code: int, body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class AuthenticationError(APIError):
    """The API key is missing, malformed, or not recognised (HTTP 401)."""


class InvalidRequestError(APIError):
    """The request was rejected as invalid, e.g. a malformed URL (HTTP 400)."""


class BlockedError(APIError):
    """The target site blocked every available bypass path (HTTP 403).

    This is the target's anti-bot protection winning, not a problem with your
    request. Blocked calls are not billed.
    """


class RateLimitError(APIError):
    """Too many requests against your account in a short window (HTTP 429)."""


class UpstreamOutageError(APIError):
    """The origin site returned a server-side outage page (HTTP 503).

    This means the *target* is down, not ScrapeUnblocker. Retrying later
    usually succeeds.
    """


class ServerError(APIError):
    """ScrapeUnblocker returned an unexpected 5xx error."""


class ScrapeTimeoutError(ScrapeUnblockerError):
    """The request did not complete within the configured timeout."""


class ConnectionError(ScrapeUnblockerError):
    """The client could not reach the ScrapeUnblocker API."""
