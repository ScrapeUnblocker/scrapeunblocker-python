"""Synchronous ScrapeUnblocker client."""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

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
        steps: Optional[List[Dict[str, Any]]] = None,
        list_elements: bool = False,
    ) -> Any:
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
            steps: An ordered list of browser-action dicts run in a real
                browser after the page loads, e.g.
                ``[{"action": "click", "selector": "#more"},
                {"action": "wait_for", "selector": ".results"}]``. Supported
                actions: ``wait_for`` (``selector``, ``selector_type?``,
                ``timeout_ms?``), ``wait_for_text`` (``value``, ``timeout_ms?``),
                ``wait`` (``value`` ms), ``click``, ``type`` (``value``,
                ``clear?``), ``select`` (``value``), ``press_key`` (``value``
                one of Enter/Tab/Escape/Backspace/Delete/Space/Arrow*/Home/End/
                PageUp/PageDown) and ``scroll`` (``value`` ``"bottom"`` or an
                int pixel amount). ``selector_type`` is one of ``css``
                (default), ``xPath``, ``className`` or ``tagName``. A request
                with steps runs once and is non-idempotent; if a step fails the
                API answers 422 and this method raises
                :class:`~scrapeunblocker.StepFailedError` carrying
                ``step_index``, ``action``, ``reason``, ``selector`` and
                ``html``.
            list_elements: When ``True`` the API returns a JSON dict
                (``{"url", "count", "elements": [...]}``) describing the
                interactive/labelled elements on the page instead of HTML -
                handy for discovering the selectors to drive ``steps``. The
                method then returns that parsed ``dict`` rather than a string.

        Returns:
            The page HTML as a string, or the parsed JSON ``dict`` when
            ``list_elements=True``.
        """
        params = _base.build_params(
            url=url,
            proxy_country=proxy_country,
            time_sleep=time_sleep,
            method=method,
            value=value,
            method_timeout=method_timeout,
            steps=json.dumps(steps) if steps is not None else None,
            list_elements=True if list_elements else None,
        )
        response = self._request("/getPageSource", params)
        if list_elements:
            return response.json()
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
            "/serpApi",
            keyword=keyword,
            proxy_country=proxy_country,
            pages_to_check=pages_to_check,
            wait_after_load=wait_after_load or None,
            captcha_pause=captcha_pause or None,
        )

    def google_local(
        self,
        keyword: str,
        *,
        proxy_country: Optional[str] = None,
        hl: Optional[str] = None,
        gl: Optional[str] = None,
    ) -> Any:
        """Search Google Local (Maps) and return the businesses as JSON.

        Returns up to ~20 businesses, each with name, rating, reviews, price,
        category, address, hours and a top review snippet.

        Args:
            keyword: The search phrase, e.g. "coffee shops in chicago".
            proxy_country: Exit-IP country (ISO-2). Local results are
                location-sensitive, so set the market you want.
            gl: Google country of search (ISO-2 lowercase, e.g. "us").
            hl: Google UI language (e.g. "en", "de").
        """
        return self._post_json(
            "/maps/google-local",
            keyword=keyword,
            proxy_country=proxy_country,
            hl=hl,
            gl=gl,
        )

    def oopbuy_search(
        self,
        keyword: str,
        *,
        channel: str = "1688",
        page: int = 1,
        page_size: int = 20,
        sort: str = "default",
        proxy_country: Optional[str] = None,
    ) -> Any:
        """Search Oopbuy goods and return the products as JSON.

        Returns products from the selected sourcing channel, each with SPU,
        title (English and Chinese), price, monthly sales, image and URL.

        Args:
            keyword: The search phrase, e.g. "wireless earbuds".
            channel: Sourcing channel: ``"1688"``, ``"taobao"`` or
                ``"official"``.
            page: Result page number (1-based).
            page_size: Products per page (max 60).
            sort: Ordering: ``"default"``, ``"price_asc"``, ``"price_desc"``
                or ``"best_selling"``.
            proxy_country: Exit-IP country (ISO-2).
        """
        return self._post_json(
            "/goods/oopbuy-search",
            keyword=keyword,
            channel=channel,
            page=page,
            page_size=page_size,
            sort=sort,
            proxy_country=proxy_country,
        )

    def ebay_search(
        self,
        keyword: str,
        *,
        marketplace: str = "ebay.com",
        page: int = 1,
        page_size: int = 60,
        condition: Optional[str] = None,
        sort: str = "best_match",
        listing_type: str = "all",
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        free_shipping: bool = False,
        seller: Optional[str] = None,
        category: Optional[str] = None,
        proxy_country: Optional[str] = None,
    ) -> Any:
        """Search eBay and return the listings as JSON.

        Each listing carries title, numeric price and currency, condition,
        seller username and feedback, shipping cost, sold/watcher/bid counts,
        image and a clean item URL.

        When eBay finds no exact match it still serves a page of loosely
        related suggestions; the response then sets ``exactMatches`` to
        ``False``, so check that field before using the listings.

        Args:
            keyword: The search phrase, e.g. "iphone 13".
            marketplace: Regional eBay site, e.g. ``"ebay.com"``, ``"ebay.de"``.
            page: Result page number (1-based).
            page_size: Listings per page: 60, 120 or 240.
            condition: ``"new"``, ``"open_box"``, ``"refurbished"``,
                ``"used"`` or ``"for_parts"``.
            sort: ``"best_match"``, ``"newly_listed"``, ``"ending_soon"``,
                ``"price_asc"`` or ``"price_desc"``.
            listing_type: ``"all"``, ``"buy_it_now"`` or ``"auction"``.
            min_price: Lowest price to include, in the marketplace's currency.
            max_price: Highest price to include, in the marketplace's currency.
            free_shipping: Keep only listings eBay marks as free delivery.
            seller: Restrict the search to one seller's username.
            category: eBay category id to search inside, e.g. ``"131090"``.
            proxy_country: Exit-IP country (ISO-2).
        """
        return self._post_json(
            "/marketplace/ebay-search",
            keyword=keyword,
            marketplace=marketplace,
            page=page,
            page_size=page_size,
            condition=condition,
            sort=sort,
            listing_type=listing_type,
            min_price=min_price,
            max_price=max_price,
            free_shipping=free_shipping or None,
            seller=seller,
            category=category,
            proxy_country=proxy_country,
        )

    def amazon_product(
        self,
        *,
        asin: Optional[str] = None,
        url: Optional[str] = None,
        marketplace: str = "amazon.com",
        proxy_country: Optional[str] = None,
    ) -> Any:
        """Scrape one Amazon product by ASIN or URL and return it as JSON.

        Returns title, brand, numeric price and currency, list price and
        savings, availability, rating, review count, seller, feature bullets,
        categories and images. Prices come back in the marketplace's own
        currency: ``proxy_country`` defaults to the marketplace's home country
        (amazon.com -> US) so the exit is pinned there over the ISP pool.

        Args:
            asin: 10-char product id, e.g. ``"B0BSHF7WHW"`` (books use their
                ISBN-10). Pair with ``marketplace``.
            url: Full product URL instead of ``asin``; the ASIN and marketplace
                are read from it.
            marketplace: Regional Amazon site, e.g. ``"amazon.com"``,
                ``"amazon.de"``.
            proxy_country: Exit-IP country (ISO-2). Defaults to the
                marketplace's home country.
        """
        return self._post_json(
            "/marketplace/amazon-product",
            asin=asin,
            url=url,
            marketplace=marketplace,
            proxy_country=proxy_country,
        )

    def amazon_search(
        self,
        keyword: str,
        *,
        marketplace: str = "amazon.com",
        page: int = 1,
        sort: str = "featured",
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        proxy_country: Optional[str] = None,
    ) -> Any:
        """Search Amazon and return the result cards as JSON.

        Each card carries asin, title, numeric price and currency, list price,
        rating, review count, a clean product URL, image and the sponsored /
        prime flags. Fetch a card's full detail with :meth:`amazon_product`.
        Prices are in the marketplace's own currency.

        Args:
            keyword: The search phrase, e.g. "wireless headphones".
            marketplace: Regional Amazon site, e.g. ``"amazon.com"``,
                ``"amazon.de"``.
            page: Result page number (1-based).
            sort: ``"featured"``, ``"price_asc"``, ``"price_desc"``,
                ``"avg_review"`` or ``"newest"``.
            min_price: Lowest price to include, in the marketplace's currency.
            max_price: Highest price to include, in the marketplace's currency.
            proxy_country: Exit-IP country (ISO-2). Defaults to the
                marketplace's home country.
        """
        return self._post_json(
            "/marketplace/amazon-search",
            keyword=keyword,
            marketplace=marketplace,
            page=page,
            sort=sort,
            min_price=min_price,
            max_price=max_price,
            proxy_country=proxy_country,
        )

    def get_image(
        self, url: str, *, proxy_country: Optional[str] = None
    ) -> bytes:
        """Fetch an image URL through the bypass chain and return its bytes."""
        params = _base.build_params(url=url, proxy_country=proxy_country)
        response = self._request("/getImage", params)
        return response.content
