"""Lightweight return types for structured responses."""

from __future__ import annotations

import json as _json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


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
class XhrCall:
    """One XHR/fetch response the page received (``capture_xhr``).

    Attributes:
        url: The URL the page requested.
        method: The HTTP method, e.g. ``"GET"``.
        status: The status the site answered; ``0`` when the request failed
            without a response.
        content_type: The response's ``Content-Type``.
        body: The response body as text, or ``None`` when it was not returned
            (see ``body_omitted``).
        body_omitted: Why ``body`` is ``None``: ``"binary"``, ``"size_limit"``,
            ``"in_flight"``, ``"redirect"``, ``"unavailable"`` or
            ``"request_failed"``.
    """

    url: str
    method: str
    status: int
    content_type: Optional[str] = None
    body: Optional[str] = None
    body_omitted: Optional[str] = None

    @classmethod
    def from_dict(cls, item: Dict[str, Any]) -> "XhrCall":
        return cls(
            url=item.get("url") or "",
            method=item.get("method") or "GET",
            status=int(item.get("status") or 0),
            content_type=item.get("content_type"),
            body=item.get("body"),
            body_omitted=item.get("body_omitted"),
        )

    def json(self) -> Any:
        """The body parsed as JSON (raises ``ValueError`` when it is not)."""
        if self.body is None:
            raise ValueError(f"no body ({self.body_omitted or 'unavailable'})")
        return _json.loads(self.body)


@dataclass
class CapturedPage:
    """A page plus the XHR/fetch responses it received (``capture_xhr``).

    Attributes:
        html: The rendered page.
        xhr: The matching responses in the order the page received them.
        xhr_truncated: ``True`` when more responses matched than were returned.
        proxy: Country of the exit that served the request.
        cookies: The cookies set during the visit, when requested
            (``get_cookies=True``), otherwise ``None``.
        raw: The full JSON payload as returned by the API.
    """

    html: Optional[str]
    xhr: List[XhrCall]
    xhr_truncated: bool
    proxy: Optional[str]
    cookies: Any
    raw: Dict[str, Any]

    @classmethod
    def from_response(cls, payload: Dict[str, Any]) -> "CapturedPage":
        return cls(
            html=payload.get("html"),
            xhr=[XhrCall.from_dict(x) for x in payload.get("xhr") or []],
            xhr_truncated=bool(payload.get("xhr_truncated")),
            proxy=payload.get("proxy"),
            cookies=payload.get("cookies"),
            raw=payload,
        )


@dataclass
class PageHeaders:
    """A page plus the target's status, final URL and headers (``get_headers=True``).

    Attributes:
        html: The rendered page.
        status_code: The status the target answered with, or ``None`` when it
            could not be observed.
        final_url: The URL after redirects, or ``None`` when it could not be
            observed.
        headers: The target's response headers with lowercase names. A
            repeated header is joined with ``", "``, except ``set-cookie``,
            which is always a list of strings. ``None`` when the render path
            could not observe the headers.
        request_headers: The headers actually sent to the target (lowercase
            name -> value), or ``None``.
        proxy: Country of the exit that served the request (lowercase ISO-2),
            or ``None``.
        cookies: The cookies set during the visit, when requested
            (``get_cookies=True``), otherwise ``None``.
        raw: The full JSON payload as returned by the API.
    """

    html: Optional[str]
    status_code: Optional[int]
    final_url: Optional[str]
    headers: Optional[Dict[str, Union[str, List[str]]]]
    request_headers: Optional[Dict[str, str]]
    proxy: Optional[str]
    cookies: Any
    raw: Dict[str, Any]

    @classmethod
    def from_response(cls, payload: Dict[str, Any]) -> "PageHeaders":
        status = payload.get("status_code")
        headers = payload.get("headers")
        request_headers = payload.get("request_headers")
        return cls(
            html=payload.get("html"),
            status_code=status if isinstance(status, int) else None,
            final_url=payload.get("final_url"),
            headers=headers if isinstance(headers, dict) else None,
            request_headers=request_headers if isinstance(request_headers, dict) else None,
            proxy=payload.get("proxy"),
            cookies=payload.get("cookies"),
            raw=payload,
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
