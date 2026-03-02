from collections import defaultdict

from fastapi import FastAPI, HTTPException

from app.agent import run_agent
from app.config import settings
from app.data_sources import build_provider
from app.data_sources.ghostfolio_api_provider import GhostfolioAPIDataProvider
from app.ghostfolio_client import GhostfolioClient
from app.llm import get_active_model_name
from app.schemas import (
    DATA_SOURCE_GHOSTFOLIO_API,
    ChatRequest,
    ChatResponse,
    SessionStartRequest,
    SessionStartResponse,
)
from app.telemetry import configure_logging, get_logger
from app.tools import ToolContext

configure_logging(
    level=settings.log_level,
    log_format=settings.log_format,
    include_stack=settings.log_include_stack,
    redact_fields_raw=settings.log_redact_fields,
)
logger = get_logger(__name__)

app = FastAPI(title="Ghostfolio Agent", version="0.1.0")

# P0 in-memory session memory for follow-up questions.
SESSION_STORE: dict[str, list[dict[str, str]]] = defaultdict(list)
SESSION_TOKENS: dict[str, str] = {}


@app.get("/health")
async def health() -> dict[str, str]:
    logger.debug("health_check", extra={"data_source": settings.default_data_source})

    return {
        "status": "ok",
        "data_source": settings.default_data_source,
        "ghostfolio_url": settings.ghostfolio_base_url,
        "llm_model": get_active_model_name(),
    }


@app.post("/session/start", response_model=SessionStartResponse)
async def session_start(request: SessionStartRequest) -> SessionStartResponse:
    logger.info("session_start_requested", extra={"session_id": request.session_id})
    if settings.default_data_source == DATA_SOURCE_GHOSTFOLIO_API:
        security_token = (request.access_token or request.ghostfolio_token or "").strip()
        if not security_token:
            raise HTTPException(
                status_code=400,
                detail="access_token is required when server data source is ghostfolio_api",
            )
        try:
            auth_token = await GhostfolioClient(
                base_url=settings.ghostfolio_base_url,
                token=None,
                timeout_seconds=settings.request_timeout_seconds,
            ).exchange_access_token_for_auth_token(security_token)
        except Exception as exc:
            logger.warning(
                "session_start_auth_failed",
                extra={"session_id": request.session_id, "error": str(exc)},
            )
            raise HTTPException(status_code=401, detail=f"Failed to authenticate session: {exc}") from exc

        SESSION_TOKENS[request.session_id] = auth_token
        logger.info("session_start_connected", extra={"session_id": request.session_id})
        return SessionStartResponse(
            session_id=request.session_id,
            connected=True,
            data_source=settings.default_data_source,
        )

    # In mock mode no token is required.
    return SessionStartResponse(
        session_id=request.session_id,
        connected=True,
        data_source=settings.default_data_source,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    session_history = SESSION_STORE[request.session_id]
    logger.info("chat_requested", extra={"session_id": request.session_id})
    # Data source is server-owned configuration, not client-controlled input.
    data_source = settings.default_data_source
    session_token = SESSION_TOKENS.get(request.session_id)
    if data_source == DATA_SOURCE_GHOSTFOLIO_API and not session_token:
        raise HTTPException(
            status_code=401,
            detail="Session is not connected. Call /session/start with access_token first.",
        )
    api_provider = GhostfolioAPIDataProvider(
        GhostfolioClient(
            base_url=settings.ghostfolio_base_url,
            token=session_token,
            timeout_seconds=settings.request_timeout_seconds,
        )
    )

    tool_context = ToolContext(
        provider=build_provider(data_source, api_provider),
    )

    result = await run_agent(
        query=request.message,
        session_history=session_history,
        tool_context=tool_context,
        session_id=request.session_id,
    )
    logger.info(
        "chat_completed",
        extra={
            "session_id": request.session_id,
            "tool_calls": result["tool_calls"],
            "confidence": result["confidence"],
        },
    )

    session_history.append({"role": "user", "content": request.message})
    session_history.append(
        {
            "role": "assistant",
            "content": result["response"],
            "tool": result["selected_tool"],
        }
    )

    return ChatResponse(
        session_id=request.session_id,
        response=result["response"],
        tool_calls=result["tool_calls"],
        confidence=result["confidence"],
        verification=result["verification"],
    )
