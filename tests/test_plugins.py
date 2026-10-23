import inspect
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import respx

from scrapeunblocker import AsyncClient, Client
from scrapeunblocker._plugins import _AsyncPluginMethods, _PluginMethods

BASE = "https://api.scrapeunblocker.com"


def _query(route):
    return parse_qs(urlparse(str(route.calls.last.request.url)).query)


def _plugin_methods(cls):
    return [
        name
        for name, fn in inspect.getmembers(cls, inspect.isfunction)
        if not name.startswith("_") and name != "plugin"
    ]


def test_sync_and_async_mixins_offer_the_same_methods():
    assert _plugin_methods(_PluginMethods) == _plugin_methods(_AsyncPluginMethods)
    assert len(_plugin_methods(_PluginMethods)) > 90


@respx.mock
@pytest.mark.parametrize("name", _plugin_methods(_PluginMethods))
def test_every_method_posts_its_positional_args(name):
    route = respx.post(url__startswith=BASE).mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    method = getattr(Client(api_key="test-key"), name)
    params = inspect.signature(method).parameters.values()
    positional = [p for p in params if p.kind is p.POSITIONAL_OR_KEYWORD]
    args = [f"v{i}" for i, _ in enumerate(positional)]
    assert method(*args) == {"ok": True}
    request = route.calls.last.request
    assert request.method == "POST"
    query = _query(route)
    for i, p in enumerate(positional):
        assert query[p.name] == [f"v{i}"]


@respx.mock
def test_options_are_sent_under_their_api_names_and_unset_ones_are_left_out():
    route = respx.post(f"{BASE}/marketplace/target-search").mock(
        return_value=httpx.Response(200, json={"products": []})
    )
    with Client(api_key="test-key") as su:
        assert su.target_search("tv", sort="price_low", max_results=48) == {"products": []}
    assert _query(route) == {"query": ["tv"], "sort": ["price_low"], "max_results": ["48"]}


@respx.mock
def test_a_mode_method_pins_its_mode():
    route = respx.post(f"{BASE}/groceries/woolworths").mock(
        return_value=httpx.Response(200, json={"product": {}})
    )
    with Client(api_key="test-key") as su:
        su.woolworths_product("888137")
    assert _query(route) == {"mode": ["product"], "product": ["888137"]}


@respx.mock
def test_two_positional_arguments_and_a_false_flag():
    route = respx.post(f"{BASE}/local/yelp").mock(
        return_value=httpx.Response(200, json={"businesses": []})
    )
    with Client(api_key="test-key") as su:
        su.yelp_search("coffee", "San Francisco, CA", open_now=False)
    assert _query(route) == {
        "mode": ["search"],
        "find_desc": ["coffee"],
        "find_loc": ["San Francisco, CA"],
        "open_now": ["false"],
    }


@respx.mock
def test_a_list_is_joined_where_the_api_takes_one_string():
    route = respx.post(f"{BASE}/trends/google-trends").mock(
        return_value=httpx.Response(200, json={})
    )
    with Client(api_key="test-key") as su:
        su.google_trends(["coffee", "tea"], geo="US")
    assert _query(route) == {"keywords": ["coffee,tea"], "geo": ["US"]}


@respx.mock
def test_a_list_parameter_repeats_its_key():
    route = respx.post(f"{BASE}/reviews/trustpilot").mock(
        return_value=httpx.Response(200, json={"reviews": []})
    )
    with Client(api_key="test-key") as su:
        su.trustpilot_reviews("www.nike.com", stars=[4, 5])
    assert _query(route) == {"company": ["www.nike.com"], "stars": ["4", "5"]}


@respx.mock
def test_optional_positional_argument_can_be_left_out():
    route = respx.post(f"{BASE}/jobs/career-site").mock(
        return_value=httpx.Response(200, json={"jobs": []})
    )
    with Client(api_key="test-key") as su:
        su.career_site_jobs(provider="greenhouse", company="stripe")
    assert _query(route) == {"provider": ["greenhouse"], "company": ["stripe"]}


@respx.mock
def test_generic_plugin_call():
    route = respx.post(f"{BASE}/marketplace/target-search").mock(
        return_value=httpx.Response(200, json={"products": []})
    )
    with Client(api_key="test-key") as su:
        su.plugin("/marketplace/target-search", query="tv", sort=None)
    assert _query(route) == {"query": ["tv"]}


@respx.mock
async def test_async_methods():
    route = respx.post(f"{BASE}/groceries/coles").mock(
        return_value=httpx.Response(200, json={"products": []})
    )
    async with AsyncClient(api_key="test-key") as su:
        assert await su.coles_search("milk", max_results=96) == {"products": []}
        await su.plugin("/groceries/coles", mode="specials")
    assert _query(route) == {"mode": ["specials"]}
    first = parse_qs(urlparse(str(route.calls[0].request.url)).query)
    assert first == {"mode": ["search"], "query": ["milk"], "max_results": ["96"]}


