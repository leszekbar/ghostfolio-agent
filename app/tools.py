from dataclasses import dataclass
from typing import Any

from app.ghostfolio_client import GhostfolioClient
from app.mock_data import MOCK_HOLDINGS, MOCK_PERFORMANCE, MOCK_TRANSACTIONS
from app.schemas import DataSource, ToolError, ToolResult


@dataclass
class ToolContext:
    data_source: DataSource
    client: GhostfolioClient


def _safe_error(code: str, message: str) -> ToolResult:
    return ToolResult(success=False, error=ToolError(code=code, message=message))


async def get_portfolio_summary(context: ToolContext, account_id: str | None = None) -> ToolResult:
    try:
        if context.data_source == "mock":
            holdings = MOCK_HOLDINGS
            total_value = sum(item["value"] for item in holdings)
            return ToolResult(
                success=True,
                data={
                    "total_value": total_value,
                    "currency": "USD",
                    "holdings_count": len(holdings),
                    "holdings": holdings,
                },
            )

        response = await context.client.get_portfolio_holdings(account_id=account_id)
        if not isinstance(response, list):
            return _safe_error("invalid_api_shape", "Expected holdings list from Ghostfolio API")
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
        return ToolResult(
            success=True,
            data={
                "total_value": total_value,
                "currency": "USD",
                "holdings_count": len(holdings),
                "holdings": holdings,
            },
        )
    except Exception as exc:
        return _safe_error("tool_execution_failed", str(exc))


async def get_performance(context: ToolContext, query_range: str = "ytd") -> ToolResult:
    valid_ranges = {"1d", "ytd", "1y", "5y", "max"}
    if query_range not in valid_ranges:
        return _safe_error("invalid_input", f"Unsupported range '{query_range}'")

    try:
        if context.data_source == "mock":
            return ToolResult(success=True, data=MOCK_PERFORMANCE[query_range])

        response = await context.client.get_portfolio_performance(query_range=query_range)
        return_pct = float(response.get("performance", 0.0))
        absolute_gain = float(response.get("value", 0.0))
        return ToolResult(
            success=True,
            data={
                "range": query_range,
                "return_pct": return_pct,
                "absolute_gain": absolute_gain,
                "currency": "USD",
            },
        )
    except Exception as exc:
        return _safe_error("tool_execution_failed", str(exc))


async def get_transactions(
    context: ToolContext,
    symbol: str | None = None,
    tx_type: str | None = None,
    limit: int = 5,
) -> ToolResult:
    try:
        transactions: list[dict[str, Any]]
        if context.data_source == "mock":
            transactions = MOCK_TRANSACTIONS
        else:
            response = await context.client.get_orders()
            if not isinstance(response, list):
                return _safe_error("invalid_api_shape", "Expected transaction list from Ghostfolio API")
            transactions = [
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

        filtered = transactions
        if symbol:
            filtered = [item for item in filtered if item.get("symbol", "").upper() == symbol.upper()]
        if tx_type:
            filtered = [item for item in filtered if item.get("type", "").upper() == tx_type.upper()]
        filtered = filtered[: max(limit, 1)]

        return ToolResult(success=True, data={"transactions": filtered, "total_count": len(filtered)})
    except Exception as exc:
        return _safe_error("tool_execution_failed", str(exc))
