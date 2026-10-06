"""Lightweight return types for structured responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ParsedPage:
    """Structured data extracted from a page (``parsed_data=True``).

    Attributes:
        page_type: What the API classified the page as, e.g. ``"product"``.
        source: How the data was extracted (Schema.org, __NEXT_DATA__, AI rules).
        data: The extracted fields as a plain dict.
        raw: The full JSON payload as returned by the API.
        data_extracted: ``False`` when the page rendered but no structured
            data could be extracted from it (``data`` is then empty).
        html: The rendered page when ``data_extracted`` is ``False``,
            otherwise ``None``.
        detail: The API's explanation when ``data_extracted`` is ``False``.
    """

    page_type: Optional[str]
    source: Optional[str]
    data: Any
    raw: Dict[str, Any]
    data_extracted: bool = True
    html: Optional[str] = None
    detail: Optional[str] = None

    @classmethod
    def from_response(cls, payload: Dict[str, Any]) -> "ParsedPage":
        inner = payload.get("data", payload) or {}
        return cls(
            page_type=inner.get("page_type"),
            source=inner.get("source"),
            data=inner.get("data"),
            raw=payload,
            data_extracted=payload.get("data_extracted") is not False,
            html=payload.get("html"),
            detail=payload.get("detail"),
        )


@dataclass
class PageResult:
    """HTML plus the cookies and proxy that served it (``get_cookies=True``)."""

    html: Optional[str]
    cookies: Any
    proxy: Optional[str]
    raw: Dict[str, Any]

    @classmethod
    def from_response(cls, payload: Dict[str, Any]) -> "PageResult":
        return cls(
            html=payload.get("html") or payload.get("page_source") or payload.get("content"),
            cookies=payload.get("cookies"),
            proxy=payload.get("proxy") or payload.get("proxy_address"),
            raw=payload,
        )
