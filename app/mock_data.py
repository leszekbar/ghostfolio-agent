MOCK_HOLDINGS = [
    {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "allocation_pct": 42.5,
        "value": 21250.0,
        "performance_pct": 12.4,
    },
    {
        "symbol": "MSFT",
        "name": "Microsoft Corp.",
        "allocation_pct": 32.5,
        "value": 16250.0,
        "performance_pct": 8.2,
    },
    {
        "symbol": "VTI",
        "name": "Vanguard Total Stock Market ETF",
        "allocation_pct": 25.0,
        "value": 12500.0,
        "performance_pct": 6.1,
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
