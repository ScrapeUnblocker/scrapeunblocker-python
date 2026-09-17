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

## Browser steps

Drive the page in a real browser after it loads - click, type, wait for content, scroll - then capture the result. Pass an ordered list of action dicts; they run in sequence:

```python
html = su.get_page_source(
    "https://example.com/search",
    steps=[
        {"action": "type", "selector": "#q", "value": "wireless earbuds", "clear": True},
        {"action": "press_key", "value": "Enter"},
        {"action": "wait_for", "selector": ".results"},
        {"action": "scroll", "value": "bottom"},
    ],
)
```

Supported actions: `wait_for` (`selector`, `selector_type?`, `timeout_ms?`), `wait_for_text` (`value`, `timeout_ms?`), `wait` (`value` ms), `click`, `type` (`value`, `clear?` - human-like typing), `select` (`value`), `press_key` (`value` one of Enter, Tab, Escape, Backspace, Delete, Space, ArrowUp/Down/Left/Right, Home, End, PageUp, PageDown) and `scroll` (`value` = `"bottom"` or an int pixel amount). `selector_type` is one of `css` (default), `xPath`, `className` or `tagName`.

A request with `steps` runs once and is non-idempotent. If a step fails (a selector never appears, a `wait_for_text` times out), the call raises `StepFailedError` with the details:

```python
from scrapeunblocker import StepFailedError

try:
    su.get_page_source(url, steps=[{"action": "click", "selector": "#missing"}])
except StepFailedError as e:
    print(e.step_index, e.action, e.reason, e.selector)
    print(e.html)   # page HTML captured at the moment the step failed
```

`StepFailedError` subclasses `ValidationError` (HTTP 422), so `except ValidationError` still catches it.

## List elements

Ask the API to return the page's interactive/labelled elements as JSON instead of HTML - handy for discovering the selectors to feed into `steps`:

```python
result = su.get_page_source("https://example.com", list_elements=True)
print(result["count"])
for el in result["elements"]:
    print(el["tag"], el["selector"], el.get("text"), el.get("aria_label"))
```

With `list_elements=True` the method returns a `dict` (`{"url", "count", "elements": [...]}`) rather than an HTML string.

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

## Google Images

```python
# Image results for a keyword and market
images = su.google_images("golden retriever puppy", proxy_country="US", gl="us")
for img in images["results"]:
    print(img["imageUrl"], img["sourceDomain"], img["title"])
```

## Meta Ad Library

```python
# Ads an advertiser is running in the Meta/Facebook Ad Library
ads = su.meta_ad_library("Nike", country="US")
for ad in ads["results"]:
    print(ad["ad_text"], ad["cta_text"], ad["display_format"], ad["is_active"])
    print("  link:", ad["link_url"], "platforms:", ad["platforms"])
```

## Oopbuy product search

```python
# Search Oopbuy sourcing channels (1688, Taobao, official)
goods = su.oopbuy_search("wireless earbuds", channel="1688", sort="best_selling")
for item in goods["results"]:
    print(item["title"], item["price"], item["monthSold"], item["url"])
```

## eBay search

```python
# Listings from any regional eBay marketplace
items = su.ebay_search("iphone 13", marketplace="ebay.com", condition="used")
if items["exactMatches"]:
    for item in items["results"]:
        print(item["title"], item["price"], item["currency"], item["condition"])
        print("  seller:", item["seller"]["username"], item["seller"]["feedbackPercent"])
```

### TikTok

```python
profile = su.tiktok_profile("nasa", max_videos=5)      # exact stats + newest videos
print(profile["stats"]["followers"], profile["videos"][0]["stats"]["plays"])

video = su.tiktok_video("https://www.tiktok.com/@nasa/video/7665075736742530317", include_transcript=True)
print(video["stats"], video["music"]["title"], video["transcript"])

tag = su.tiktok_hashtag("nasa", max_videos=10)
print(tag["stats"]["views"], len(tag["videos"]))

results = su.tiktok_search("space telescope", max_results=25)   # TikTok's own ranking
comments = su.tiktok_comments("https://www.tiktok.com/@nasa/video/7665075736742530317", max_comments=40)
```

Profiles and hashtags list up to 10 videos in a couple of seconds from TikTok's server-rendered widget; ask for more (up to 200) and the real grid is scrolled in a browser session.

## Amazon

```python
# One product by ASIN (or url="https://www.amazon.de/dp/B0BSHF7WHW")
product = su.amazon_product(asin="B0BSHF7WHW", marketplace="amazon.com")
print(product["title"], product["price"], product["currency"], product["rating"])

# Keyword search - prices come back in the marketplace's currency
results = su.amazon_search("wireless headphones", sort="price_asc")
for item in results["results"]:
    print(item["title"], item["price"], item["currency"], item["asin"])
```

Prices are returned in the marketplace's own currency: `proxy_country` defaults
to the marketplace's home country (`amazon.com` -> US, `amazon.de` -> DE), so
you do not have to configure the exit yourself.

## eBay: exact matches

`exactMatches` is `False` when eBay found nothing for the keyword and returned
its own loosely-related suggestions instead, so check it before using the
listings.

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

## Southwest plugin

Southwest fares are not sold through the usual aggregators, so this queries
Southwest's own booking API directly and returns its raw JSON. Airports are
IATA codes; omit `return_date` for a one-way search.

```python
# Round-trip, priced in dollars
flights = su.southwest.flights(
    origin="DAL", dest="HOU",
    depart_date="2026-10-20", return_date="2026-10-27",
)

# One-way, priced in Rapid Rewards points
one_way = su.southwest.flights(
    origin="DAL", dest="HOU",
    depart_date="2026-10-20", adults=2, fare_type="points",
)
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
| `StepFailedError` | 422 | A browser `steps` action failed; carries `step_index`, `action`, `reason`, `selector`, `html` (subclass of `ValidationError`) |
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

Full details for every status code: [docs.scrapeunblocker.com/errors](https://docs.scrapeunblocker.com/errors).

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

- Documentation: [docs.scrapeunblocker.com](https://docs.scrapeunblocker.com?utm_source=pypi&utm_medium=integration&utm_campaign=python-sdk)
- Website: [scrapeunblocker.com](https://scrapeunblocker.com?utm_source=pypi&utm_medium=integration&utm_campaign=python-sdk)
- Dashboard: [app.scrapeunblocker.com](https://app.scrapeunblocker.com?utm_source=pypi&utm_medium=integration&utm_campaign=python-sdk)

## License

MIT
