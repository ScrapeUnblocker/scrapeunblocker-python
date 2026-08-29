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
    """The API key was rejected (HTTP 401).

    Two distinct cases produce a 401, both raised as this class (or the
    :class:`NoSubscriptionError` subclass for the second one):

    * ``Unauthorized`` - the key is not recognised. Usually a typo, a
      truncated copy-paste, trailing whitespace or a newline in the header
      value, an empty value, or a key that has been rotated in the dashboard.
    * ``No valid subscription`` - the key itself is fine, but the account
      behind it has no plan covering today.

    Omitting the API key entirely is a 400, not a 401, and is raised as
    :class:`InvalidRequestError`. Nothing is scraped for a 401, so it is not
    billed and does not count against your quota.
    """


class NoSubscriptionError(AuthenticationError):
    """The key is valid but the account has no active plan (HTTP 401).

    Raised when the API answers a 401 with ``No valid subscription``. Pick a
    plan at https://app.scrapeunblocker.com - access resumes within about a
    minute, and the key does not change.
    """


class PaymentRequiredError(APIError):
    """The account has a billing problem (HTTP 402).

    Your credentials are fine - the request was stopped for a billing reason.
    There are three of them, each raised as a dedicated subclass so you can
    react to them separately, or catch ``PaymentRequiredError`` for all three:

    * :class:`QuotaExceededError` - ``Quota exceeded``
    * :class:`CreditLimitExceededError` - ``Credit limit exceeded``
    * :class:`PaymentFailedError` - ``Payment failed - update payment method``

    When more than one applies, the most serious wins: failed payment
    outranks credit limit, which outranks quota. All three resolve
    themselves once the underlying billing state changes - access returns
    within roughly a minute, with no key change needed.

    Like a 401, a 402 is refused before anything is scraped, so it is never
    billed and consumes no quota. Retrying it is pointless; fix the billing
    state first.
    """


class QuotaExceededError(PaymentRequiredError):
    """Every request the plan allows this period has been used (HTTP 402).

    On plans that permit overages this only fires past the quota *plus* the
    overage allowance; inside that band requests still succeed and the extra
    usage is invoiced. Any active coupon credit is spent before plan quota.

    The counter resets at the start of the next billing period, which runs
    from the subscription's anniversary day, not the first of the month.
    Upgrade at https://app.scrapeunblocker.com to continue sooner.
    """


class CreditLimitExceededError(PaymentRequiredError):
    """The unpaid balance has passed the account's credit limit (HTTP 402).

    The balance counted here is the amount remaining on open invoices plus
    metered usage already consumed but not yet invoiced. Outstanding invoices
    are finalised and charged automatically when this triggers, so with a
    working card it usually clears itself within about a minute.
    """


class PaymentFailedError(PaymentRequiredError):
    """A card payment has been declined three times (HTTP 402).

    Those attempts are the payment provider's automatic retries spread over
    several days, so reaching this state means a card has been failing for a
    while - typically expired, cancelled, or short of funds.

    Subscribing to a new plan does **not** clear this: the old unpaid invoice
    stays open, and the block stays until that specific invoice is paid.
    Update the payment method at https://app.scrapeunblocker.com.
    """


class InvalidRequestError(APIError):
    """The request was rejected as invalid (HTTP 400).

    Raised for a malformed URL or unsupported scheme, for a missing
    ``x-scrapeunblocker-key`` header (``Missing x-scrapeunblocker-key``), and
    for a URL that belongs to a dedicated plugin - the response names the
    endpoint to use instead.
    """


class NotFoundError(APIError):
    """The page loaded but the requested element was absent (HTTP 404).

    Only ``get_image()`` raises this: the page rendered fine and contained no
    ``<img>`` tag.
    """


class BrowserTimeoutError(APIError):
    """The browser run did not finish in time on our side (HTTP 408).

    Distinct from :class:`ScrapeTimeoutError`, which is *this client* giving
    up locally. Here the API answered - it just could not render the page in
    the time allowed. Retrying usually helps.
    """


class UnsupportedContentError(APIError):
    """The URL serves something other than HTML (HTTP 415).

    The message names the content type that was found. For images, use
    ``get_image()`` instead of ``get_page_source()``.
    """


class ValidationError(APIError):
    """A request parameter is missing or has the wrong type (HTTP 422).

    Unlike the other errors, the body is JSON with a ``detail`` array that
    pinpoints each problem field::

        {"detail": [{"loc": ["query", "url"],
                     "msg": "field required",
                     "type": "value_error.missing"}]}

    Use :attr:`APIError.body` to read it.
    """


class StepFailedError(ValidationError):
    """A browser step in a ``steps`` sequence could not run (HTTP 422).

    Raised when the API executes the ordered ``steps`` you passed to
    ``get_page_source()`` and one of them fails - a selector never appears, a
    ``wait_for_text`` times out, and so on. The API answers 422 with a JSON
    body of ``{"error": "step_failed", ...}``, and this subclass surfaces its
    fields directly so you do not have to parse the body by hand:

    Attributes:
        step_index: Zero-based index of the step that failed.
        action: The action name of the failed step, e.g. ``"click"``.
        reason: Human-readable explanation of the failure.
        selector: The selector the step was acting on, if any.
        html: The page HTML captured at the moment the step failed, useful
            for working out why the selector was not there.

    It derives from :class:`ValidationError` (itself a 422), so existing
    ``except ValidationError`` handlers keep catching it.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        body: Optional[str] = None,
        step_index: Optional[int] = None,
        action: Optional[str] = None,
        reason: Optional[str] = None,
        selector: Optional[str] = None,
        html: Optional[str] = None,
    ):
        super().__init__(message, status_code=status_code, body=body)
        self.step_index = step_index
        self.action = action
        self.reason = reason
        self.selector = selector
        self.html = html


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
    """ScrapeUnblocker returned an unexpected 5xx error.

    Also covers the 504 returned when a SERP fetch times out; lowering
    ``pages_to_check`` or choosing a different ``proxy_country`` helps if it
    persists.
    """


class ScrapeTimeoutError(ScrapeUnblockerError):
    """The request did not complete within the configured timeout."""


class ConnectionError(ScrapeUnblockerError):
    """The client could not reach the ScrapeUnblocker API."""
