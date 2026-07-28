from typing import Any

from langchain.tools import tool
from pydantic import BaseModel, Field

from app.tools.git_info import get_git_info
from app.tools.http_health import check_http_health
from app.tools.project_list import list_projects
from app.tools.project_status import (
    ProjectStatusInput,
    get_project_status,
)


class ProjectQueryInput(BaseModel):
    project_name: str = Field(
        min_length=1,
        max_length=100,
        description=(
            "The project name, ID, or known alias. "
            "Use the user's original project wording."
        ),
    )


@tool
def query_registered_projects() -> dict[str, Any]:
    """
    List all projects registered in OpsPilot.

    Use this tool when the user asks which projects exist, which
    projects are managed, or requests an overview of available projects.
    """

    return list_projects()


@tool(args_schema=ProjectStatusInput)
def query_project_status(
    project_name: str,
) -> dict[str, Any]:
    """
    Retrieve the stored running status, Git branch, and repository
    information of a project.

    Use this when the user explicitly asks for the stored project status.
    Do not use it as a substitute for a live HTTP health check.
    """

    result = get_project_status(
        ProjectStatusInput(
            project_name=project_name,
        )
    )

    return result.model_dump()


@tool(args_schema=ProjectQueryInput)
def query_git_info(
    project_name: str,
) -> dict[str, Any]:
    """
    Inspect the real local Git repository of a project.

    Use this tool for questions about the current branch, latest commit,
    commit author, remote repository, uncommitted files, or working-tree
    cleanliness.
    """

    return get_git_info(project_name)


@tool(args_schema=ProjectQueryInput)
async def query_http_health(
    project_name: str,
) -> dict[str, Any]:
    """
    Perform a live HTTP request to check whether a project's configured
    website or health endpoint is reachable.

    Use this tool when the user asks whether a website is accessible,
    online, healthy, responding, or returning an HTTP error.
    """

    return await check_http_health(project_name)


TOOLS = [
    query_registered_projects,
    query_project_status,
    query_git_info,
    query_http_health,
]