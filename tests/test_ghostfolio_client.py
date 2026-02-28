import httpx
import pytest

from app.ghostfolio_client import GhostfolioClient


@pytest.mark.asyncio
async def test_get_uses_httpx_async_client_get(monkeypatch: pytest.MonkeyPatch):
    client = GhostfolioClient("https://ghostfol.io", token=None, timeout_seconds=10.0)
    calls = {"count": 0}

    async def fake_get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ):
        calls["count"] += 1
        return httpx.Response(200, json=[], request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    await client.get_orders()
    assert calls["count"] == 1


@pytest.mark.asyncio
async def test_get_retries_once_on_network_error(monkeypatch: pytest.MonkeyPatch):
    client = GhostfolioClient("https://ghostfol.io", token=None, timeout_seconds=10.0)
    attempts = {"count": 0}

    async def fake_get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise httpx.ConnectError("temporary network issue", request=httpx.Request("GET", url))
        return httpx.Response(200, json=[{"ok": True}], request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    result = await client.get_orders()
    assert attempts["count"] == 2
    assert result == [{"ok": True}]


@pytest.mark.asyncio
async def test_get_raises_after_retry_exhausted(monkeypatch: pytest.MonkeyPatch):
    client = GhostfolioClient("https://ghostfol.io", token=None, timeout_seconds=10.0)
    attempts = {"count": 0}

    async def fake_get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ):
        attempts["count"] += 1
        raise httpx.ConnectError("persistent network issue", request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    with pytest.raises(httpx.ConnectError):
        await client.get_orders()
    assert attempts["count"] == 2


@pytest.mark.asyncio
async def test_get_does_not_retry_on_http_status_error(monkeypatch: pytest.MonkeyPatch):
    client = GhostfolioClient("https://ghostfol.io", token=None, timeout_seconds=10.0)
    attempts = {"count": 0}

    async def fake_get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ):
        attempts["count"] += 1
        return httpx.Response(500, json={"error": "server"}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    with pytest.raises(httpx.HTTPStatusError):
        await client.get_orders()
    assert attempts["count"] == 1


@pytest.mark.asyncio
async def test_get_portfolio_holdings_calls_get_with_account_param(
    monkeypatch: pytest.MonkeyPatch,
):
    client = GhostfolioClient("https://ghostfol.io", token=None, timeout_seconds=10.0)
    captured: dict[str, object] = {}

    async def fake_get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ):
        captured["url"] = url
        captured["params"] = params
        return httpx.Response(200, json=[], request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    await client.get_portfolio_holdings(account_id="acc-123")
    assert captured["url"] == "https://ghostfol.io/api/v1/portfolio/holdings"
    assert captured["params"] == {"accountId": "acc-123"}


@pytest.mark.asyncio
async def test_get_portfolio_performance_calls_get_with_range_param(
    monkeypatch: pytest.MonkeyPatch,
):
    client = GhostfolioClient("https://ghostfol.io", token=None, timeout_seconds=10.0)
    captured: dict[str, object] = {}

    async def fake_get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ):
        captured["url"] = url
        captured["params"] = params
        return httpx.Response(200, json={"ok": True}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    await client.get_portfolio_performance(query_range="ytd")
    assert captured["url"] == "https://ghostfol.io/api/v2/portfolio/performance"
    assert captured["params"] == {"range": "ytd"}


@pytest.mark.asyncio
async def test_exchange_access_token_for_auth_token_calls_auth_endpoint(
    monkeypatch: pytest.MonkeyPatch,
):
    client = GhostfolioClient("https://ghostfol.io", token=None, timeout_seconds=10.0)
    captured: dict[str, object] = {}

    async def fake_post(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        json: dict[str, str] | None = None,
    ):
        captured["url"] = url
        captured["json"] = json
        return httpx.Response(
            200,
            json={"authToken": "jwt-token"},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    auth_token = await client.exchange_access_token_for_auth_token("security-token")
    assert auth_token == "jwt-token"
    assert captured["url"] == "https://ghostfol.io/api/v1/auth/anonymous"
    assert captured["json"] == {"accessToken": "security-token"}
