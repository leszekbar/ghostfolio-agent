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
    data_source: DataSource | None = None


class ChatResponse(BaseModel):
    session_id: str
    response: str
    tool_calls: list[str]
    confidence: float
    verification: dict[str, Any]
