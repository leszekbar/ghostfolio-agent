from typing import Any

from app.ghostfolio_client import GhostfolioClient


class GhostfolioAPIDataProvider:
    def __init__(self, client: GhostfolioClient) -> None:
        self.client = client

    async def get_portfolio_summary(self, account_id: str | None = None) -> dict[str, Any]:
        response = await self.client.get_portfolio_holdings(account_id=account_id)
        if not isinstance(response, list):
            raise ValueError("Expected holdings list from Ghostfolio API")

        total_value = float(sum(item.get("marketValue", 0.0) for item in response))
        holdings = [
            {
                "symbol": item.get("symbol"),
                "name": item.get("name"),
                "allocation_pct": item.get("allocationInPercentage"),
                "value": item.get("marketValue"),
                "performance_pct": item.get("performanceInPercentage"),
            }
            for item in response
        ]
        return {
            "total_value": total_value,
            "currency": "USD",
            "holdings_count": len(holdings),
            "holdings": holdings,
        }

    async def get_performance(self, query_range: str) -> dict[str, Any]:
        response = await self.client.get_portfolio_performance(query_range=query_range)
        return {
            "range": query_range,
            "return_pct": float(response.get("performance", 0.0)),
            "absolute_gain": float(response.get("value", 0.0)),
            "currency": "USD",
        }

    async def get_transactions(self) -> list[dict[str, Any]]:
        response = await self.client.get_orders()
        if not isinstance(response, list):
            raise ValueError("Expected transaction list from Ghostfolio API")
        return [
            {
                "date": item.get("date"),
                "type": item.get("type"),
                "symbol": item.get("symbol"),
                "quantity": item.get("quantity"),
                "unit_price": item.get("unitPrice"),
                "fee": item.get("fee"),
                "currency": item.get("currency", "USD"),
            }
            for item in response
        ]
