from app.data_sources import build_provider
from app.data_sources.ghostfolio_api_provider import GhostfolioAPIDataProvider
from app.data_sources.mock_provider import MockPortfolioDataProvider
from app.ghostfolio_client import GhostfolioClient
from app.schemas import DATA_SOURCE_GHOSTFOLIO_API, DATA_SOURCE_MOCK


def test_build_provider_returns_mock_for_mock_source():
    api_provider = GhostfolioAPIDataProvider(GhostfolioClient("https://ghostfol.io", token=None, timeout_seconds=10.0))
    provider = build_provider(DATA_SOURCE_MOCK, api_provider)
    assert isinstance(provider, MockPortfolioDataProvider)


def test_build_provider_returns_api_for_live_source():
    api_provider = GhostfolioAPIDataProvider(GhostfolioClient("https://ghostfol.io", token=None, timeout_seconds=10.0))
    provider = build_provider(DATA_SOURCE_GHOSTFOLIO_API, api_provider)
    assert provider is api_provider
