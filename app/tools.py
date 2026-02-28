from dataclasses import dataclass
from typing import Any

from app.data_sources.base import PortfolioDataProvider
from app.schemas import ToolError, ToolResult


@dataclass
class ToolContext:
    provider: PortfolioDataProvider


def _safe_error(code: str, message: str) -> ToolResult:
    return ToolResult(success=False, error=ToolError(code=code, message=message))


async def get_portfolio_summary(context: ToolContext, account_id: str | None = None) -> ToolResult:
    try:
        data = await context.provider.get_portfolio_summary(account_id=account_id)
        return ToolResult(success=True, data=data)
    except Exception as exc:
        return _safe_error("tool_execution_failed", str(exc))


async def get_performance(context: ToolContext, query_range: str = "ytd") -> ToolResult:
    valid_ranges = {"1d", "ytd", "1y", "5y", "max"}
    if query_range not in valid_ranges:
        return _safe_error("invalid_input", f"Unsupported range '{query_range}'")

    try:
        data = await context.provider.get_performance(query_range=query_range)
        return ToolResult(success=True, data=data)
    except Exception as exc:
        return _safe_error("tool_execution_failed", str(exc))


async def get_transactions(
    context: ToolContext,
    symbol: str | None = None,
    tx_type: str | None = None,
    limit: int = 5,
) -> ToolResult:
    try:
        transactions = await context.provider.get_transactions()

        filtered = transactions
        if symbol:
            filtered = [item for item in filtered if item.get("symbol", "").upper() == symbol.upper()]
        if tx_type:
            filtered = [item for item in filtered if item.get("type", "").upper() == tx_type.upper()]
        filtered = filtered[: max(limit, 1)]

        return ToolResult(success=True, data={"transactions": filtered, "total_count": len(filtered)})
    except Exception as exc:
        return _safe_error("tool_execution_failed", str(exc))
