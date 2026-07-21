# Changelog

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
