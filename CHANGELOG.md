# Changelog

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
