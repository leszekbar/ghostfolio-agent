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

    # LLM settings
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1"
    openai_eval_model: str = "gpt-4.1-mini"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    llm_enabled: bool = True

    # Langfuse observability
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="GHOSTFOLIO_")


settings = Settings()
