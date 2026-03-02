"""Pydantic input models and LangChain StructuredTool wrappers for all 7 agent tools."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GetPortfolioSummaryInput(BaseModel):
    """Input for retrieving portfolio summary."""

    account_id: str | None = Field(None, description="Optional account ID to filter by")


class GetPerformanceInput(BaseModel):
    """Input for retrieving portfolio performance."""

    query_range: str = Field(
        "ytd",
        description="Time range for performance data. Must be one of: '1d', 'ytd', '1y', '5y', 'max'",
    )


class GetTransactionsInput(BaseModel):
    """Input for retrieving transaction history."""

    symbol: str | None = Field(None, description="Optional stock symbol to filter by (e.g., 'AAPL')")
    tx_type: str | None = Field(None, description="Optional transaction type filter: 'BUY' or 'SELL'")
    limit: int = Field(5, description="Maximum number of transactions to return (default: 5)")


class GetAccountDetailsInput(BaseModel):
    """Input for retrieving account details."""

    account_id: str | None = Field(None, description="Optional account ID for a specific account")


class GetMarketDataInput(BaseModel):
    """Input for retrieving market data for symbols."""

    symbols: list[str] = Field(description="List of stock/ETF symbols to look up (e.g., ['AAPL', 'MSFT'])")


class AnalyzeAllocationInput(BaseModel):
    """Input for portfolio allocation analysis. No parameters needed."""

    pass


class CheckRiskRulesInput(BaseModel):
    """Input for portfolio risk assessment. No parameters needed."""

    pass


TOOL_DESCRIPTIONS: dict[str, dict[str, Any]] = {
    "get_portfolio_summary": {
        "name": "get_portfolio_summary",
        "description": (
            "Get the user's current portfolio summary including total value, currency, "
            "number of holdings, and details of each holding (symbol, name, allocation %, "
            "value, performance %). Use this when the user asks about their portfolio value, "
            "holdings, or wants a general overview."
        ),
        "input_model": GetPortfolioSummaryInput,
    },
    "get_performance": {
        "name": "get_performance",
        "description": (
            "Get portfolio performance metrics for a specific time range. Returns return "
            "percentage, absolute gain/loss, and currency. Valid ranges: '1d' (today), "
            "'ytd' (year-to-date), '1y' (one year), '5y' (five years), 'max' (all time). "
            "Use this when the user asks about returns, gains, losses, or performance."
        ),
        "input_model": GetPerformanceInput,
    },
    "get_transactions": {
        "name": "get_transactions",
        "description": (
            "Get recent transaction history (buys, sells). Can filter by symbol or "
            "transaction type. Use this when the user asks about their trades, "
            "recent buys/sells, or transaction activity."
        ),
        "input_model": GetTransactionsInput,
    },
    "get_account_details": {
        "name": "get_account_details",
        "description": (
            "Get details of the user's linked brokerage accounts including account name, "
            "balance, currency, and platform. Use this when the user asks about their "
            "accounts, cash balances, or which brokerages they use."
        ),
        "input_model": GetAccountDetailsInput,
    },
    "get_market_data": {
        "name": "get_market_data",
        "description": (
            "Look up current market data (price, daily change) for specific stock or ETF "
            "symbols. Use this when the user asks about current prices, market quotes, "
            "or how specific symbols are doing in the market."
        ),
        "input_model": GetMarketDataInput,
    },
    "analyze_allocation": {
        "name": "analyze_allocation",
        "description": (
            "Analyze the portfolio's asset allocation broken down by sector, region, "
            "and asset class. Also identifies risk flags like high concentration or "
            "low diversification. Use this when the user asks about their allocation, "
            "diversification, sector exposure, or wants a portfolio breakdown."
        ),
        "input_model": AnalyzeAllocationInput,
    },
    "check_risk_rules": {
        "name": "check_risk_rules",
        "description": (
            "Run risk assessment rules against the portfolio. Checks for concentration "
            "risk (>30% in single holding), low diversification (<5 holdings), and "
            "asset class concentration (>80% in one class). Returns triggered rules "
            "with severity levels. Use this when the user asks about portfolio risk, "
            "whether their portfolio is balanced, or wants a health check."
        ),
        "input_model": CheckRiskRulesInput,
    },
}


def build_openai_tools() -> list[dict[str, Any]]:
    """Build tool schemas suitable for OpenAI function calling / bind_tools()."""
    tools = []
    for tool_info in TOOL_DESCRIPTIONS.values():
        schema = tool_info["input_model"].model_json_schema()
        # Remove $defs, title from top level for cleaner schemas
        schema.pop("$defs", None)
        schema.pop("title", None)
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool_info["name"],
                    "description": tool_info["description"],
                    "parameters": schema,
                },
            }
        )
    return tools
