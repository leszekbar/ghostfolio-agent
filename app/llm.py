"""LLM factory — OpenRouter (preferred), OpenAI, Anthropic fallback, None if no keys."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.config import settings
from app.telemetry import get_logger

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel

logger = get_logger(__name__)

# Friendly name → OpenRouter model ID
OPENROUTER_MODELS: dict[str, str] = {
    "gpt-o": "openai/o4-mini",
    "gpt-mini": "openai/gpt-4.1-mini",
    "claude-haiku": "anthropic/claude-haiku-4-5-20251001",
    "claude-sonnet": "anthropic/claude-sonnet-4-20250514",
    "claude-opus": "anthropic/claude-opus-4-20250514",
}

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _resolve_openrouter_model(agent_model: str) -> str | None:
    """Map a friendly model name to an OpenRouter model ID."""
    key = agent_model.strip().lower()
    if key in OPENROUTER_MODELS:
        return OPENROUTER_MODELS[key]
    # Allow passing a raw OpenRouter model ID directly (e.g. "openai/gpt-4.1")
    if "/" in agent_model:
        return agent_model
    return None


def get_active_model_name() -> str:
    """Return the display name of the active LLM model."""
    if not settings.llm_enabled:
        return "rule-based (no LLM)"

    if settings.openrouter_api_key and settings.agent_model:
        model_id = _resolve_openrouter_model(settings.agent_model)
        if model_id:
            return f"{settings.agent_model} ({model_id})"

    if settings.openai_api_key:
        return settings.openai_model
    if settings.anthropic_api_key:
        return settings.anthropic_model
    return "rule-based (no LLM)"


def get_llm() -> BaseChatModel | None:
    """Return the best available chat model, or None when no API keys are set."""
    if not settings.llm_enabled:
        logger.info("llm_disabled", extra={"reason": "llm_enabled=False"})
        return None

    # OpenRouter takes priority when both api key and model are configured
    if settings.openrouter_api_key and settings.agent_model:
        model_id = _resolve_openrouter_model(settings.agent_model)
        if model_id:
            try:
                from langchain_openai import ChatOpenAI

                logger.info(
                    "llm_selected",
                    extra={"provider": "openrouter", "model": model_id, "agent_model": settings.agent_model},
                )
                return ChatOpenAI(
                    model=model_id,
                    api_key=settings.openrouter_api_key,
                    base_url=OPENROUTER_BASE_URL,
                    temperature=0,
                )
            except Exception as exc:
                logger.warning("llm_openrouter_init_failed", extra={"error": str(exc)})
        else:
            logger.warning(
                "llm_openrouter_unknown_model",
                extra={"agent_model": settings.agent_model, "available": list(OPENROUTER_MODELS.keys())},
            )

    # Direct OpenAI fallback
    if settings.openai_api_key:
        try:
            from langchain_openai import ChatOpenAI

            logger.info("llm_selected", extra={"provider": "openai", "model": settings.openai_model})
            return ChatOpenAI(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
                temperature=0,
            )
        except Exception as exc:
            logger.warning("llm_openai_init_failed", extra={"error": str(exc)})

    # Direct Anthropic fallback
    if settings.anthropic_api_key:
        try:
            from langchain_anthropic import ChatAnthropic

            logger.info("llm_selected", extra={"provider": "anthropic", "model": settings.anthropic_model})
            return ChatAnthropic(
                model=settings.anthropic_model,
                api_key=settings.anthropic_api_key,
                temperature=0,
            )
        except Exception as exc:
            logger.warning("llm_anthropic_init_failed", extra={"error": str(exc)})

    logger.info("llm_unavailable", extra={"reason": "no API keys configured"})
    return None


def get_eval_llm() -> BaseChatModel | None:
    """Return the evaluation/judge model (gpt-4.1-mini), or None."""
    if not settings.openai_api_key:
        return None
    try:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.openai_eval_model,
            api_key=settings.openai_api_key,
            temperature=0,
        )
    except Exception:
        return None
