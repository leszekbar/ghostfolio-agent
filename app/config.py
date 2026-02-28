from pydantic_settings import BaseSettings, SettingsConfigDict

from app.schemas import DataSource


class Settings(BaseSettings):
    ghostfolio_base_url: str = "https://ghostfol.io"
    ghostfolio_token: str | None = None
    request_timeout_seconds: float = 10.0
    default_data_source: DataSource = "mock"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="GHOSTFOLIO_")


settings = Settings()
