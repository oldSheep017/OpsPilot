import json
from typing import Any

from openai import OpenAI

from app.config import get_settings
from app.schemas.agent import (
    AgentChatResponse,
    ToolExecutionRecord,
)
from app.services.llm import create_llm_client
from app.tools.registry import MODEL_TOOLS, execute_tool


AGENT_SYSTEM_PROMPT = """
You are OpsPilot, an AI operations assistant for developers.

You have access to tools that provide project information.

Rules:
1. Use a tool whenever the user asks about the real or known status of a project.
2. Never invent a project status, Git branch, repository, process, container, or log.
3. If a tool reports that a project was not found, clearly tell the user.
4. For general software questions, answer directly without calling a tool.
5. Base operational claims only on tool results.
6. Keep the final answer concise and clearly explain what data was checked.
7. Reply me in Chinese.
""".strip()


MAX_AGENT_STEPS = 3


def serialize_assistant_message(
    message: Any,
) -> dict[str, Any]:
    serialized: dict[str, Any] = {
        "role": "assistant",
        "content": message.content,
    }

    if message.tool_calls:
        serialized["tool_calls"] = [
            {
                "id": tool_call.id,
                "type": tool_call.type,
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                },
            }
            for tool_call in message.tool_calls
        ]

    return serialized


def run_agent(user_message: str) -> AgentChatResponse:
    settings = get_settings()
    client: OpenAI = create_llm_client()

    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": AGENT_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]

    execution_records: list[ToolExecutionRecord] = []

    for _step in range(MAX_AGENT_STEPS):
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            tools=MODEL_TOOLS,
            tool_choice="auto",
        )

        assistant_message = response.choices[0].message
        messages.append(
            serialize_assistant_message(assistant_message)
        )

        if not assistant_message.tool_calls:
            return AgentChatResponse(
                answer=assistant_message.content
                or "The model returned an empty response.",
                finish_reason="completed",
                tool_executions=execution_records,
            )

        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            raw_arguments = tool_call.function.arguments

            try:
                parsed_arguments = json.loads(raw_arguments)
            except json.JSONDecodeError:
                parsed_arguments = {}

            result = execute_tool(
                tool_name=tool_name,
                raw_arguments=raw_arguments,
            )

            execution_records.append(
                ToolExecutionRecord(
                    tool_call_id=tool_call.id,
                    tool_name=tool_name,
                    arguments=parsed_arguments,
                    result=result,
                )
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(
                        result,
                        ensure_ascii=False,
                    ),
                }
            )

    return AgentChatResponse(
        answer=(
            "The agent reached the maximum number of execution steps "
            "before producing a final answer."
        ),
        finish_reason="max_steps_reached",
        tool_executions=execution_records,
    )