"""Shared logic between the sync and async clients.

Keeps request construction, response decoding, error mapping and retry
decisions in one place so the two client classes stay thin and cannot drift
apart.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional, Type

import httpx

from .exceptions import (
    APIError,
    AuthenticationError,
    BlockedError,
    BrowserTimeoutError,
    CreditLimitExceededError,
    InvalidRequestError,
    NoSubscriptionError,
    NotFoundError,
    PaymentFailedError,
    PaymentRequiredError,
    QuotaExceededError,
    RateLimitError,
    ScrapeUnblockerError,
    ServerError,
    StepFailedError,
    UnsupportedContentError,
    UpstreamOutageError,
    ValidationError,
)

DEFAULT_BASE_URL = "https://api.scrapeunblocker.com"
DEFAULT_TIMEOUT = 180.0
DEFAULT_MAX_RETRIES = 2
API_KEY_HEADER = "x-scrapeunblocker-key"

# Status codes worth retrying: transient upstream outage, rate limiting, and
# generic 5xx. A 400/401/402/403 is deterministic - retrying only wastes time,
# and for 402 the block lifts on a billing change, not on another attempt.
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
        raise _auth_error_class(body)(message, status_code=status, body=body)
    if status == 402:
        raise _billing_error_class(body)(message, status_code=status, body=body)
    if status == 403:
        raise BlockedError(message, status_code=status, body=body)
    if status == 404:
        raise NotFoundError(message, status_code=status, body=body)
    if status == 408:
        raise BrowserTimeoutError(message, status_code=status, body=body)
    if status == 415:
        raise UnsupportedContentError(message, status_code=status, body=body)
    if status == 422:
        step_error = _step_failed_error(body)
        if step_error is not None:
            raise step_error
        raise ValidationError(message, status_code=status, body=body)
    if status == 429:
        raise RateLimitError(message, status_code=status, body=body)
    if status == 503:
        raise UpstreamOutageError(message, status_code=status, body=body)
    if status >= 500:
        raise ServerError(message, status_code=status, body=body)
    raise APIError(message, status_code=status, body=body)


def _step_failed_error(body: Optional[str]) -> Optional[StepFailedError]:
    """Build a :class:`StepFailedError` from a ``step_failed`` 422 body.

    A 422 raised by a ``steps`` run carries a JSON body of
    ``{"error": "step_failed", "step_index", "action", "reason", "selector",
    "html"}``. Anything else (a plain FastAPI validation error) returns None
    so the caller falls back to the general :class:`ValidationError`.
    """
    try:
        data = json.loads(body or "")
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict) or data.get("error") != "step_failed":
        return None
    index = data.get("step_index")
    action = data.get("action")
    reason = data.get("reason")
    message = f"Browser step {index} ({action}) failed: {reason}"
    return StepFailedError(
        message,
        status_code=422,
        body=body,
        step_index=index,
        action=action,
        reason=reason,
        selector=data.get("selector"),
        html=data.get("html"),
    )


def _auth_error_class(body: Optional[str]) -> Type[AuthenticationError]:
    """Pick the 401 subclass from the response body.

    A 401 is either an unknown key or a recognised key on an account without a
    plan. Only the body tells them apart; anything unrecognised stays on the
    general AuthenticationError.
    """
    if "no valid subscription" in (body or "").lower():
        return NoSubscriptionError
    return AuthenticationError


def _billing_error_class(body: Optional[str]) -> Type[PaymentRequiredError]:
    """Pick the 402 subclass from the response body.

    The three billing blocks share a status code and differ only in their
    plain-text body. An unrecognised body falls back to the general
    PaymentRequiredError rather than guessing.
    """
    text = (body or "").lower()
    if "quota exceeded" in text:
        return QuotaExceededError
    if "credit limit exceeded" in text:
        return CreditLimitExceededError
    if "payment failed" in text:
        return PaymentFailedError
    return PaymentRequiredError


def _message_for(status: int, body: Optional[str]) -> str:
    snippet = (body or "").strip().replace("\n", " ")
    if len(snippet) > 200:
        snippet = snippet[:200] + "..."
    base = {
        400: "Invalid request (bad URL, unsupported scheme, or missing API key header)",
        401: "Authentication failed - key not recognised, or account has no active plan",
        402: "Billing block - quota exceeded, credit limit exceeded, or a failed payment",
        403: "Target blocked by bot protection on every bypass path",
        404: "Requested element not found on the page",
        408: "Browser run timed out before the page was ready",
        415: "URL does not serve HTML",
        422: "Validation error - see the detail array in the response body",
        429: "Rate limited - too many requests",
        503: "Upstream origin returned a server-side outage page",
        504: "Fetch timed out upstream",
    }.get(status, f"API returned HTTP {status}")
    return f"{base}: {snippet}" if snippet else base


def decode_page_response(
    response: httpx.Response, *, want_json: bool
) -> Any:
    """Return parsed JSON when the caller asked for it, else the text body."""
    if want_json:
        return response.json()
    return response.text
