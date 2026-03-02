from dataclasses import dataclass
from typing import Any

from app.data_sources.base import PortfolioDataProvider
from app.schemas import ToolError, ToolResult
from app.telemetry import get_logger


logger = get_logger(__name__)


@dataclass
class ToolContext:
    provider: PortfolioDataProvider


def _safe_error(code: str, message: str) -> ToolResult:
    return ToolResult(success=False, error=ToolError(code=code, message=message))


async def get_portfolio_summary(context: ToolContext, account_id: str | None = None) -> ToolResult:
    logger.debug(
        "tool_called",
        extra={"tool": "get_portfolio_summary", "account_id": account_id},
    )
    try:
        data = await context.provider.get_portfolio_summary(account_id=account_id)
        return ToolResult(success=True, data=data)
    except Exception as exc:
        logger.warning("tool_failed", extra={"tool": "get_portfolio_summary", "error": str(exc)})
        return _safe_error("tool_execution_failed", str(exc))


async def get_performance(context: ToolContext, query_range: str = "ytd") -> ToolResult:
    logger.debug(
        "tool_called",
        extra={"tool": "get_performance", "query_range": query_range},
    )
    valid_ranges = {"1d", "ytd", "1y", "5y", "max"}
    if query_range not in valid_ranges:
        return _safe_error("invalid_input", f"Unsupported range '{query_range}'")

    try:
        data = await context.provider.get_performance(query_range=query_range)
        return ToolResult(success=True, data=data)
    except Exception as exc:
        logger.warning("tool_failed", extra={"tool": "get_performance", "error": str(exc)})
        return _safe_error("tool_execution_failed", str(exc))


async def get_transactions(
    context: ToolContext,
    symbol: str | None = None,
    tx_type: str | None = None,
    limit: int = 5,
) -> ToolResult:
    logger.debug(
        "tool_called",
        extra={
            "tool": "get_transactions",
            "symbol": symbol,
            "tx_type": tx_type,
            "limit": limit,
        },
    )
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
        logger.warning("tool_failed", extra={"tool": "get_transactions", "error": str(exc)})
        return _safe_error("tool_execution_failed", str(exc))


async def get_account_details(context: ToolContext, account_id: str | None = None) -> ToolResult:
    logger.debug(
        "tool_called",
        extra={"tool": "get_account_details", "account_id": account_id},
    )
    try:
        accounts = await context.provider.get_accounts()
        if account_id:
            accounts = [a for a in accounts if a.get("id") == account_id]
            if not accounts:
                return _safe_error("not_found", f"Account '{account_id}' not found")
        total_balance = sum(a.get("balance", 0) for a in accounts)
        return ToolResult(
            success=True,
            data={
                "accounts": accounts,
                "account_count": len(accounts),
                "total_balance": total_balance,
                "currency": accounts[0].get("currency", "USD") if accounts else "USD",
            },
        )
    except Exception as exc:
        logger.warning("tool_failed", extra={"tool": "get_account_details", "error": str(exc)})
        return _safe_error("tool_execution_failed", str(exc))


async def get_market_data(context: ToolContext, symbols: list[str] | None = None) -> ToolResult:
    logger.debug(
        "tool_called",
        extra={"tool": "get_market_data", "symbols": symbols},
    )
    if not symbols:
        return _safe_error("invalid_input", "At least one symbol is required")
    try:
        data = await context.provider.get_market_data(symbols)
        return ToolResult(
            success=True,
            data={
                "quotes": data,
                "symbols_found": list(data.keys()),
                "symbols_missing": [s.upper() for s in symbols if s.upper() not in data],
            },
        )
    except Exception as exc:
        logger.warning("tool_failed", extra={"tool": "get_market_data", "error": str(exc)})
        return _safe_error("tool_execution_failed", str(exc))


