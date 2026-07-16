"""Shared logic between the sync and async clients.

Keeps request construction, response decoding, error mapping and retry
decisions in one place so the two client classes stay thin and cannot drift
apart.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx

from .exceptions import (
    APIError,
    AuthenticationError,
    BlockedError,
    InvalidRequestError,
    RateLimitError,
    ScrapeUnblockerError,
    ServerError,
    UpstreamOutageError,
)

DEFAULT_BASE_URL = "https://api.scrapeunblocker.com"
DEFAULT_TIMEOUT = 180.0
DEFAULT_MAX_RETRIES = 2
API_KEY_HEADER = "x-scrapeunblocker-key"

# Status codes worth retrying: transient upstream outage, rate limiting, and
# generic 5xx. A 400/403 is deterministic - retrying only wastes time.
_RETRYABLE_STATUS = frozenset({429, 502, 503, 504})


def resolve_api_key(api_key: Optional[str]) -> str:
    """Return the API key, falling back to the SCRAPEUNBLOCKER_KEY env var."""
    key = api_key or os.environ.get("SCRAPEUNBLOCKER_KEY")
    if not key:
        raise ScrapeUnblockerError(
            "No API key provided. Pass api_key=... or set the "
            "SCRAPEUNBLOCKER_KEY environment variable. Get your key at "
            "https://app.scrapeunblocker.com"
        )
    return key


def build_params(**kwargs: Any) -> Dict[str, Any]:
    """Drop None values so optional params are simply omitted from the query."""
    return {k: v for k, v in kwargs.items() if v is not None}


def user_agent(version: str) -> str:
    return f"scrapeunblocker-python/{version}"


def is_retryable(status_code: int) -> bool:
    return status_code in _RETRYABLE_STATUS


def raise_for_status(response: httpx.Response) -> None:
    """Map a non-2xx response to the matching typed exception."""
    if response.is_success:
        return

    status = response.status_code
    try:
        body = response.text
    except Exception:  # pragma: no cover - defensive
        body = None

    message = _message_for(status, body)

    if status == 400:
        raise InvalidRequestError(message, status_code=status, body=body)
    if status == 401:
        raise AuthenticationError(message, status_code=status, body=body)
    if status == 403:
        raise BlockedError(message, status_code=status, body=body)
    if status == 429:
        raise RateLimitError(message, status_code=status, body=body)
    if status == 503:
        raise UpstreamOutageError(message, status_code=status, body=body)
    if status >= 500:
        raise ServerError(message, status_code=status, body=body)
    raise APIError(message, status_code=status, body=body)


def _message_for(status: int, body: Optional[str]) -> str:
    snippet = (body or "").strip().replace("\n", " ")
    if len(snippet) > 200:
        snippet = snippet[:200] + "..."
    base = {
        400: "Invalid request (bad URL or unsupported scheme)",
        401: "Authentication failed - check your API key",
        403: "Target blocked by bot protection on every bypass path",
        429: "Rate limited - too many requests",
        503: "Upstream origin returned a server-side outage page",
    }.get(status, f"API returned HTTP {status}")
    return f"{base}: {snippet}" if snippet else base


def decode_page_response(
    response: httpx.Response, *, want_json: bool
) -> Any:
    """Return parsed JSON when the caller asked for it, else the text body."""
    if want_json:
        return response.json()
    return response.text