@respx.mock
def test_google_hotels_search_and_property():
    search = respx.post(f"{BASE}/travel/google-hotels").mock(
        return_value=httpx.Response(200, json={"properties": []})
    )
    prop = respx.post(f"{BASE}/travel/google-hotels-property").mock(
        return_value=httpx.Response(200, json={"offers": []})
    )
    with Client(api_key="test-key") as su:
        su.google_hotels("hotels in Paris", check_in="2026-11-02", check_out="2026-11-05", currency="EUR")
        su.google_hotels_property("ChkIqp", adults=1, children="7,10")
    assert _query(search) == {
        "q": ["hotels in Paris"],
        "check_in": ["2026-11-02"],
        "check_out": ["2026-11-05"],
        "currency": ["EUR"],
    }
    assert _query(prop) == {"property_token": ["ChkIqp"], "adults": ["1"], "children": ["7,10"]}


@respx.mock
def test_google_news_search_or_section():
    route = respx.post(f"{BASE}/search/google-news").mock(
        return_value=httpx.Response(200, json={"articles": []})
    )
    with Client(api_key="test-key") as su:
        su.google_news("tesla", when="1d", max_results=50)
        assert _query(route) == {"q": ["tesla"], "when": ["1d"], "max_results": ["50"]}
        su.google_news(topic="technology", gl="gb")
    assert _query(route) == {"topic": ["technology"], "gl": ["gb"]}


@respx.mock
def test_google_ads_transparency_and_advertisers():
    ads = respx.post(f"{BASE}/ads/google-ads-transparency").mock(
        return_value=httpx.Response(200, json={"ads": []})
    )
    advertisers = respx.post(f"{BASE}/ads/google-ads-transparency-advertisers").mock(
        return_value=httpx.Response(200, json={"advertisers": []})
    )
    with Client(api_key="test-key") as su:
        su.google_ads_transparency(domain="nike.com", format="video", include_preview=False)
        su.google_ads_transparency_advertisers("nike", max_results=5)
    assert _query(ads) == {"domain": ["nike.com"], "format": ["video"], "include_preview": ["false"]}
    assert _query(advertisers) == {"q": ["nike"], "max_results": ["5"]}


@respx.mock
def test_shopee_search_and_product():
    search = respx.post(f"{BASE}/marketplace/shopee-search").mock(
        return_value=httpx.Response(200, json={"products": []})
    )
    product = respx.post(f"{BASE}/marketplace/shopee-product").mock(
        return_value=httpx.Response(200, json={"title": "Case"})
    )
    with Client(api_key="test-key") as su:
        su.shopee_search("lego", country="my", sort="sales", min_price=10)
        su.shopee_product(shop_id="442800909", item_id="40270108836", country="sg")
    assert _query(search) == {"q": ["lego"], "country": ["my"], "sort": ["sales"], "min_price": ["10"]}
    assert _query(product) == {"shop_id": ["442800909"], "item_id": ["40270108836"], "country": ["sg"]}


@respx.mock
def test_taobao_search_and_product():
    search = respx.post(f"{BASE}/marketplace/taobao-search").mock(
        return_value=httpx.Response(200, json={"products": []})
    )
    product = respx.post(f"{BASE}/marketplace/taobao-product").mock(
        return_value=httpx.Response(200, json={"itemId": "765833709683"})
    )
    with Client(api_key="test-key") as su:
        su.taobao_search("phone case", sort="sales", price_max=99.5, filter="20000-88634403")
        su.taobao_product(url="https://item.taobao.com/item.htm?id=765833709683")
    assert _query(search) == {
        "q": ["phone case"],
        "sort": ["sales"],
        "price_max": ["99.5"],
        "filter": ["20000-88634403"],
    }
    assert _query(product) == {"url": ["https://item.taobao.com/item.htm?id=765833709683"]}


@respx.mock
def test_upwork_jobs_without_a_query():
    route = respx.post(f"{BASE}/jobs/upwork").mock(
        return_value=httpx.Response(200, json={"jobs": []})
    )
    with Client(api_key="test-key") as su:
        su.upwork_jobs(sort="recency", job_type="hourly", details=True)
    assert _query(route) == {"job_type": ["hourly"], "sort": ["recency"], "details": ["true"]}


@respx.mock
def test_smyths_and_wish():
    smyths = respx.post(f"{BASE}/marketplace/smyths-inventory").mock(
        return_value=httpx.Response(200, json={"products": []})
    )
    wish = respx.post(f"{BASE}/marketplace/wish-search").mock(
        return_value=httpx.Response(200, json={"products": []})
    )
    with Client(api_key="test-key") as su:
        su.smyths_search("lego", max_results=24)
        su.wish_search("phone case", page=2)
    assert _query(smyths) == {"mode": ["search"], "query": ["lego"], "max_results": ["24"]}
    assert _query(wish) == {"query": ["phone case"], "page": ["2"]}
