from datetime import UTC, datetime
from typing import Any

MOCK_HOLDINGS = [
    {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "allocation_pct": 42.5,
        "value": 21250.0,
        "performance_pct": 12.4,
        "sector": "Technology",
        "region": "North America",
        "asset_class": "Equity",
    },
    {
        "symbol": "MSFT",
        "name": "Microsoft Corp.",
        "allocation_pct": 32.5,
        "value": 16250.0,
        "performance_pct": 8.2,
        "sector": "Technology",
        "region": "North America",
        "asset_class": "Equity",
    },
    {
        "symbol": "VTI",
        "name": "Vanguard Total Stock Market ETF",
        "allocation_pct": 25.0,
        "value": 12500.0,
        "performance_pct": 6.1,
        "sector": "Diversified",
        "region": "North America",
        "asset_class": "ETF",
    },
]

MOCK_PERFORMANCE = {
    "1d": {"range": "1d", "return_pct": 0.3, "absolute_gain": 150.0, "currency": "USD"},
    "ytd": {"range": "ytd", "return_pct": 9.8, "absolute_gain": 4900.0, "currency": "USD"},
    "1y": {"range": "1y", "return_pct": 15.2, "absolute_gain": 7600.0, "currency": "USD"},
    "5y": {"range": "5y", "return_pct": 58.1, "absolute_gain": 29050.0, "currency": "USD"},
    "max": {"range": "max", "return_pct": 75.0, "absolute_gain": 37500.0, "currency": "USD"},
}

MOCK_TRANSACTIONS = [
    {
        "date": "2026-02-20",
        "type": "BUY",
        "symbol": "AAPL",
        "quantity": 10,
        "unit_price": 184.0,
        "fee": 0.0,
        "currency": "USD",
    },
    {
        "date": "2026-01-15",
        "type": "BUY",
        "symbol": "MSFT",
        "quantity": 5,
        "unit_price": 405.0,
        "fee": 0.0,
        "currency": "USD",
    },
    {
        "date": "2025-12-11",
        "type": "SELL",
        "symbol": "VTI",
        "quantity": 3,
        "unit_price": 280.0,
        "fee": 1.0,
        "currency": "USD",
    },
]

MOCK_ACCOUNTS = [
    {
        "id": "acc-1",
        "name": "Main Brokerage",
        "balance": 5420.50,
        "currency": "USD",
        "platform": "Interactive Brokers",
        "is_excluded": False,
    },
    {
        "id": "acc-2",
        "name": "Retirement 401k",
        "balance": 32150.00,
        "currency": "USD",
        "platform": "Fidelity",
        "is_excluded": False,
    },
    {
        "id": "acc-3",
        "name": "Savings",
        "balance": 12429.50,
        "currency": "USD",
        "platform": "Vanguard",
        "is_excluded": False,
    },
]

MOCK_MARKET_DATA = {
    "AAPL": {"symbol": "AAPL", "name": "Apple Inc.", "price": 184.0, "currency": "USD", "change_pct": 1.2},
    "MSFT": {"symbol": "MSFT", "name": "Microsoft Corp.", "price": 405.0, "currency": "USD", "change_pct": -0.3},
    "VTI": {
        "symbol": "VTI",
        "name": "Vanguard Total Stock Market ETF",
        "price": 280.0,
        "currency": "USD",
        "change_pct": 0.5,
    },
}


class MockPortfolioDataProvider:
    async def get_portfolio_summary(self, account_id: str | None = None) -> dict[str, Any]:
        _ = account_id
        holdings = MOCK_HOLDINGS
        total_value = sum(item["value"] for item in holdings)
        return {
            "total_value": total_value,
            "currency": "USD",
            "holdings_count": len(holdings),
            "holdings": holdings,
        }

    async def get_performance(self, query_range: str) -> dict[str, Any]:
        payload = dict(MOCK_PERFORMANCE[query_range])
        payload.setdefault("last_updated", datetime.now(UTC).isoformat().replace("+00:00", "Z"))
        return payload

    async def get_transactions(self) -> list[dict[str, Any]]:
        return MOCK_TRANSACTIONS

    async def get_accounts(self) -> list[dict[str, Any]]:
        return MOCK_ACCOUNTS

    async def get_market_data(self, symbols: list[str]) -> dict[str, Any]:
        result = {}
        for symbol in symbols:
            upper = symbol.upper()
            if upper in MOCK_MARKET_DATA:
                result[upper] = MOCK_MARKET_DATA[upper]
        return result
