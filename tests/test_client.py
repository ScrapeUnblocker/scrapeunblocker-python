import httpx
import pytest
import respx

from scrapeunblocker import (
    AsyncClient,
    BlockedError,
    Client,
    InvalidRequestError,
    ParsedPage,
    RateLimitError,
    ScrapeUnblockerError,
    UpstreamOutageError,
)

BASE = "https://api.scrapeunblocker.com"


def make_client(**kwargs):
    return Client(api_key="test-key", **kwargs)


def test_requires_api_key(monkeypatch):
    monkeypatch.delenv("SCRAPEUNBLOCKER_KEY", raising=False)
    with pytest.raises(ScrapeUnblockerError):
        Client()


def test_api_key_from_env(monkeypatch):
    monkeypatch.setenv("SCRAPEUNBLOCKER_KEY", "from-env")
    client = Client()
    assert client._api_key == "from-env"


@respx.mock
def test_get_page_source_returns_html():
    route = respx.post(f"{BASE}/getPageSource").mock(
        return_value=httpx.Response(200, text="<html>hi</html>")
    )
    with make_client() as su:
        html = su.get_page_source("https://example.com", proxy_country="US")
    assert html == "<html>hi</html>"
    request = route.calls.last.request
    assert request.headers["x-scrapeunblocker-key"] == "test-key"
    assert "url=https%3A%2F%2Fexample.com" in str(request.url)
    assert "proxy_country=US" in str(request.url)


@respx.mock
def test_none_params_are_omitted():
    route = respx.post(f"{BASE}/getPageSource").mock(
        return_value=httpx.Response(200, text="ok")
    )
    with make_client() as su:
        su.get_page_source("https://example.com")
    url = str(route.calls.last.request.url)
    assert "proxy_country" not in url
    assert "time_sleep" not in url


@respx.mock
def test_get_parsed_returns_parsed_page():
    payload = {"data": {"page_type": "product", "source": "schema.org", "data": {"price": 10}}}
    respx.post(f"{BASE}/getPageSource").mock(return_value=httpx.Response(200, json=payload))
    with make_client() as su:
        result = su.get_parsed("https://example.com/p/1")
    assert isinstance(result, ParsedPage)
    assert result.page_type == "product"
    assert result.data == {"price": 10}


@respx.mock
def test_parsed_data_flag_sent():
    route = respx.post(f"{BASE}/getPageSource").mock(
        return_value=httpx.Response(200, json={"data": {}})
    )
    with make_client() as su:
        su.get_parsed("https://example.com", refresh_rules=True, rules_hint="price missing")
    url = str(route.calls.last.request.url)
    assert "parsed_data=true" in url
    assert "refresh_rules=true" in url
    assert "rules_hint=price+missing" in url or "rules_hint=price%20missing" in url


@respx.mock
def test_serp():
    route = respx.post(f"{BASE}/serpApi").mock(
        return_value=httpx.Response(200, json={"organic": []})
    )
    with make_client() as su:
        out = su.serp("hello world", pages_to_check=2)
    assert out == {"organic": []}
    url = str(route.calls.last.request.url)
    assert "keyword=hello" in url
    assert "pages_to_check=2" in url


@respx.mock
def test_google_local():
    route = respx.post(f"{BASE}/maps/google-local").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    with make_client() as su:
        out = su.google_local("coffee shops in chicago", proxy_country="US", gl="us")
    assert out == {"results": []}
    url = str(route.calls.last.request.url)
    assert "keyword=coffee" in url
    assert "proxy_country=US" in url
    assert "gl=us" in url


@respx.mock
def test_get_image_returns_bytes():
    respx.post(f"{BASE}/getImage").mock(
        return_value=httpx.Response(200, content=b"\x89PNG")
    )
    with make_client() as su:
        data = su.get_image("https://example.com/x.png")
    assert data == b"\x89PNG"


@respx.mock
def test_skyscanner_flights():
    route = respx.post(f"{BASE}/flights/skyscanner-quotes").mock(
        return_value=httpx.Response(200, json={"itineraries": []})
    )
    with make_client() as su:
        out = su.skyscanner.flights(origin="London", dest="Paris")
    assert out == {"itineraries": []}
    assert "origin=London" in str(route.calls.last.request.url)


@respx.mock
@pytest.mark.parametrize(
    "status,exc",
    [
        (400, InvalidRequestError),
        (403, BlockedError),
        (429, RateLimitError),
        (503, UpstreamOutageError),
    ],
)
def test_error_mapping(status, exc):
    # max_retries=0 so 429/503 raise immediately instead of retrying.
    respx.post(f"{BASE}/getPageSource").mock(
        return_value=httpx.Response(status, text="nope")
    )
    with make_client(max_retries=0) as su:
        with pytest.raises(exc) as info:
            su.get_page_source("https://example.com")
    assert info.value.status_code == status


@respx.mock
def test_retries_then_succeeds():
    route = respx.post(f"{BASE}/getPageSource").mock(
        side_effect=[
            httpx.Response(503, text="outage"),
            httpx.Response(200, text="recovered"),
        ]
    )
    with make_client(max_retries=2) as su:
        html = su.get_page_source("https://example.com")
    assert html == "recovered"
    assert route.call_count == 2


@respx.mock
async def test_async_get_page_source():
    respx.post(f"{BASE}/getPageSource").mock(
        return_value=httpx.Response(200, text="<html>async</html>")
    )
    async with AsyncClient(api_key="test-key") as su:
        html = await su.get_page_source("https://example.com")
    assert html == "<html>async</html>"


@respx.mock
async def test_async_error_mapping():
    respx.post(f"{BASE}/getPageSource").mock(return_value=httpx.Response(403, text="blocked"))
    async with AsyncClient(api_key="test-key", max_retries=0) as su:
        with pytest.raises(BlockedError):
            await su.get_page_source("https://example.com")