async def analyze_allocation(context: ToolContext) -> ToolResult:
    logger.debug("tool_called", extra={"tool": "analyze_allocation"})
    try:
        summary = await context.provider.get_portfolio_summary()
        holdings = summary.get("holdings", [])
        if not holdings:
            return ToolResult(
                success=True,
                data={
                    "by_sector": {},
                    "by_region": {},
                    "by_asset_class": {},
                    "risk_flags": ["empty_portfolio"],
                    "total_value": 0,
                    "currency": summary.get("currency", "USD"),
                },
            )

        total_value = summary["total_value"]
        currency = summary.get("currency", "USD")

        by_sector: dict[str, float] = {}
        by_region: dict[str, float] = {}
        by_asset_class: dict[str, float] = {}

        for h in holdings:
            alloc = h.get("allocation_pct", 0) or 0
            sector = h.get("sector", "Unknown") or "Unknown"
            region = h.get("region", "Unknown") or "Unknown"
            asset_class = h.get("asset_class", "Unknown") or "Unknown"

            by_sector[sector] = by_sector.get(sector, 0) + alloc
            by_region[region] = by_region.get(region, 0) + alloc
            by_asset_class[asset_class] = by_asset_class.get(asset_class, 0) + alloc

        risk_flags: list[str] = []
        # Concentration check: any single holding > 40%
        for h in holdings:
            alloc = h.get("allocation_pct", 0) or 0
            if alloc > 40:
                risk_flags.append(f"high_concentration:{h['symbol']}:{alloc:.1f}%")
        # Low diversification: fewer than 3 holdings
        if len(holdings) < 3:
            risk_flags.append("low_diversification")

        return ToolResult(
            success=True,
            data={
                "by_sector": by_sector,
                "by_region": by_region,
                "by_asset_class": by_asset_class,
                "risk_flags": risk_flags,
                "total_value": total_value,
                "currency": currency,
                "holdings_count": len(holdings),
            },
        )
    except Exception as exc:
        logger.warning("tool_failed", extra={"tool": "analyze_allocation", "error": str(exc)})
        return _safe_error("tool_execution_failed", str(exc))


async def check_risk_rules(context: ToolContext) -> ToolResult:
    logger.debug("tool_called", extra={"tool": "check_risk_rules"})
    try:
        summary = await context.provider.get_portfolio_summary()
        holdings = summary.get("holdings", [])

        rules: list[dict[str, Any]] = []

        # Rule 1: Single holding concentration > 30%
        for h in holdings:
            alloc = h.get("allocation_pct", 0) or 0
            if alloc > 30:
                rules.append({
                    "rule": "concentration",
                    "severity": "warning" if alloc <= 50 else "critical",
                    "message": f"{h['symbol']} represents {alloc:.1f}% of portfolio (threshold: 30%)",
                    "symbol": h["symbol"],
                    "value": alloc,
                })

        # Rule 2: Low diversification (< 5 holdings)
        if len(holdings) < 5:
            rules.append({
                "rule": "diversification",
                "severity": "warning",
                "message": f"Portfolio has only {len(holdings)} holdings (recommended: 5+)",
                "value": len(holdings),
            })

        # Rule 3: Single asset class > 80%
        asset_class_totals: dict[str, float] = {}
        for h in holdings:
            ac = h.get("asset_class", "Unknown") or "Unknown"
            alloc = h.get("allocation_pct", 0) or 0
            asset_class_totals[ac] = asset_class_totals.get(ac, 0) + alloc
        for ac, total in asset_class_totals.items():
            if total > 80:
                rules.append({
                    "rule": "asset_class_concentration",
                    "severity": "warning",
                    "message": f"{ac} represents {total:.1f}% of portfolio (threshold: 80%)",
                    "asset_class": ac,
                    "value": total,
                })

        risk_level = "low"
        if any(r["severity"] == "critical" for r in rules):
            risk_level = "high"
        elif rules:
            risk_level = "medium"

        return ToolResult(
            success=True,
            data={
                "rules_triggered": rules,
                "rules_count": len(rules),
                "risk_level": risk_level,
                "holdings_analyzed": len(holdings),
            },
        )
    except Exception as exc:
        logger.warning("tool_failed", extra={"tool": "check_risk_rules", "error": str(exc)})
        return _safe_error("tool_execution_failed", str(exc))


# Registry for tool dispatch by name
TOOL_REGISTRY: dict[str, Any] = {
    "get_portfolio_summary": get_portfolio_summary,
    "get_performance": get_performance,
    "get_transactions": get_transactions,
    "get_account_details": get_account_details,
    "get_market_data": get_market_data,
    "analyze_allocation": analyze_allocation,
    "check_risk_rules": check_risk_rules,
}
