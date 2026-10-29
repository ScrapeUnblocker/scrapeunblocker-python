# Changelog

## 0.15.1 (2026-10-29)

- `shopee_product` and `shopee_search` docs: describe `availability` and `inStock`, sold-out variations (`models[].available`, `tierIndex`), `categories` as the breadcrumb path plus `browseCategories`, `isPixPrice` (Brazilian Pix prices) and the JSON `{"status": "not_found", ...}` answer for a product that does not exist. Signatures are unchanged.

## 0.15.0 (2026-10-29)

- 23 new plugin methods on `Client` and `AsyncClient`:
  - Groceries: `kroger_search(query)` and `kroger_product(product)` (Kroger and its 18 banner stores such as Ralphs and Fred Meyer, priced for one store), `instacart_search(query, retailer=...)` and `instacart_product(product)` (any retailer on Instacart, priced for a ZIP code), `publix_search(query)` and `publix_product(product)`.
  - E-commerce: `amazon_offers()` (every seller's offer for a product, by `asin=` or `url=`), `amazon_seller()` (a seller's public profile and feedback, by `seller_id=` or `url=`), `costco_search(query)` and `costco_product(product)`, `flipkart_search(query)` and `flipkart_product(product_id)`, `lazada_search(query)` and `lazada_product(item_id)` (six markets, `country=`), `allegro_search(query)` and `allegro_product(offer_id)`, `falabella_search(query)` and `falabella_product()` (Chile, Colombia and Peru), `magazineluiza_search(query)` and `magazineluiza_product()`.
  - Google: `google_ai_mode(q)` (the AI Mode answer with the pages it cites) and `google_lens(url)` (Google Lens visual matches for an image URL).
  - AI: `gemini(prompt)` (Google Gemini's answer with its citations and sources).
- The first argument of `flipkart_product`, `lazada_product`, `allegro_product`, `falabella_search` and `magazineluiza_search` is optional, for calls that pass `url=` instead. `falabella_product` and `magazineluiza_product` take `product_id=` or `url=`.
- `instacart_search` needs `retailer=` (the retailer's Instacart slug, e.g. `"costco"`); the API answers 400 without it. `instacart_product` takes it too, unless `product` is a link that names the retailer.
- `shein_search` docs: results also carry `reviewCountText`, and the price filters apply to `price`.

No breaking changes.

## 0.14.1 (2026-10-25)

- `serp(captcha_pause=...)` docs: the API ignores `captcha_pause`; it is kept for compatibility. CAPTCHAs are handled server-side by retrying from other exits.

## 0.14.0 (2026-10-23)

- 16 new plugin methods on `Client` and `AsyncClient`:
  - Google: `google_hotels(q)` (Google Hotels search with stay prices, ratings and amenities), `google_hotels_property(property_token)` (one property's prices from every booking site), `google_news(q)` (a search, or a section with `topic=`), `google_ads_transparency()` (an advertiser's ads from the Ads Transparency Center, picked with `advertiser=` or `domain=`) and `google_ads_transparency_advertisers(q)` (advertiser lookup by name).
  - E-commerce: `shopee_search(q)` and `shopee_product(url)` (Shopee in eight markets, `country=`), `taobao_search(q)` and `taobao_product(item_id)` (Taobao and Tmall), `smyths_inventory(code)`, `smyths_details(code)`, `smyths_search(query)` and `smyths_category(category)` (Smyths Toys UK), `wish_search(query)` and `wish_product(product)`.
  - Jobs: `upwork_jobs(q)`.
- The first argument of `google_news`, `shopee_search`, `shopee_product`, `taobao_search`, `taobao_product` and `upwork_jobs` is optional, for calls that pass another input instead: `google_news(topic="technology")`, `shopee_product(shop_id=..., item_id=...)`, `taobao_product(url=...)`, `taobao_search(category=...)`, `upwork_jobs(sort="recency")` for the newest jobs.
- `temu_search` and `temu_product` (and their async twins) are deprecated: Temu's plugin is unlisted. They are kept for compatibility with the same signatures and are no longer listed in the README.
- `google_shopping` docs: result cards also carry `currencyCode` and Google's own product ids (`productId`, `catalogId`, `offerId`).

No breaking changes.

## 0.13.0 (2026-10-23)

- New `get_markdown()` (and its async twin) returns the rendered page as clean Markdown for LLMs, agents and RAG pipelines: headings, lists, tables, absolute links, images with their alt text and code blocks, without scripts, styles, navigation, footers, forms or hidden elements. It sends `markdown=true` to `/getPageSource` and is billed like an HTML call.
- `main_content_only` (default `True`) keeps only the page's main content, without navigation, site header, footer and sidebars; pass `False` to convert the whole page. The method also takes `proxy_country`, `time_sleep`, `method`, `value`, `method_timeout` and `steps`, like `get_page_source()`.
- A target page that answers 404 or 410 raises `TargetNotFoundError`, as with `get_page_source()`; the not-found page, as Markdown, is on `.html`.

No breaking changes.

## 0.12.0 (2026-10-15)

- `google_images()` (and its async twin) takes `time_range` (`"hour"`, `"day"`, `"week"`, `"month"` or `"year"`) to return only the images Google found in that recent period, so a query scanned on a schedule returns only what is new. For a fixed window pass `date_from` and/or `date_to` (`"YYYY-MM-DD"`) instead; the API answers 400 when `time_range` is combined with either.

No breaking changes.

## 0.11.1 (2026-10-15)

- `get_image` docs: the API now returns the image's original bytes and format (JPEG, PNG, WebP, AVIF, GIF, SVG, ...) instead of a PNG re-encode. The method still returns `bytes`.
- A missing image (the host's own 404/410) raises `TargetNotFoundError`; a URL that is not an image raises `UnsupportedContentError`. The 415 message no longer says "does not serve HTML", which was wrong for `get_image`.

## 0.11.0 (2026-10-13)

- Removed four plugin methods added in 0.10.0: `youtube_comments`, `telegram_channel`, `quora_question` and `quora_profile`. Those plugins are no longer offered through the SDKs; `plugin(path, params)` still reaches any endpoint your account can use.

## 0.10.1 (2026-10-13)

- `tiktok_shop_search` takes its keyword as optional, so a category-only search works (`category` option).
- `aldi_au_specials` takes `category`: a Special Buys drop date such as `2026-10-14`.
- `capterra_search` no longer offers `page` and `app_store_reviews` no longer offers `lang`; the API ignored both for those calls.
- Method docs say "proxy country" where they said "exit-IP country", and drop internal routing notes.

## 0.10.0 (2026-10-13)

- 104 new plugin methods on `Client` and `AsyncClient`, one for every public plugin endpoint: e-commerce (Walmart, Target, Best Buy, Home Depot, Etsy, Temu, SHEIN, Zalando, AliExpress, Alibaba, 1688, TikTok Shop, Amazon Best Sellers and reviews), groceries (Woolworths, Coles, ALDI Australia), travel (Booking.com reviews, Airbnb listings and reviews, Tripadvisor), Google (Trends, Shopping, Jobs, Maps place details), Bing / DuckDuckGo / Yahoo / Brave search and images, real estate (Zillow, Redfin, Rightmove, Idealista, ImmobilienScout24), vehicles (mobile.de, AutoScout24), jobs (Indeed, Glassdoor, Naukri, Wellfound, company career sites), reviews and companies (Trustpilot, G2, Capterra, Product Hunt, Crunchbase), Yelp, Naver Place, Google Play, the App Store, YouTube, Spotify, Similarweb, Ahrefs and Semrush. The README lists them by category; every parameter is on the docs plugin pages.
- Each method takes the plugin's main input positionally and the rest as keyword options. Options left at `None` are not sent, so the API's defaults apply. Methods for one mode of a multi-mode endpoint set the mode themselves (`woolworths_product("888137")`, `spotify_artist(...)`).
- New `plugin(path, **params)` calls any plugin endpoint by path.

No breaking changes.

## 0.9.0 (2026-10-07)

- New `BudgetExceededError` (a subclass of `PaymentRequiredError`): raised when the API answers 402 with `User set budget exceeded`, meaning this billing period's spend reached the monthly budget limit (EUR, excluding VAT) set in the [profile](https://app.scrapeunblocker.com/dashboard/profile). It clears at the start of the next billing period, or within about a minute after the limit is raised or removed. Like the other 402s it is never retried and not billed. Before, this body surfaced as a plain `PaymentRequiredError`.

No breaking changes: `except PaymentRequiredError` keeps catching it.

## 0.8.0 (2026-10-06)

- `get_parsed()` (and its async twin) on a page that rendered but held no structured data now returns a normal `ParsedPage` instead of raising `NoDataExtractedError`. The API answers this case with a billed 200: `data` is empty, the new `data_extracted` attribute is `False`, `detail` explains it and the new `html` attribute carries the rendered page, so no second call is needed. On a successful parse `data_extracted` is `True` and `html` / `detail` are `None`.
- `NoDataExtractedError` is deprecated: the API no longer sends the 422 `no_data_extracted`. The class stays exported so existing imports keep working.

Behaviour change: code that caught `NoDataExtractedError` should check `page.data_extracted` instead.

## 0.7.1 (2026-09-30)

- New `NoDataExtractedError` (a subclass of `ValidationError`): raised by `get_parsed()` (and its async twin) when the page rendered but no structured data could be extracted from it. The API answers 422 with `{"error": "no_data_extracted", "detail": ...}`; the error carries `detail`. The call is not billed and is never retried - use `get_page_source()` for the HTML. Before, this came back as a billed 200 with empty `data`.
- A dead URL fetched with `get_parsed()` raises `TargetNotFoundError` with `html=None` (the body is the parsed-data JSON, on `.body`).

## 0.7.0 (2026-09-30)

- New `TargetNotFoundError` (a subclass of `NotFoundError`): raised by `get_page_source()`, `get_parsed()` and `get_page_with_cookies()` (and their async twins) when the target page itself answers 404 or 410. The API now passes the target's own status through instead of a 200, marked with the `X-Origin-Status` header. The error carries `origin_status`, the not-found page on `html` and `destination_url`. It is never retried, and the call is billed like any delivered page.

Behaviour change: a dead target URL used to return its not-found page as a normal string; it now raises `TargetNotFoundError`. `except NotFoundError` catches it. A 404 without `X-Origin-Status` is the API's own and stays a plain `NotFoundError`.

## 0.6.0 (2026-09-24)

- `google_images()` (and its async twin) takes `pages` (1-5): fetch up to five Google Images result pages of ~100 results each in one call. Each page fetched is billed as one request; the response's `pagesFetched` says how many. The Google market now follows `proxy_country` automatically, so `gl` is only an optional override, and `max_results` is an optional cap up to 500.

No breaking changes.

## 0.5.0 (2026-09-17)

- Added `google_images()` (and its async twin) for the new Google Images plugin (`POST /images/google-search`). Given a keyword `q` it returns Google Images results as JSON - each with the full-size `imageUrl` and its `sourceDomain`, plus the source page URL, title, source name, thumbnail URL, pixel dimensions and file size. Optional `gl` (ISO-2 lowercase market), `max_results` (1-100) and `proxy_country` (ISO-2) refine the search.

No breaking changes.

## 0.4.0 (2026-09-16)

- Added the `southwest` namespace with `southwest.flights()` (and its async twin) for the new Southwest Airlines plugin (`POST /flights/southwest-quotes`). Given `origin`/`dest` IATA codes and a `depart_date` it queries Southwest's own booking API and returns the raw booking/shopping JSON - Southwest fares are not sold through the usual aggregators. Optional `return_date` (omit for one-way), `adults` (1-8), `fare_type` (`"dollars"` or `"points"`), `proxy_country` (Southwest is US-only) and `max_attempts` (1-5) refine the search.

No breaking changes.

## 0.3.0 (2026-09-08)

- Added `tiktok_profile()`, `tiktok_video()`, `tiktok_hashtag()`, `tiktok_search()` and `tiktok_comments()` (and their async twins) for the new TikTok plugin: a creator's exact follower / like / video counts with their newest videos (up to 200), any video or photo post with exact plays, likes, comments, shares, saves and reposts, hashtags, music, play / download URLs, subtitle tracks and an optional transcript, a hashtag's total views and videos with its videos, keyword search in TikTok's own ranking, and the comments of any post. No login.

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
