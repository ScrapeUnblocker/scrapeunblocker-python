"""Asynchronous ScrapeUnblocker client (mirror of the sync client)."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

import httpx

from . import _base
from .exceptions import ConnectionError as SUConnectionError
from .exceptions import ScrapeTimeoutError
from .models import PageResult, ParsedPage
from .version import __version__


class _AsyncSkyscannerNamespace:
    """Skyscanner plugin endpoints (flights, hotels, car hire)."""

    def __init__(self, client: "AsyncClient"):
        self._c = client

    async def flight_locations(self, q: str, **params: Any) -> Any:
        return await self._c._post_json("/flights/skyscanner-locations", q=q, **params)

    async def flights(self, **params: Any) -> Any:
        return await self._c._post_json("/flights/skyscanner-quotes", **params)

    async def hotel_locations(self, q: str, **params: Any) -> Any:
        return await self._c._post_json("/hotels/skyscanner-locations", q=q, **params)

    async def hotels(self, **params: Any) -> Any:
        return await self._c._post_json("/hotels/skyscanner-quotes", **params)

    async def carhire_locations(self, q: str, **params: Any) -> Any:
        return await self._c._post_json("/carhire/skyscanner-locations", q=q, **params)

    async def carhire(self, **params: Any) -> Any:
        return await self._c._post_json("/carhire/skyscanner-quotes", **params)


class AsyncClient:
    """Async client for the ScrapeUnblocker API.

    Mirrors :class:`~scrapeunblocker.Client`; every method is a coroutine.

    Example:
        >>> import asyncio
        >>> from scrapeunblocker import AsyncClient
        >>> async def main():
        ...     async with AsyncClient(api_key="YOUR_API_KEY") as su:
        ...         html = await su.get_page_source("https://example.com")
        >>> asyncio.run(main())
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
        self._http = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers={
                _base.API_KEY_HEADER: self._api_key,
                "User-Agent": _base.user_agent(__version__),
                "Accept": "*/*",
            },
        )
        self.skyscanner = _AsyncSkyscannerNamespace(self)

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _request(self, path: str, params: Dict[str, Any]) -> httpx.Response:
        attempt = 0
        while True:
            try:
                response = await self._http.post(path, params=params)
            except httpx.TimeoutException as exc:
                raise ScrapeTimeoutError(str(exc)) from exc
            except httpx.TransportError as exc:
                if attempt < self._max_retries:
                    await self._sleep(attempt)
                    attempt += 1
                    continue
                raise SUConnectionError(str(exc)) from exc

            if _base.is_retryable(response.status_code) and attempt < self._max_retries:
                await self._sleep(attempt)
                attempt += 1
                continue

            _base.raise_for_status(response)
            return response

    @staticmethod
    async def _sleep(attempt: int) -> None:
        await asyncio.sleep(min(0.5 * (2 ** attempt), 8.0))

    async def _post_json(self, path: str, **params: Any) -> Any:
        response = await self._request(path, _base.build_params(**params))
        return response.json()

    async def get_page_source(
        self,
        url: str,
        *,
        proxy_country: Optional[str] = None,
        time_sleep: Optional[int] = None,
        method: Optional[str] = None,
        value: Optional[str] = None,
        method_timeout: Optional[int] = None,
    ) -> str:
        """Fetch a URL and return the fully rendered HTML."""
        params = _base.build_params(
            url=url,
            proxy_country=proxy_country,
            time_sleep=time_sleep,
            method=method,
            value=value,
            method_timeout=method_timeout,
        )
        response = await self._request("/getPageSource", params)
        return response.text

    async def get_parsed(
        self,
        url: str,
        *,
        refresh_rules: bool = False,
        rules_hint: Optional[str] = None,
        proxy_country: Optional[str] = None,
        time_sleep: Optional[int] = None,
    ) -> ParsedPage:
        """Fetch a URL and return structured JSON instead of HTML."""
        params = _base.build_params(
            url=url,
            parsed_data=True,
            refresh_rules=refresh_rules or None,
            rules_hint=rules_hint,
            proxy_country=proxy_country,
            time_sleep=time_sleep,
        )
        response = await self._request("/getPageSource", params)
        return ParsedPage.from_response(response.json())

    async def get_page_with_cookies(
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
        response = await self._request("/getPageSource", params)
        return PageResult.from_response(response.json())

    async def serp(
        self,
        keyword: str,
        *,
        proxy_country: Optional[str] = None,
        pages_to_check: int = 1,
        wait_after_load: int = 0,
        captcha_pause: int = 0,
    ) -> Any:
        """Run a Google search and return the parsed SERP as JSON."""
        return await self._post_json(
            "/serpApi",
            keyword=keyword,
            proxy_country=proxy_country,
            pages_to_check=pages_to_check,
            wait_after_load=wait_after_load or None,
            captcha_pause=captcha_pause or None,
        )

    async def google_local(
        self,
        keyword: str,
        *,
        proxy_country: Optional[str] = None,
        hl: Optional[str] = None,
        gl: Optional[str] = None,
    ) -> Any:
        """Search Google Local (Maps) and return the businesses as JSON."""
        return await self._post_json(
            "/maps/google-local",
            keyword=keyword,
            proxy_country=proxy_country,
            hl=hl,
            gl=gl,
        )

    async def oopbuy_search(
        self,
        keyword: str,
        *,
        channel: str = "1688",
        page: int = 1,
        page_size: int = 20,
        sort: str = "default",
        proxy_country: Optional[str] = None,
    ) -> Any:
        """Search Oopbuy goods and return the products as JSON."""
        return await self._post_json(
            "/goods/oopbuy-search",
            keyword=keyword,
            channel=channel,
            page=page,
            page_size=page_size,
            sort=sort,
            proxy_country=proxy_country,
        )

    async def ebay_search(
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
        """Search eBay and return the listings as JSON."""
        return await self._post_json(
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

    async def amazon_product(
        self,
        *,
        asin: Optional[str] = None,
        url: Optional[str] = None,
        marketplace: str = "amazon.com",
        proxy_country: Optional[str] = None,
    ) -> Any:
        """Scrape one Amazon product by ASIN or URL and return it as JSON.

        Prices come back in the marketplace's own currency: ``proxy_country``
        defaults to the marketplace's home country (amazon.com -> US). Pass
        either ``asin`` (with ``marketplace``) or a full product ``url``.
        """
        return await self._post_json(
            "/marketplace/amazon-product",
            asin=asin,
            url=url,
            marketplace=marketplace,
            proxy_country=proxy_country,
        )

    async def amazon_search(
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

        Each card carries asin, title, price and currency, list price, rating,
        review count, a clean product URL, image and the sponsored / prime
        flags. ``sort`` is one of ``"featured"``, ``"price_asc"``,
        ``"price_desc"``, ``"avg_review"`` or ``"newest"``.
        """
        return await self._post_json(
            "/marketplace/amazon-search",
            keyword=keyword,
            marketplace=marketplace,
            page=page,
            sort=sort,
            min_price=min_price,
            max_price=max_price,
            proxy_country=proxy_country,
        )

    async def get_image(
        self, url: str, *, proxy_country: Optional[str] = None
    ) -> bytes:
        """Fetch an image URL through the bypass chain and return its bytes."""
        params = _base.build_params(url=url, proxy_country=proxy_country)
        response = await self._request("/getImage", params)
        return response.content
