"""LLM factory — OpenAI first, Anthropic fallback, None if no keys."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.config import settings
from app.telemetry import get_logger

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel

logger = get_logger(__name__)


def get_llm() -> BaseChatModel | None:
    """Return the best available chat model, or None when no API keys are set."""
    if not settings.llm_enabled:
        logger.info("llm_disabled", extra={"reason": "llm_enabled=False"})
        return None

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
