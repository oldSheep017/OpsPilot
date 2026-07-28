from typing import Literal

from pydantic import BaseModel, Field

from app.core.project_registry import find_project


ProjectStatusValue = Literal["running", "stopped", "unknown"]


class ProjectStatusInput(BaseModel):
    project_name: str = Field(
        min_length=1,
        max_length=100,
        description="The exact or approximate name of the project.",
    )


class ProjectStatusResult(BaseModel):
    success: bool
    project_name: str
    status: ProjectStatusValue | None = None
    branch: str | None = None
    repository: str | None = None
    message: str


def get_project_status(
    input_data: ProjectStatusInput,
) -> ProjectStatusResult:
    project = find_project(input_data.project_name)

    if project is None:
        return ProjectStatusResult(
            success=False,
            project_name=input_data.project_name,
            message="The requested project was not found.",
        )

    return ProjectStatusResult(
        success=True,
        project_name=project.name,
        status=project.status,
        repository=project.repository,
        message="Stored project status retrieved successfully.",
    )
