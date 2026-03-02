from typing import Any, Literal

from pydantic import BaseModel, Field

DATA_SOURCE_GHOSTFOLIO_API = "ghostfolio_api"
DATA_SOURCE_MOCK = "mock"
DataSource = Literal[DATA_SOURCE_GHOSTFOLIO_API, DATA_SOURCE_MOCK]


class ToolError(BaseModel):
    code: str
    message: str


class ToolResult(BaseModel):
    success: bool
    data: dict[str, Any] | None = None
    error: ToolError | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str = "default"


class ChatResponse(BaseModel):
    session_id: str
    response: str
    tool_calls: list[str]
    confidence: float
    verification: dict[str, Any]


class SessionStartRequest(BaseModel):
    session_id: str = "default"
    access_token: str | None = None
    # Backward compatibility for earlier UI naming.
    ghostfolio_token: str | None = None


class SessionStartResponse(BaseModel):
    session_id: str
    connected: bool
    data_source: DataSource
