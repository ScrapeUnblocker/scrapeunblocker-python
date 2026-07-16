"""Synchronous ScrapeUnblocker client."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

import httpx

from . import _base
from .exceptions import ConnectionError as SUConnectionError
from .exceptions import ScrapeTimeoutError
from .models import PageResult, ParsedPage
from .version import __version__


class _SkyscannerNamespace:
    """Skyscanner plugin endpoints (flights, hotels, car hire)."""

    def __init__(self, client: "Client"):
        self._c = client

    def flight_locations(self, q: str, **params: Any) -> Any:
        return self._c._post_json("/flights/skyscanner-locations", q=q, **params)

    def flights(self, **params: Any) -> Any:
        return self._c._post_json("/flights/skyscanner-quotes", **params)

    def hotel_locations(self, q: str, **params: Any) -> Any:
        return self._c._post_json("/hotels/skyscanner-locations", q=q, **params)

    def hotels(self, **params: Any) -> Any:
        return self._c._post_json("/hotels/skyscanner-quotes", **params)

    def carhire_locations(self, q: str, **params: Any) -> Any:
        return self._c._post_json("/carhire/skyscanner-locations", q=q, **params)

    def carhire(self, **params: Any) -> Any:
        return self._c._post_json("/carhire/skyscanner-quotes", **params)


class Client:
    """Client for the ScrapeUnblocker API.

    Args:
        api_key: Your API key. Falls back to the ``SCRAPEUNBLOCKER_KEY``
            environment variable when omitted.
        base_url: Override the API host (rarely needed).
        timeout: Per-request timeout in seconds. Rendering heavy, protected
            pages can take a while, so the default is generous (180s).
        max_retries: How many times to retry transient failures (429/5xx and
            network errors) with exponential backoff.

    Example:
        >>> from scrapeunblocker import Client
        >>> su = Client(api_key="YOUR_API_KEY")
        >>> html = su.get_page_source("https://example.com")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = _base.DEFAULT_BASE_URL,
        timeout: float = _base.DEFAULT_TIMEOUT,
        max_retries: int = _base.DEFAULT_MAX_RETRIES,
    ):
        self._api_key = _base.resolve_api_key(api_key)
        self._max_retries = max_retries
        self._http = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers={
                _base.API_KEY_HEADER: self._api_key,
                "User-Agent": _base.user_agent(__version__),
                "Accept": "*/*",
            },
        )
        self.skyscanner = _SkyscannerNamespace(self)

    # -- context manager ------------------------------------------------
    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()

    # -- low-level request with retry -----------------------------------
    def _request(self, path: str, params: Dict[str, Any]) -> httpx.Response:
        attempt = 0
        while True:
            try:
                response = self._http.post(path, params=params)
            except httpx.TimeoutException as exc:
                raise ScrapeTimeoutError(str(exc)) from exc
            except httpx.TransportError as exc:
                if attempt < self._max_retries:
                    self._sleep(attempt)
                    attempt += 1
                    continue
                raise SUConnectionError(str(exc)) from exc

            if _base.is_retryable(response.status_code) and attempt < self._max_retries:
                self._sleep(attempt)
                attempt += 1
                continue

            _base.raise_for_status(response)
            return response

    @staticmethod
    def _sleep(attempt: int) -> None:
        time.sleep(min(0.5 * (2 ** attempt), 8.0))

    def _post_json(self, path: str, **params: Any) -> Any:
        response = self._request(path, _base.build_params(**params))
        return response.json()

    # -- public API -----------------------------------------------------
    def get_page_source(
        self,
        url: str,
        *,
        proxy_country: Optional[str] = None,
        time_sleep: Optional[int] = None,
        method: Optional[str] = None,
        value: Optional[str] = None,
        method_timeout: Optional[int] = None,
    ) -> str:
        """Fetch a URL and return the fully rendered HTML.

        The page is loaded in a real browser behind the appropriate anti-bot
        bypass chain, so JavaScript-heavy and protected sites come back
        rendered.

        Args:
            url: The page to fetch.
            proxy_country: ISO country code to route through (e.g. ``"US"``).
            time_sleep: Extra seconds to wait after load before capture.
            method: Advanced render-wait method (``"css"``, ``"js"``, ...).
            value: The selector/expression paired with ``method``.
            method_timeout: Cap in seconds for the render-wait method.

        Returns:
            The page HTML as a string.
        """
        params = _base.build_params(
            url=url,
            proxy_country=proxy_country,
            time_sleep=time_sleep,
            method=method,
            value=value,
            method_timeout=method_timeout,
        )
        response = self._request("/getPageSource", params)
        return response.text

    def get_parsed(
        self,
        url: str,
        *,
        refresh_rules: bool = False,
        rules_hint: Optional[str] = None,
        proxy_country: Optional[str] = None,
        time_sleep: Optional[int] = None,
    ) -> ParsedPage:
        """Fetch a URL and return structured JSON instead of HTML.

        The API extracts fields using Schema.org, ``__NEXT_DATA__`` or
        AI-generated rules - no per-site parser to maintain.

        Args:
            url: The page to parse.
            refresh_rules: Force-regenerate the cached extraction rules for
                this domain (use when a parse comes back clearly wrong).
            rules_hint: Free-text steer for regeneration, e.g. ``"price is
                missing"``.
            proxy_country: ISO country code to route through.
            time_sleep: Extra seconds to wait after load before capture.

        Returns:
            A :class:`ParsedPage` with ``page_type``, ``source`` and ``data``.
        """
        params = _base.build_params(
            url=url,
            parsed_data=True,
            refresh_rules=refresh_rules or None,
            rules_hint=rules_hint,
            proxy_country=proxy_country,
            time_sleep=time_sleep,
        )
        response = self._request("/getPageSource", params)
        return ParsedPage.from_response(response.json())

    def get_page_with_cookies(
        self,
        url: str,
        *,
        proxy_country: Optional[str] = None,
        time_sleep: Optional[int] = None,
    ) -> PageResult:
        """Fetch a URL and also return the cookies and proxy that served it."""
        params = _base.build_params(
            url=url,
            get_cookies=True,
            proxy_country=proxy_country,
            time_sleep=time_sleep,
        )
        response = self._request("/getPageSource", params)
        return PageResult.from_response(response.json())

    def serp(
        self,
        keyword: str,
        *,
        proxy_country: Optional[str] = None,
        pages_to_check: int = 1,
        wait_after_load: int = 0,
        captcha_pause: int = 0,
    ) -> Any:
        """Run a Google search and return the parsed SERP as JSON.

        Args:
            keyword: The search query.
            proxy_country: ISO country code to search from.
            pages_to_check: How many result pages to fetch (1-10).
            wait_after_load: Seconds to wait after the page loads.
            captcha_pause: Seconds to pause if a captcha appears.
        """
        return self._post_json(
            "/serp",
            keyword=keyword,
            proxy_country=proxy_country,
            pages_to_check=pages_to_check,
            wait_after_load=wait_after_load or None,
            captcha_pause=captcha_pause or None,
        )

    def get_image(
        self, url: str, *, proxy_country: Optional[str] = None
    ) -> bytes:
        """Fetch an image URL through the bypass chain and return its bytes."""
        params = _base.build_params(url=url, proxy_country=proxy_country)
        response = self._request("/getImage", params)
        return response.content
