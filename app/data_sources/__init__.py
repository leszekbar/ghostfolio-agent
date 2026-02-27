from app.data_sources.base import PortfolioDataProvider
from app.data_sources.ghostfolio_api_provider import GhostfolioAPIDataProvider
from app.data_sources.mock_provider import MockPortfolioDataProvider
from app.schemas import DataSource


def build_provider(data_source: DataSource, api_provider: GhostfolioAPIDataProvider) -> PortfolioDataProvider:
    if data_source == "mock":
        return MockPortfolioDataProvider()
    return api_provider
