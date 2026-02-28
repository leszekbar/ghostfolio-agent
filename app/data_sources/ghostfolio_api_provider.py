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

    @staticmethod
    def _first_numeric(*values: Any) -> float | None:
        for value in values:
            parsed = GhostfolioAPIDataProvider._parse_optional_float(value)
            if parsed is not None:
                return parsed
        return None

    async def get_portfolio_summary(self, account_id: str | None = None) -> dict[str, Any]:
        response = await self.client.get_portfolio_holdings(account_id=account_id)
        if isinstance(response, list):
            raw_holdings = response
        elif isinstance(response, dict) and isinstance(response.get("holdings"), list):
            raw_holdings = response["holdings"]
        else:
            raise ValueError("Expected holdings list or {holdings: [...]} from Ghostfolio API")

        holdings: list[dict[str, Any]] = []
        for index, item in enumerate(raw_holdings):
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
                        item.get("marketValue", item.get("valueInBaseCurrency")),
                        "marketValue/valueInBaseCurrency",
                        f"Holding at index {index}",
                    ),
                    "performance_pct": self._parse_optional_float(
                        item.get("performanceInPercentage", item.get("netPerformancePercentage"))
                    ),
                }
            )

        total_value = sum(item["value"] for item in holdings)
        currency = "USD"
        if holdings:
            first_holding = raw_holdings[0]
            if isinstance(first_holding, dict) and isinstance(first_holding.get("currency"), str):
                currency = first_holding["currency"]
        return {
            "total_value": total_value,
            "currency": currency,
            "holdings_count": len(holdings),
            "holdings": holdings,
        }

    async def get_performance(self, query_range: str) -> dict[str, Any]:
        response = await self.client.get_portfolio_performance(query_range=query_range)
        if not isinstance(response, dict):
            raise ValueError("Expected performance object from Ghostfolio API")

        if isinstance(response.get("performance"), dict):
            performance = response["performance"]
            return_pct = self._first_numeric(
                performance.get("netPerformancePercentage"),
                performance.get("netPerformancePercentageWithCurrencyEffect"),
            )
            if return_pct is None:
                raise ValueError(
                    "Performance payload has invalid required numeric field "
                    "'performance.netPerformancePercentage/netPerformancePercentageWithCurrencyEffect'"
                )

            absolute_gain = self._first_numeric(
                performance.get("netPerformance"),
                performance.get("netPerformanceWithCurrencyEffect"),
            )
            if absolute_gain is None:
                current_value = self._first_numeric(
                    performance.get("currentValueInBaseCurrency"),
                    performance.get("currentNetWorth"),
                )
                total_investment = self._first_numeric(
                    performance.get("totalInvestment"),
                    performance.get("totalInvestmentValueWithCurrencyEffect"),
                )
                if current_value is not None and total_investment is not None:
                    absolute_gain = current_value - total_investment
                else:
                    raise ValueError(
                        "Performance payload has invalid required numeric field "
                        "'performance.netPerformance/netPerformanceWithCurrencyEffect'"
                    )

            return {
                "range": query_range,
                "return_pct": return_pct,
                "absolute_gain": absolute_gain,
                "currency": "USD",
            }

        return {
            "range": query_range,
            "return_pct": self._parse_required_float(response.get("performance"), "performance", "Performance payload"),
            "absolute_gain": self._parse_required_float(response.get("value"), "value", "Performance payload"),
            "currency": "USD",
        }

    async def get_transactions(self) -> list[dict[str, Any]]:
        response = await self.client.get_orders()
        if isinstance(response, list):
            raw_transactions = response
        elif isinstance(response, dict) and isinstance(response.get("activities"), list):
            raw_transactions = response["activities"]
        else:
            raise ValueError(
                "Expected transaction list or {activities: [...]} from Ghostfolio API"
            )

        transactions: list[dict[str, Any]] = []
        for index, item in enumerate(raw_transactions):
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
