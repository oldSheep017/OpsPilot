from typing import Any

from langchain_core.tools import tool

from app.tools.project_status import (
  ProjectStatusInput,
  get_project_status,
)


@tool(args_schema=ProjectStatusInput)
def query_project_status(project_name: str) -> dict[str, Any]:
  """
  Retrive the known status, Git branch, and repository of a project.

  Use this tool when the user asks whether a specific project is running, stopped, available, or deployed. It can also be used when the user asks for the project's Git branch or repository.
  """

  result = get_project_status(
    ProjectStatusInput(
      project_name=project_name,
    )
  )

  return result.model_dump()


TOOLS = [
  query_project_status,
]