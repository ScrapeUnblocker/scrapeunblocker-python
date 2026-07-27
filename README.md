# ScrapeUnblocker Python client

Official Python client for the [ScrapeUnblocker](https://scrapeunblocker.com?utm_source=pypi&utm_medium=integration&utm_campaign=python-sdk) web scraping API.

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

Get your API key at [app.scrapeunblocker.com](https://app.scrapeunblocker.com?utm_source=pypi&utm_medium=integration&utm_campaign=python-sdk). The free trial does not require a credit card.

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

## Google Local (Maps)

```python
# Local business listings for a search and market
local = su.google_local("coffee shops in chicago", proxy_country="US", gl="us")
for biz in local["results"]:
    print(biz["name"], biz["rating"], biz["reviews"], biz["address"])
```

## Oopbuy product search

```python
# Search Oopbuy sourcing channels (1688, Taobao, official)
goods = su.oopbuy_search("wireless earbuds", channel="1688", sort="best_selling")
for item in goods["results"]:
    print(item["title"], item["price"], item["monthSold"], item["url"])
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
from scrapeunblocker import (
    Client,
    BlockedError,
    PaymentRequiredError,
    RateLimitError,
    UpstreamOutageError,
)

su = Client()
try:
    html = su.get_page_source("https://example.com")
except BlockedError:
    ...   # 403: the target blocked every bypass path (not billed)
except PaymentRequiredError:
    ...   # 402: quota, credit limit, or a failed payment - fix billing
except RateLimitError:
    ...   # 429: slow down
except UpstreamOutageError:
    ...   # 503: the target site itself is down - retry later
```

| Exception | Status | Meaning |
|---|---|---|
| `InvalidRequestError` | 400 | Bad URL, unsupported scheme, or the API key header was not sent |
| `AuthenticationError` | 401 | Key not recognised - typo, stray whitespace, or a rotated key |
| `NoSubscriptionError` | 401 | Key is fine, but the account has no active plan |
| `PaymentRequiredError` | 402 | Billing block - base class for the three below |
| `QuotaExceededError` | 402 | The plan's requests for this period are used up |
| `CreditLimitExceededError` | 402 | Unpaid balance is past the account's credit limit |
| `PaymentFailedError` | 402 | A card payment was declined three times |
| `BlockedError` | 403 | Blocked by bot protection on every path |
| `NotFoundError` | 404 | Page loaded but held no image (`get_image` only) |
| `BrowserTimeoutError` | 408 | Our browser run timed out before the page was ready |
| `UnsupportedContentError` | 415 | The URL serves something other than HTML |
| `ValidationError` | 422 | Missing or wrong-typed parameter; `body` holds the `detail` array |
| `RateLimitError` | 429 | Too many requests |
| `UpstreamOutageError` | 503 | The target origin is down |
| `ServerError` | 5xx | Unexpected server error, including a 504 upstream timeout |
| `ScrapeTimeoutError` | - | This client gave up locally before the API answered |
| `ConnectionError` | - | Could not reach the API |

Every one of these subclasses `ScrapeUnblockerError`, so a single `except ScrapeUnblockerError` still catches everything, and the 402 and 401 subclasses can be caught by their base class when you do not need to tell them apart.

Transient failures (429, 502, 503, 504 and network errors) are retried automatically with exponential backoff; tune with `Client(max_retries=...)`. A 401 or 402 is never retried - it clears when the key or the billing state changes, not on another attempt. Neither is billed or counted against your quota, because the request is refused before anything is scraped.

### Billing errors (402)

The three billing blocks share a status code and differ only in their message, so the client raises a dedicated exception for each:

```python
from scrapeunblocker import (
    Client,
    CreditLimitExceededError,
    PaymentFailedError,
    QuotaExceededError,
)

su = Client()
try:
    html = su.get_page_source("https://example.com")
except QuotaExceededError:
    ...   # plan quota (plus any overage allowance) is used up for this period
except CreditLimitExceededError:
    ...   # unpaid balance passed the account credit limit
except PaymentFailedError:
    ...   # card declined three times - update the payment method
```

When more than one applies, the most serious wins: failed payment outranks credit limit, which outranks quota. All three lift by themselves once the billing state changes - access returns within about a minute, and the API key stays the same. One catch worth knowing: subscribing to a new plan does **not** clear `PaymentFailedError`, because the old unpaid invoice stays open until it is paid.

Full details for every status code: [developers.scrapeunblocker.com/errors](https://developers.scrapeunblocker.com/errors).

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

- Documentation: [developers.scrapeunblocker.com](https://developers.scrapeunblocker.com?utm_source=pypi&utm_medium=integration&utm_campaign=python-sdk)
- Website: [scrapeunblocker.com](https://scrapeunblocker.com?utm_source=pypi&utm_medium=integration&utm_campaign=python-sdk)
- Dashboard: [app.scrapeunblocker.com](https://app.scrapeunblocker.com?utm_source=pypi&utm_medium=integration&utm_campaign=python-sdk)

## License

MIT
