from typing import Any

from app.ghostfolio_client import GhostfolioClient


class GhostfolioAPIDataProvider:
    def __init__(self, client: GhostfolioClient) -> None:
        self.client = client

    @staticmethod
    def _parse_required_float(value: Any, field_name: str, context: str) -> float:
        try:
            if value is None:
                raise ValueError
            return float(value)
        except (TypeError, ValueError):
            raise ValueError(f"{context} has invalid required numeric field '{field_name}'")

    @staticmethod
    def _parse_optional_float(value: Any) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    async def get_portfolio_summary(self, account_id: str | None = None) -> dict[str, Any]:
        response = await self.client.get_portfolio_holdings(account_id=account_id)
        if not isinstance(response, list):
            raise ValueError("Expected holdings list from Ghostfolio API")

        holdings: list[dict[str, Any]] = []
        for index, item in enumerate(response):
            if not isinstance(item, dict):
                raise ValueError(f"Holding at index {index} must be an object")
            symbol = item.get("symbol")
            name = item.get("name")
            if not symbol or not name:
                raise ValueError(f"Holding at index {index} is missing required symbol or name")
            holdings.append(
                {
                    "symbol": symbol,
                    "name": name,
                    "allocation_pct": self._parse_optional_float(item.get("allocationInPercentage")),
                    "value": self._parse_required_float(
                        item.get("marketValue"), "marketValue", f"Holding at index {index}"
                    ),
                    "performance_pct": self._parse_optional_float(item.get("performanceInPercentage")),
                }
            )

        total_value = sum(item["value"] for item in holdings)
        return {
            "total_value": total_value,
            "currency": "USD",
            "holdings_count": len(holdings),
            "holdings": holdings,
        }

    async def get_performance(self, query_range: str) -> dict[str, Any]:
        response = await self.client.get_portfolio_performance(query_range=query_range)
        if not isinstance(response, dict):
            raise ValueError("Expected performance object from Ghostfolio API")
        return {
            "range": query_range,
            "return_pct": self._parse_required_float(response.get("performance"), "performance", "Performance payload"),
            "absolute_gain": self._parse_required_float(response.get("value"), "value", "Performance payload"),
            "currency": "USD",
        }

    async def get_transactions(self) -> list[dict[str, Any]]:
        response = await self.client.get_orders()
        if not isinstance(response, list):
            raise ValueError("Expected transaction list from Ghostfolio API")

        transactions: list[dict[str, Any]] = []
        for index, item in enumerate(response):
            if not isinstance(item, dict):
                raise ValueError(f"Transaction at index {index} must be an object")
            transactions.append(
                {
                    "date": item.get("date"),
                    "type": item.get("type"),
                    "symbol": item.get("symbol"),
                    "quantity": self._parse_optional_float(item.get("quantity")),
                    "unit_price": self._parse_optional_float(item.get("unitPrice")),
                    "fee": self._parse_optional_float(item.get("fee")),
                    "currency": item.get("currency", "USD"),
                }
            )
        return transactions
