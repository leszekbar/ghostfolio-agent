import pytest

from app.data_sources.ghostfolio_api_provider import GhostfolioAPIDataProvider


class FakeClient:
    def __init__(self, holdings, performance, orders):
        self._holdings = holdings
        self._performance = performance
        self._orders = orders

    async def get_portfolio_holdings(self, account_id: str | None = None):
        _ = account_id
        return self._holdings

    async def get_portfolio_performance(self, query_range: str):
        _ = query_range
        return self._performance

    async def get_orders(self):
        return self._orders


@pytest.mark.asyncio
async def test_portfolio_summary_raises_for_non_list_holdings():
    provider = GhostfolioAPIDataProvider(FakeClient(holdings={"bad": "shape"}, performance={}, orders=[]))
    with pytest.raises(ValueError, match="Expected holdings list"):
        await provider.get_portfolio_summary()


@pytest.mark.asyncio
async def test_portfolio_summary_raises_for_missing_required_fields():
    provider = GhostfolioAPIDataProvider(
        FakeClient(
            holdings=[{"name": "Apple Inc.", "marketValue": 1000}],
            performance={},
            orders=[],
        )
    )
    with pytest.raises(ValueError, match="missing required symbol or name"):
        await provider.get_portfolio_summary()


@pytest.mark.asyncio
async def test_portfolio_summary_raises_for_invalid_required_market_value():
    provider = GhostfolioAPIDataProvider(
        FakeClient(
            holdings=[
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc.",
                    "marketValue": "not-a-number",
                    "allocationInPercentage": None,
                    "performanceInPercentage": "bad",
                }
            ],
            performance={},
            orders=[],
        )
    )
    with pytest.raises(ValueError, match="invalid required numeric field 'marketValue/valueInBaseCurrency'"):
        await provider.get_portfolio_summary()


@pytest.mark.asyncio
async def test_portfolio_summary_sets_invalid_optional_numeric_fields_to_none():
    provider = GhostfolioAPIDataProvider(
        FakeClient(
            holdings=[
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc.",
                    "marketValue": 1000,
                    "allocationInPercentage": "bad",
                    "performanceInPercentage": None,
                }
            ],
            performance={},
            orders=[],
        )
    )
    result = await provider.get_portfolio_summary()
    assert result["total_value"] == 1000.0
    assert result["holdings"][0]["allocation_pct"] is None
    assert result["holdings"][0]["performance_pct"] is None


@pytest.mark.asyncio
async def test_portfolio_summary_accepts_wrapped_holdings_response():
    provider = GhostfolioAPIDataProvider(
        FakeClient(
            holdings={
                "holdings": [
                    {
                        "symbol": "AAPL",
                        "name": "Apple Inc.",
                        "currency": "USD",
                        "valueInBaseCurrency": 1234.5,
                        "allocationInPercentage": 12.5,
                        "netPerformancePercentage": 4.2,
                    }
                ]
            },
            performance={},
            orders=[],
        )
    )
    result = await provider.get_portfolio_summary()
    assert result["holdings_count"] == 1
    assert result["currency"] == "USD"
    assert result["total_value"] == 1234.5
    assert result["holdings"][0]["performance_pct"] == 4.2


@pytest.mark.asyncio
async def test_performance_raises_for_non_object_payload():
    provider = GhostfolioAPIDataProvider(FakeClient(holdings=[], performance=["bad"], orders=[]))
    with pytest.raises(ValueError, match="Expected performance object"):
        await provider.get_performance("ytd")


@pytest.mark.asyncio
async def test_performance_raises_for_invalid_required_numeric_fields():
    provider = GhostfolioAPIDataProvider(
        FakeClient(
            holdings=[],
            performance={"performance": "bad", "value": 100},
            orders=[],
        )
    )
    with pytest.raises(ValueError, match="invalid required numeric field 'performance'"):
        await provider.get_performance("ytd")


@pytest.mark.asyncio
async def test_performance_accepts_nested_performance_shape():
    provider = GhostfolioAPIDataProvider(
        FakeClient(
            holdings=[],
            performance={
                "performance": {
                    "netPerformancePercentage": 9.8,
                    "netPerformance": 4900.0,
                }
            },
            orders=[],
        )
    )
    result = await provider.get_performance("ytd")
    assert result["return_pct"] == 9.8
    assert result["absolute_gain"] == 4900.0


@pytest.mark.asyncio
async def test_performance_accepts_nested_alternative_gain_fields():
    provider = GhostfolioAPIDataProvider(
        FakeClient(
            holdings=[],
            performance={
                "performance": {
                    "netPerformancePercentageWithCurrencyEffect": 8.5,
                    "netPerformanceWithCurrencyEffect": 4200.0,
                }
            },
            orders=[],
        )
    )
    result = await provider.get_performance("ytd")
    assert result["return_pct"] == 8.5
    assert result["absolute_gain"] == 4200.0


@pytest.mark.asyncio
async def test_performance_derives_absolute_gain_from_current_and_investment():
    provider = GhostfolioAPIDataProvider(
        FakeClient(
            holdings=[],
            performance={
                "performance": {
                    "netPerformancePercentage": 6.0,
                    "currentValueInBaseCurrency": 10600.0,
                    "totalInvestment": 10000.0,
                }
            },
            orders=[],
        )
    )
    result = await provider.get_performance("ytd")
    assert result["return_pct"] == 6.0
    assert result["absolute_gain"] == 600.0


@pytest.mark.asyncio
async def test_transactions_raises_for_non_list_payload():
    provider = GhostfolioAPIDataProvider(FakeClient(holdings=[], performance={}, orders={"bad": "shape"}))
    with pytest.raises(ValueError, match="Expected transaction list or \\{activities: \\[\\.\\.\\.\\]\\}"):
        await provider.get_transactions()


@pytest.mark.asyncio
async def test_transactions_raises_for_non_object_entry():
    provider = GhostfolioAPIDataProvider(FakeClient(holdings=[], performance={}, orders=["bad"]))
    with pytest.raises(ValueError, match="Transaction at index 0 must be an object"):
        await provider.get_transactions()


@pytest.mark.asyncio
async def test_transactions_set_invalid_optional_numeric_fields_to_none():
    provider = GhostfolioAPIDataProvider(
        FakeClient(
            holdings=[],
            performance={},
            orders=[
                {
                    "date": "2026-02-20",
                    "type": "BUY",
                    "symbol": "AAPL",
                    "quantity": "bad",
                    "unitPrice": None,
                    "fee": "bad",
                    "currency": "USD",
                }
            ],
        )
    )
    transactions = await provider.get_transactions()
    assert transactions[0]["quantity"] is None
    assert transactions[0]["unit_price"] is None
    assert transactions[0]["fee"] is None


@pytest.mark.asyncio
async def test_transactions_accept_wrapped_activities_response():
    provider = GhostfolioAPIDataProvider(
        FakeClient(
            holdings=[],
            performance={},
            orders={
                "activities": [
                    {
                        "date": "2026-02-20",
                        "type": "BUY",
                        "symbol": "AAPL",
                        "quantity": 1,
                        "unitPrice": 100,
                        "fee": 0,
                        "currency": "USD",
                    }
                ],
                "count": 1,
            },
        )
    )
    transactions = await provider.get_transactions()
    assert len(transactions) == 1
    assert transactions[0]["symbol"] == "AAPL"
