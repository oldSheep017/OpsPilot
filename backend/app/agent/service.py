import json
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


def find_tool_call(
    messages: list[Any],
    tool_call_id: str,
) -> dict[str, Any] | None:
    for message in messages:
        if not isinstance(message, AIMessage):
            continue

        for tool_call in message.tool_calls:
            if tool_call.get("id") == tool_call_id:
                return tool_call

    return None


def parse_tool_result(content: Any) -> dict[str, Any]:
    if isinstance(content, dict):
        return content

    if isinstance(content, str):
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return {"content": content}

        return parsed if isinstance(parsed, dict) else {"value": parsed}

    if isinstance(content, list):
        return {"content": content}

    return {"content": str(content)}


def collect_tool_executions(
    messages: list[Any],
) -> list[ToolExecutionRecord]:
    records: list[ToolExecutionRecord] = []

    for message in messages:
        if not isinstance(message, ToolMessage):
            continue

        tool_call = find_tool_call(
            messages=messages,
            tool_call_id=message.tool_call_id,
        )

        arguments = tool_call.get("args", {}) if tool_call else {}
        tool_name = (
            tool_call.get("name", "unknown_tool")
            if tool_call
            else message.name or "unknown_tool"
        )

        records.append(
            ToolExecutionRecord(
                tool_call_id=message.tool_call_id,
                tool_name=tool_name,
                arguments=arguments,
                result=parse_tool_result(message.content),
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
