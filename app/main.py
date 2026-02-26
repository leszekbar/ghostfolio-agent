from collections import defaultdict

from fastapi import FastAPI

from app.agent import run_agent
from app.config import settings
from app.ghostfolio_client import GhostfolioClient
from app.schemas import ChatRequest, ChatResponse
from app.tools import ToolContext

app = FastAPI(title="Ghostfolio Agent", version="0.1.0")

# P0 in-memory session memory for follow-up questions.
SESSION_STORE: dict[str, list[dict[str, str]]] = defaultdict(list)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    session_history = SESSION_STORE[request.session_id]
    data_source = request.data_source or settings.default_data_source

    tool_context = ToolContext(
        data_source=data_source,
        client=GhostfolioClient(
            base_url=settings.ghostfolio_base_url,
            token=settings.ghostfolio_token,
            timeout_seconds=settings.request_timeout_seconds,
        ),
    )

    result = await run_agent(
        query=request.message,
        session_history=session_history,
        tool_context=tool_context,
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
