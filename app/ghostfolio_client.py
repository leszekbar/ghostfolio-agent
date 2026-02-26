from typing import Any

import httpx


class GhostfolioClient:
    def __init__(self, base_url: str, token: str | None, timeout_seconds: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout_seconds = timeout_seconds

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(url, headers=self._headers(), params=params)
        response.raise_for_status()
        return response.json()

    async def get_portfolio_holdings(self, account_id: str | None = None) -> Any:
        params: dict[str, Any] = {}
        if account_id:
            params["accountId"] = account_id
        return await self._get("/api/v2/portfolio/holdings", params=params or None)

    async def get_portfolio_performance(self, query_range: str) -> Any:
        return await self._get("/api/v2/portfolio/performance", params={"range": query_range})

    async def get_orders(self) -> Any:
        return await self._get("/api/v1/order")
