from langchain_core.messages import AIMessage, ToolMessage

from app.agent.service import collect_tool_executions


def test_collect_tool_executions_parses_json_and_recovers_tool_name() -> None:
    messages = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "query_http_health",
                    "args": {"project_name": "OpsPilot"},
                    "id": "call_1",
                    "type": "tool_call",
                }
            ],
        ),
        ToolMessage(
            content='{"success": true, "healthy": true}',
            tool_call_id="call_1",
            name="query_http_health",
        ),
    ]

    records = collect_tool_executions(messages)

    assert records[0].tool_name == "query_http_health"
    assert records[0].arguments == {"project_name": "OpsPilot"}
    assert records[0].result == {"success": True, "healthy": True}
