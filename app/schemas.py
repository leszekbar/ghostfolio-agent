from typing import Any, Literal

from pydantic import BaseModel, Field


DataSource = Literal["ghostfolio_api", "mock"]


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
