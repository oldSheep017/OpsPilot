from typing import Any

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    ToolMessage,
)

from app.agent.graph import opspilot_graph
from app.schemas.agent import (
    AgentChatResponse,
    ToolExecutionRecord,
)


def find_tool_arguments(
    messages: list[Any],
    tool_call_id: str,
) -> dict[str, Any]:
    for message in messages:
        if not isinstance(message, AIMessage):
            continue

        for tool_call in message.tool_calls:
            if tool_call["id"] == tool_call_id:
                return tool_call.get("args", {})

    return {}


def collect_tool_executions(
    messages: list[Any],
) -> list[ToolExecutionRecord]:
    records: list[ToolExecutionRecord] = []

    for message in messages:
        if not isinstance(message, ToolMessage):
            continue

        arguments = find_tool_arguments(
            messages=messages,
            tool_call_id=message.tool_call_id,
        )

        result: dict[str, Any]

        if isinstance(message.content, dict):
            result = message.content
        else:
            result = {
                "content": message.content,
            }

        records.append(
            ToolExecutionRecord(
                tool_call_id=message.tool_call_id,
                tool_name=message.name or "unknown_tool",
                arguments=arguments,
                result=result,
            )
        )

    return records


async def run_agent(
    user_message: str,
) -> AgentChatResponse:
    result = await opspilot_graph.ainvoke(
        {
            "messages": [
                HumanMessage(
                    content=user_message,
                )
            ],
            "llm_calls": 0,
        }
    )

    messages = result["messages"]
    last_message = messages[-1]

    if isinstance(last_message, AIMessage):
        answer = (
            last_message.content
            if isinstance(last_message.content, str)
            else str(last_message.content)
        )
    else:
        answer = "The agent did not return a final response."

    tool_executions = collect_tool_executions(messages)

    reached_limit = (
        "maximum number of model execution steps"
        in answer.lower()
    )

    return AgentChatResponse(
        answer=answer,
        finish_reason=(
            "max_steps_reached"
            if reached_limit
            else "completed"
        ),
        tool_executions=tool_executions,
    )