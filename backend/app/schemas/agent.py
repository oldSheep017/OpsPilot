from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=4000,
        description="The user's message.",
    )


class ToolExecutionRecord(BaseModel):
    tool_call_id: str
    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any]


class AgentChatResponse(BaseModel):
    answer: str
    finish_reason: Literal[
        "completed",
        "max_steps_reached",
        "model_error",
    ]
    tool_executions: list[ToolExecutionRecord]