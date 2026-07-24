# 定义模型能够理解的工具Schema
import json
from collections.abc import Callable
from typing import Any

from pydantic import ValidationError

from app.tools.project_status import (
    ProjectStatusInput,
    get_project_status,
)


GET_PROJECT_STATUS_TOOL = {
    "type": "function",
    "function": {
        "name": "get_project_status",
        "description": (
            "Retrieve the current known status, Git branch, and repository "
            "of a project. Use this tool when the user asks whether a "
            "specific project is running, stopped, available, or deployed."
        ),
        "parameters": ProjectStatusInput.model_json_schema(),
    },
}


MODEL_TOOLS = [
    GET_PROJECT_STATUS_TOOL,
]


def execute_tool(
    tool_name: str,
    raw_arguments: str,
) -> dict[str, Any]:
    try:
        arguments = json.loads(raw_arguments)
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "invalid_json_arguments",
            "message": "The model returned invalid JSON arguments.",
        }

    try:
        if tool_name == "get_project_status":
            validated_input = ProjectStatusInput.model_validate(arguments)
            result = get_project_status(validated_input)
            return result.model_dump()

        return {
            "success": False,
            "error": "unknown_tool",
            "message": f"Unknown tool: {tool_name}",
        }

    except ValidationError as error:
        return {
            "success": False,
            "error": "invalid_tool_arguments",
            "message": "Tool arguments failed validation.",
            "details": error.errors(
                include_url=False,
                include_input=False,
            ),
        }

    except Exception:
        return {
            "success": False,
            "error": "tool_execution_failed",
            "message": "The tool failed during execution.",
        }