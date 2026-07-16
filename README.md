# ScrapeUnblocker Python client

Official Python client for the [ScrapeUnblocker](https://scrapeunblocker.com) web scraping API.

Every request is fully JavaScript-rendered in a real browser and routed through premium proxies, so it bypasses Cloudflare, DataDome, PerimeterX, Akamai, Kasada and similar anti-bot systems - from one simple call. You are only billed for successful requests.

- **Highest success rate on the market** (95%+ on live production traffic)
- **Rendered HTML or parsed JSON** - no per-site parsers to maintain
- Sync **and** async clients, fully type-hinted

## Install

```bash
pip install scrapeunblocker
```

Requires Python 3.8+.

## Quickstart

```python
from scrapeunblocker import Client

su = Client(api_key="YOUR_API_KEY")   # or set the SCRAPEUNBLOCKER_KEY env var

# Rendered HTML for any URL
html = su.get_page_source("https://example.com")

# Structured JSON instead of HTML (products, listings, search results, ...)
product = su.get_parsed("https://www.amazon.com/dp/B08N5WRWNW")
print(product.page_type)   # "product"
print(product.data)        # {...}
```

Get your API key at [app.scrapeunblocker.com](https://app.scrapeunblocker.com). The free trial does not require a credit card.

## Authentication

Pass the key directly, or set an environment variable and omit it:

```bash
export SCRAPEUNBLOCKER_KEY="YOUR_API_KEY"
```

```python
from scrapeunblocker import Client
su = Client()   # reads SCRAPEUNBLOCKER_KEY
```

## Fetch rendered HTML

```python
html = su.get_page_source(
    "https://www.nordstrom.com/browse/women/clothing/dresses",
    proxy_country="US",     # route through a specific country
    time_sleep=3,           # wait extra seconds after load
)
```

## Get parsed JSON

Pass a URL and get back structured data extracted via Schema.org, `__NEXT_DATA__` or AI-generated rules:

```python
result = su.get_parsed("https://www.walmart.com/ip/12345")
print(result.page_type)    # e.g. "product"
print(result.source)       # how it was extracted
print(result.data)         # the fields

# If a parse ever comes back wrong, force a fresh set of rules:
result = su.get_parsed(url, refresh_rules=True, rules_hint="price is missing")
```

## Google search (SERP)

```python
serp = su.serp("web scraping api", pages_to_check=2, proxy_country="US")
```

## Cookies and the serving proxy

```python
page = su.get_page_with_cookies("https://example.com")
print(page.html, page.cookies, page.proxy)
```

## Images

```python
data = su.get_image("https://example.com/photo.jpg")
open("photo.jpg", "wb").write(data)
```

## Skyscanner plugins

```python
# Resolve a place name to entity IDs, then search
locs = su.skyscanner.flight_locations("London")
flights = su.skyscanner.flights(
    origin="London", dest="New York",
    depart_date="2026-09-01", adults=1, currency="USD",
)

hotels = su.skyscanner.hotels(destination="Madrid", checkin="2026-09-01", checkout="2026-09-03")
cars = su.skyscanner.carhire(pickup="Madrid", pickup_datetime="2026-09-01T10:00", dropoff_datetime="2026-09-03T10:00")
```

## Async

Every method has an async twin on `AsyncClient`:

```python
import asyncio
from scrapeunblocker import AsyncClient

async def main():
    async with AsyncClient(api_key="YOUR_API_KEY") as su:
        html = await su.get_page_source("https://example.com")

asyncio.run(main())
```

## Error handling

Non-2xx responses raise typed exceptions, all subclasses of `ScrapeUnblockerError`:

```python
from scrapeunblocker import Client, BlockedError, RateLimitError, UpstreamOutageError

su = Client()
try:
    html = su.get_page_source("https://example.com")
except BlockedError:
    ...   # 403: the target blocked every bypass path (not billed)
except RateLimitError:
    ...   # 429: slow down
except UpstreamOutageError:
    ...   # 503: the target site itself is down - retry later
```

| Exception | Status | Meaning |
|---|---|---|
| `InvalidRequestError` | 400 | Bad URL or unsupported scheme |
| `AuthenticationError` | 401 | Missing or invalid API key |
| `BlockedError` | 403 | Blocked by bot protection on every path |
| `RateLimitError` | 429 | Too many requests |
| `UpstreamOutageError` | 503 | The target origin is down |
| `ServerError` | 5xx | Unexpected server error |
| `ScrapeTimeoutError` | - | Request exceeded the timeout |
| `ConnectionError` | - | Could not reach the API |

Transient failures (429, 502, 503, 504 and network errors) are retried automatically with exponential backoff; tune with `Client(max_retries=...)`.

## Configuration

```python
Client(
    api_key=None,          # or SCRAPEUNBLOCKER_KEY env var
    base_url="https://api.scrapeunblocker.com",
    timeout=180.0,         # seconds; protected pages can be slow
    max_retries=2,
)
```

## Links

- Documentation: https://developers.scrapeunblocker.com
- Website: https://scrapeunblocker.com
- Dashboard: https://app.scrapeunblocker.com

## License

MIT
