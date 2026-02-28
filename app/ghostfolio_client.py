from typing import Any

import httpx

from app.telemetry import get_logger


logger = get_logger(__name__)


class GhostfolioClient:
    def __init__(self, base_url: str, token: str | None, timeout_seconds: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout_seconds = timeout_seconds
        self.max_network_retries = 1

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        return await self._request_json("GET", url, params=params)

    async def _post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        return await self._request_json("POST", url, json=json)

    async def _request_json(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        attempts = self.max_network_retries + 1
        last_error: Exception | None = None

        for attempt in range(attempts):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    if method == "GET":
                        response = await client.get(url, headers=self._headers(), params=params)
                    else:
                        response = await client.post(url, headers=self._headers(), json=json)
                response.raise_for_status()
                logger.debug(
                    "ghostfolio_http_success",
                    extra={
                        "method": method,
                        "url": url,
                        "status_code": response.status_code,
                        "attempt": attempt + 1,
                    },
                )
                return response.json()
            except (httpx.RequestError, httpx.TimeoutException) as exc:
                last_error = exc
                logger.warning(
                    "ghostfolio_http_retryable_error",
                    extra={
                        "method": method,
                        "url": url,
                        "attempt": attempt + 1,
                        "error": str(exc),
                    },
                )
                if attempt == attempts - 1:
                    raise

        if last_error:
            raise last_error

        raise RuntimeError("Unexpected request failure without a captured exception")

    async def get_portfolio_holdings(self, account_id: str | None = None) -> Any:
        params: dict[str, Any] = {}
        if account_id:
            params["accountId"] = account_id
        return await self._get("/api/v1/portfolio/holdings", params=params or None)

    async def get_portfolio_performance(self, query_range: str) -> Any:
        return await self._get("/api/v2/portfolio/performance", params={"range": query_range})

    async def get_orders(self) -> Any:
        return await self._get("/api/v1/order")

    async def exchange_access_token_for_auth_token(self, access_token: str) -> str:
        logger.info("ghostfolio_auth_exchange_requested")
        response = await self._post("/api/v1/auth/anonymous", json={"accessToken": access_token})
        auth_token = response.get("authToken") if isinstance(response, dict) else None
        if not auth_token:
            raise ValueError("Auth response did not contain authToken")
        return auth_token
