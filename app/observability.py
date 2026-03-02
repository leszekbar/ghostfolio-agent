"""Langfuse observability — traces agent runs, tool calls, and LLM interactions.

No-ops gracefully when Langfuse keys are not configured.
"""

from __future__ import annotations

import time
from collections.abc import Generator
from contextlib import contextmanager, suppress
from typing import Any

from app.config import settings
from app.telemetry import get_logger

logger = get_logger(__name__)

_langfuse_client = None
_initialized = False


def _ensure_langfuse() -> Any:
    """Lazy-initialize Langfuse client. Returns None if keys are missing."""
    global _langfuse_client, _initialized
    if _initialized:
        return _langfuse_client

    _initialized = True
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        logger.info("langfuse_disabled", extra={"reason": "no keys configured"})
        return None

    try:
        from langfuse import Langfuse

        host = settings.langfuse_base_url or settings.langfuse_host
        _langfuse_client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=host,
        )
        logger.info("langfuse_initialized", extra={"host": host})
        return _langfuse_client
    except Exception as exc:
        logger.warning("langfuse_init_failed", extra={"error": str(exc)})
        return None


class TraceContext:
    """Wrapper around a Langfuse trace that no-ops when Langfuse is unavailable."""

    def __init__(self, trace: Any = None):
        self._trace = trace

    def span(self, name: str, **kwargs: Any) -> SpanContext:
        if self._trace is None:
            return SpanContext(None)
        try:
            span = self._trace.span(name=name, **kwargs)
            return SpanContext(span)
        except Exception:
            return SpanContext(None)

    def update(self, **kwargs: Any) -> None:
        if self._trace is None:
            return
        with suppress(Exception):
            self._trace.update(**kwargs)

    def generation(self, name: str, **kwargs: Any) -> Any:
        if self._trace is None:
            return _NoOpGeneration()
        try:
            return self._trace.generation(name=name, **kwargs)
        except Exception:
            return _NoOpGeneration()


class SpanContext:
    """Wrapper around a Langfuse span."""

    def __init__(self, span: Any = None):
        self._span = span

    def update(self, **kwargs: Any) -> None:
        if self._span is None:
            return
        with suppress(Exception):
            self._span.update(**kwargs)

    def end(self) -> None:
        if self._span is None:
            return
        with suppress(Exception):
            self._span.end()


class _NoOpGeneration:
    def update(self, **kwargs: Any) -> None:
        pass

    def end(self) -> None:
        pass


def create_trace(
    name: str = "agent_run",
    session_id: str | None = None,
    user_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> TraceContext:
    """Create a new Langfuse trace for an agent run."""
    client = _ensure_langfuse()
    if client is None:
        return TraceContext(None)

    try:
        trace = client.trace(
            name=name,
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {},
        )
        return TraceContext(trace)
    except Exception as exc:
        logger.warning("langfuse_trace_failed", extra={"error": str(exc)})
        return TraceContext(None)


def log_tool_call(
    trace: TraceContext,
    tool_name: str,
    tool_args: dict[str, Any],
    result_success: bool,
    duration_ms: float,
    error: str | None = None,
) -> None:
    """Log a tool call as a span on the trace."""
    span = trace.span(
        name=f"tool:{tool_name}",
        input=tool_args,
    )
    span.update(
        output={"success": result_success, "error": error},
        metadata={"duration_ms": duration_ms},
    )
    span.end()


def log_llm_call(
    trace: TraceContext,
    model: str,
    input_messages: list[dict[str, str]],
    output: str,
    usage: dict[str, int] | None = None,
    duration_ms: float = 0,
) -> None:
    """Log an LLM call as a generation on the trace."""
    gen = trace.generation(
        name="llm_call",
        model=model,
        input=input_messages,
        output=output,
        usage=usage,
        metadata={"duration_ms": duration_ms},
    )
    gen.end()


def log_verification(
    trace: TraceContext,
    verification: dict[str, Any],
    confidence: float,
) -> None:
    """Log verification results on the trace."""
    span = trace.span(name="verification")
    span.update(
        output=verification,
        metadata={"confidence": confidence},
    )
    span.end()


@contextmanager
def timed() -> Generator[dict[str, float], None, None]:
    """Context manager to measure elapsed time in milliseconds."""
    timing: dict[str, float] = {"start": time.monotonic(), "elapsed_ms": 0}
    try:
        yield timing
    finally:
        timing["elapsed_ms"] = (time.monotonic() - timing["start"]) * 1000


def flush() -> None:
    """Flush any pending Langfuse events."""
    client = _ensure_langfuse()
    if client is not None:
        with suppress(Exception):
            client.flush()
