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

## Markdown for LLMs

Get the rendered page as clean Markdown instead of HTML, ready for an LLM prompt, an agent or a RAG pipeline. Headings, lists, tables, absolute links and images with their alt text are kept; scripts, styles, navigation, footers and forms are dropped. Billed like an HTML call.

```python
md = su.get_markdown("https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html")
print(md)   # "# A Light in the Attic\n\n£51.77\n..."

# Only the main content by default (no navigation, site header, footer or sidebars).
# Pass main_content_only=False to convert the whole page:
full = su.get_markdown("https://example.com", main_content_only=False)
```

`get_markdown()` takes the same `proxy_country`, `time_sleep`, `method` / `value` / `method_timeout` and `steps` options as `get_page_source()`. More in the [Markdown guide](https://docs.scrapeunblocker.com/guides/markdown?utm_source=pypi&utm_medium=integration&utm_campaign=python-sdk).

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
print(result.data)         # the fields

# If a parse ever comes back wrong, force a fresh set of rules:
result = su.get_parsed(url, refresh_rules=True, rules_hint="price is missing")
```

## Plugins

Ready-made scrapers for specific sites that return structured JSON. Each
method takes the plugin's main input positionally and everything else as
keyword options; options you leave out are not sent, so the API's own
defaults apply. Every parameter is documented on the
[plugin pages](https://docs.scrapeunblocker.com/plugins/overview?utm_source=pypi&utm_medium=integration&utm_campaign=python-sdk).

```python
products = su.target_search("coffee maker", sort="price_low", max_results=48)
milk = su.woolworths_product("888137")                     # one product, with nutrition
trends = su.google_trends(["coffee", "tea"], geo="US")     # a list is sent comma-separated
reviews = su.trustpilot_reviews("www.nike.com", stars=[4, 5])
jobs = su.career_site_jobs("https://jobs.ashbyhq.com/ramp", keyword="engineer")
```

<!-- plugin-methods:start -->
| Category | Methods |
| --- | --- |
| Travel | `skyscanner.flights`, `skyscanner.hotels`, `skyscanner.carhire`, `booking_hotels`, `booking_reviews`, `airbnb_search`, `airbnb_room`, `airbnb_reviews`, `tripadvisor_list`, `tripadvisor_reviews` |
| Google | `google_local`, `google_images`, `maps_place_details`, `maps_reviews`, `google_trends`, `google_shopping`, `google_jobs`, `google_hotels`, `google_hotels_property`, `google_news`, `google_ads_transparency`, `google_ads_transparency_advertisers`, `google_ai_mode`, `google_lens` |
| AI | `gemini`, `chatgpt` |
| Search engines | `bing_search`, `bing_images`, `duckduckgo_search`, `yahoo_search`, `yahoo_images`, `brave_search`, `brave_images` |
| E-commerce | `amazon_product`, `amazon_search`, `amazon_bestsellers`, `amazon_reviews`, `amazon_offers`, `amazon_seller`, `walmart_search`, `walmart_product`, `target_search`, `target_category`, `target_product`, `bestbuy_search`, `bestbuy_product`, `homedepot_search`, `costco_search`, `costco_product`, `etsy_search`, `etsy_product`, `shein_search`, `zalando_search`, `aliexpress_search`, `aliexpress_product`, `alibaba_search`, `alibaba_product`, `alibaba1688_search`, `alibaba1688_product`, `tiktok_shop_search`, `tiktok_shop_product`, `tiktok_shop_store`, `oopbuy_search`, `smyths_inventory`, `smyths_details`, `smyths_search`, `smyths_category`, `wish_search`, `wish_product`, `shopee_search`, `shopee_product`, `taobao_search`, `taobao_product`, `flipkart_search`, `flipkart_product`, `lazada_search`, `lazada_product`, `allegro_search`, `allegro_product`, `falabella_search`, `falabella_product`, `magazineluiza_search`, `magazineluiza_product`, `mediamarkt_search`, `mediamarkt_product`, `cdiscount_search`, `cdiscount_product`, `idealo_search`, `idealo_offers`, `rakuten_search`, `rakuten_product`, `indiamart_search`, `indiamart_product`, `bedbathandbeyond_search`, `bedbathandbeyond_product`, `petco_search`, `petco_product`, `neobits_product`, `lowes_search`, `lowes_product`, `menards_search`, `menards_product`, `grainger_search`, `grainger_product` |
| Classifieds & Resale | `ebay_product`, `ebay_search`, `vinted_search`, `leboncoin_search` |
| Groceries | `woolworths_search`, `woolworths_category`, `woolworths_specials`, `woolworths_product`, `coles_search`, `coles_category`, `coles_specials`, `coles_product`, `aldi_au_search`, `aldi_au_category`, `aldi_au_specials`, `aldi_au_product`, `kroger_search`, `kroger_product`, `instacart_search`, `instacart_product`, `publix_search`, `publix_product` |
| Real estate | `zillow_search`, `zillow_detail`, `redfin_search`, `redfin_detail`, `rightmove_search`, `idealista_search`, `idealista_detail`, `immobilienscout24_search` |
| Vehicles | `mobile_de`, `autoscout24_search` |
| Jobs | `indeed_jobs`, `glassdoor_jobs`, `glassdoor_reviews`, `glassdoor_salaries`, `naukri_jobs`, `wellfound_jobs`, `wellfound_job`, `wellfound_company`, `wellfound_company_search`, `career_site_jobs`, `upwork_jobs` |
| Reviews & Companies | `trustpilot_reviews`, `g2_reviews`, `g2_search`, `capterra_reviews`, `capterra_search`, `product_hunt`, `crunchbase_company`, `crunchbase_search` |
| Local & Maps | `yelp_search`, `yelp_business`, `yelp_reviews`, `naver_place_search`, `naver_place_details` |
| Apps | `google_play_app`, `google_play_search`, `app_store_app`, `app_store_search`, `app_store_reviews` |
| Video & Music | `youtube_channel`, `youtube_search`, `youtube_transcript`, `spotify_search`, `spotify_artist`, `spotify_album`, `spotify_track`, `spotify_playlist` |
| SEO & Ads | `similarweb_overview`, `ahrefs`, `semrush_overview`, `meta_ad_library` |
<!-- plugin-methods:end -->

Any plugin endpoint can also be called by path, with parameters named as the
API names them - handy for an endpoint added after your SDK version:

```python
data = su.plugin("/marketplace/target-search", query="tv", max_results=24)
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
images = su.google_images("golden retriever puppy", proxy_country="US", pages=3)
for img in images["results"]:
    print(img["imageUrl"], img["sourceDomain"], img["title"])

# Only images Google found in the last day (for a daily scan of the same query)
new_images = su.google_images("eiffel tower", proxy_country="US", time_range="day")
# Or a fixed window: date_from / date_to (YYYY-MM-DD), each one optional
october = su.google_images("eiffel tower", date_from="2026-10-01", date_to="2026-10-07")
```

`time_range` takes `hour`, `day`, `week`, `month` or `year` and cannot be combined with `date_from` / `date_to`.

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

The bytes come back exactly as the image host serves them, in the original format (JPEG, PNG, WebP, AVIF, GIF, SVG, ...); nothing is re-encoded. Pass the image URL itself, not the page it sits on.

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
    ...   # 402: quota, credit limit, your budget limit, or a failed payment - fix billing
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
| `PaymentRequiredError` | 402 | Billing block - base class for the four below |
| `QuotaExceededError` | 402 | The plan's requests for this period are used up |
| `CreditLimitExceededError` | 402 | Unpaid balance is past the account's credit limit |
| `BudgetExceededError` | 402 | This period's spend reached the monthly budget limit you set in your profile |
| `PaymentFailedError` | 402 | A card payment was declined three times |
| `BlockedError` | 403 | Blocked by bot protection on every path |
| `NotFoundError` | 404 | What you asked for does not exist - a plugin lookup found nothing |
| `TargetNotFoundError` | 404 / 410 | The target page itself does not exist; carries `origin_status`, `html`, `destination_url` (subclass of `NotFoundError`, billed) |
| `BrowserTimeoutError` | 408 | Our browser run timed out before the page was ready |
| `UnsupportedContentError` | 415 | The URL serves something other than HTML (`get_page_source`, `get_markdown`) or other than an image (`get_image`) |
| `ValidationError` | 422 | Missing or wrong-typed parameter; `body` holds the `detail` array |
| `StepFailedError` | 422 | A browser `steps` action failed; carries `step_index`, `action`, `reason`, `selector`, `html` (subclass of `ValidationError`) |
| `RateLimitError` | 429 | Too many requests |
| `UpstreamOutageError` | 503 | The target origin is down |
| `ServerError` | 5xx | Unexpected server error, including a 504 upstream timeout |
| `ScrapeTimeoutError` | - | This client gave up locally before the API answered |
| `ConnectionError` | - | Could not reach the API |

### The target page does not exist (404 / 410)

When the site you scrape answers 404 or 410 itself, the API passes that status through with an `X-Origin-Status` header, and the client raises `TargetNotFoundError`. It is the target's final answer, so it is never retried, and it is billed like any delivered page. The not-found page is on `.html`:

```python
from scrapeunblocker import Client, TargetNotFoundError

su = Client()
try:
    html = su.get_page_source("https://example.com/removed-listing")
except TargetNotFoundError as e:
    print(e.origin_status)   # 404 or 410
    print(e.html)            # the target's own not-found page (can be empty)
```

`TargetNotFoundError` subclasses `NotFoundError`, so `except NotFoundError` catches it too. A 404 without `X-Origin-Status` is the API's own and stays a plain `NotFoundError`.

With `get_parsed()` the body is the parsed-data JSON (`{"data": {"page_type": "not_found", ...}}`), so `html` is `None` there; the raw JSON is on `.body`. With `get_markdown()` the not-found page on `.html` is Markdown.

### No structured data on the page

When `get_parsed()` renders the page but can extract no structured data from it, the API still answers 200 and the client returns a normal `ParsedPage`: `data` is empty, `data_extracted` is `False`, `detail` says why, and `html` carries the rendered page. The call is billed like any delivered page, so you already have the HTML - no second call needed:

```python
from scrapeunblocker import Client

su = Client()
page = su.get_parsed("https://example.com/some-page")
if not page.data_extracted:
    print(page.detail)      # the API's explanation
    html = page.html        # the rendered page, parse it yourself
```

On a successful parse `data_extracted` is `True` and `html` is `None`. Up to 0.7.1 this case raised `NoDataExtractedError` (a 422); the API no longer sends that, and the class stays exported only so existing imports keep working.

Every one of these subclasses `ScrapeUnblockerError`, so a single `except ScrapeUnblockerError` still catches everything, and the 402 and 401 subclasses can be caught by their base class when you do not need to tell them apart.

Transient failures (429, 502, 503, 504 and network errors) are retried automatically with exponential backoff; tune with `Client(max_retries=...)`. A 401 or 402 is never retried - it clears when the key or the billing state changes, not on another attempt. Neither is billed or counted against your quota, because the request is refused before anything is scraped.

### Billing errors (402)

The four billing blocks share a status code and differ only in their message, so the client raises a dedicated exception for each:

```python
from scrapeunblocker import (
    BudgetExceededError,
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
except BudgetExceededError:
    ...   # this period's spend reached the monthly budget limit you set
except PaymentFailedError:
    ...   # card declined three times - update the payment method
```

When more than one applies, the most serious wins: failed payment outranks credit limit, which outranks quota, which outranks your own budget limit. All four lift by themselves once the billing state changes - access returns within about a minute, and the API key stays the same. One catch worth knowing: subscribing to a new plan does **not** clear `PaymentFailedError`, because the old unpaid invoice stays open until it is paid.

`BudgetExceededError` (`User set budget exceeded`) means you set a monthly budget limit (EUR, excluding VAT) in your [profile](https://app.scrapeunblocker.com/dashboard/profile?utm_source=pypi&utm_medium=integration&utm_campaign=python-sdk) and this billing period's spend has reached it. It clears at the start of the next billing period, or within about a minute after you raise or remove the limit.

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
