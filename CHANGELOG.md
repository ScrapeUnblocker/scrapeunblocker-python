# Changelog

## 0.2.1 (2026-09-02)

- Added `meta_ad_library()` (and its async twin) for the new Meta Ad Library plugin (`POST /ads/meta-ad-library`). Given an `advertiser` name it returns that advertiser's Meta/Facebook Ad Library ads as JSON - each with ad text, CTA text, display format, creatives (image and video URLs), link URL, platforms, when it started running and whether it is still active. Optional `country`, `active_status`, `media_type` and `max_ads` refine the query; when omitted the API applies its own defaults (country=US, active_status=active, media_type=all, max_ads=50).

No breaking changes.

## 0.2.0 (2026-08-29)

- `get_page_source()` (and its async twin) gained two new parameters for the getPageSource endpoint:
  - `steps`: an ordered list of browser-action dicts run in a real browser after the page loads - `wait_for`, `wait_for_text`, `wait`, `click`, `type` (human-like), `select`, `press_key` and `scroll`. Pass a plain list of dicts, e.g. `[{"action": "click", "selector": "#more"}, {"action": "wait_for", "selector": ".results"}]`; the SDK JSON-encodes it into the `steps` query param. A request with steps runs once and is non-idempotent.
  - `list_elements`: when `True`, the API returns a JSON dict (`{"url", "count", "elements": [...]}`) describing the page's interactive/labelled elements instead of HTML - handy for discovering the selectors to drive `steps`. The method then returns that `dict` rather than a string, mirroring `get_parsed()`.
- Added `StepFailedError` (a subclass of `ValidationError`, HTTP 422) raised when a browser step fails. It surfaces the API's `step_failed` body directly through `step_index`, `action`, `reason`, `selector` and `html` attributes. Because it derives from `ValidationError`, existing `except ValidationError` / `except APIError` handlers keep catching it; ordinary (non-step) 422s stay a plain `ValidationError`.

No breaking changes: the new parameters default to off, and `StepFailedError` is a `ValidationError` subclass.

## 0.1.9 (2026-08-28)

- Added `amazon_product()` and `amazon_search()` (and their async twins) for the new Amazon plugin. `amazon_product()` returns one product by ASIN or URL - title, brand, numeric price and currency, list price and savings, availability, rating, review count, seller, feature bullets, categories and images. `amazon_search()` returns a keyword search's cards - asin, title, price, list price, rating, review count, a clean product URL, image and the sponsored/prime flags - on any of 20 regional marketplaces.
- Prices come back in the right currency automatically: `proxy_country` defaults to the marketplace's home country (amazon.com -> US, amazon.de -> DE), pinning the exit over our ISP pool.

No breaking changes.

## 0.1.8 (2026-07-31)

- Added `ebay_search()` (and its async twin) for the new eBay Search plugin: listings from any of the 19 regional eBay marketplaces as structured JSON - title, numeric price and currency, condition with a normalised `conditionCode`, seller username and feedback, shipping cost, sold/watcher/bid counts, image and a clean item URL.
- Filters map straight onto the plugin: `marketplace`, `condition`, `sort`, `listing_type`, `min_price`/`max_price`, `free_shipping`, `seller`, `category`, plus `page`/`page_size` (60, 120 or 240).
- The response carries `exactMatches`; it is `False` when eBay found no match for the keyword and answered with its own loosely-related suggestions.

No breaking changes.

## 0.1.7 (2026-07-27)

- Registry and README links to scrapeunblocker.com now carry UTM parameters so traffic from package registries is attributable. No functional changes.

## 0.1.6 (2026-07-23)

- Added `PaymentRequiredError` for HTTP 402, which previously surfaced as a bare `APIError` with no explanation. The three billing blocks now each get their own subclass, picked from the response body: `QuotaExceededError` (`Quota exceeded`), `CreditLimitExceededError` (`Credit limit exceeded`) and `PaymentFailedError` (`Payment failed - update payment method`). Catch `PaymentRequiredError` to handle all three.
- Added `NoSubscriptionError`, a subclass of `AuthenticationError`, for the 401 that means "the key is fine, the account has no active plan" (`No valid subscription`) as opposed to an unrecognised key.
- Added typed exceptions for the remaining documented status codes: `NotFoundError` (404), `BrowserTimeoutError` (408), `UnsupportedContentError` (415) and `ValidationError` (422). All previously raised a bare `APIError`.
- Error messages now describe every documented status code accurately - notably 400, which also covers a missing `x-scrapeunblocker-key` header, not just a bad URL.
- Documented the full exception hierarchy in the README, including which errors are retried, which are billed, and how each 402 clears.

No breaking changes: every new class derives from `APIError`, so existing `except APIError` / `except ScrapeUnblockerError` handlers keep working unchanged.

## 0.1.5 (2026-07-22)

- Added `oopbuy_search(keyword, ...)` (sync and async) for the new Oopbuy product search plugin (`POST /goods/oopbuy-search`) - searches the 1688, Taobao or official channel and returns products (SPU, title, price, monthly sales, image, URL) as JSON.

## 0.1.4

- Added `google_local(keyword, ...)` (sync and async) for the new Google Local (Maps) plugin (`POST /maps/google-local`) - returns local business listings (name, rating, reviews, price, category, address, hours) as JSON.

## 0.1.3

- Metadata: expanded keywords and summary (Skyscanner flights/hotels/car hire, Google SERP) so the package is discoverable for those searches. No code changes.

## 0.1.2

- `serp()` now calls the canonical public `/serpApi` endpoint (was the internal `/serp` alias).

## 0.1.1

- Docs: use a neutral `YOUR_API_KEY` placeholder in examples (keys are opaque, they do not carry a prefix).

## 0.1.0

Initial release.

- Sync `Client` and async `AsyncClient`.
- `get_page_source`, `get_parsed`, `get_page_with_cookies`, `serp`, `get_image`.
- Skyscanner plugins: flights, hotels, car hire (quotes + locations).
- Typed exception hierarchy and automatic retry on transient failures.
