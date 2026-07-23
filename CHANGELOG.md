# Changelog

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
