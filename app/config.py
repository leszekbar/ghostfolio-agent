from pydantic_settings import BaseSettings, SettingsConfigDict

from app.schemas import DataSource


class Settings(BaseSettings):
    ghostfolio_base_url: str = "https://ghostfol.io"
    request_timeout_seconds: float = 10.0
    default_data_source: DataSource = "mock"
    log_level: str = "INFO"
    log_format: str = "json"
    log_include_stack: bool = False
    log_redact_fields: str = "authorization,access_token,ghostfolio_token,authToken,token"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="GHOSTFOLIO_")


settings = Settings()
