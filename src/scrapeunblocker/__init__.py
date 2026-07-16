"""Official Python client for the ScrapeUnblocker web scraping API.

Basic usage::

    from scrapeunblocker import Client

    su = Client(api_key="YOUR_API_KEY")          # or set SCRAPEUNBLOCKER_KEY
    html = su.get_page_source("https://example.com")
    product = su.get_parsed("https://www.amazon.com/dp/B08N5WRWNW")

See https://developers.scrapeunblocker.com for the full API reference.
"""

from ._async_client import AsyncClient
from ._client import Client
from .exceptions import (
    APIError,
    AuthenticationError,
    BlockedError,
    ConnectionError,
    InvalidRequestError,
    RateLimitError,
    ScrapeTimeoutError,
    ScrapeUnblockerError,
    ServerError,
    UpstreamOutageError,
)
from .models import PageResult, ParsedPage
from .version import __version__

__all__ = [
    "Client",
    "AsyncClient",
    "ParsedPage",
    "PageResult",
    "ScrapeUnblockerError",
    "APIError",
    "AuthenticationError",
    "InvalidRequestError",
    "BlockedError",
    "RateLimitError",
    "UpstreamOutageError",
    "ServerError",
    "ScrapeTimeoutError",
    "ConnectionError",
    "__version__",
]
