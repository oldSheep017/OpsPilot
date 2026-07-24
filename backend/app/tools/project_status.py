from typing import Literal

from pydantic import BaseModel, Field

ProjectStatusValue = Literal["running", "stopped", "unknown"]

class ProjectStatusInput(BaseModel):
  project_name: str = Field(
    min_length=1,
    max_length=100,
    description="The exact or approximate name of the project."
  )

class ProjectStatusResult(BaseModel):
  success: bool
  project_name: str
  status: ProjectStatusValue | None = None
  branch: str | None = None
  repository: str | None = None
  message: str

PROJECTS: list[dict[str, str]] = [
    {
        "name": "OpsPilot Frontend",
        "status": "running",
        "branch": "main",
        "repository": "https://github.com/oldSheep017/opspilot",
    },
    {
        "name": "Demo Service",
        "status": "stopped",
        "branch": "develop",
        "repository": "https://github.com/oldSheep017/demo-service",
    },
]


def get_project_status(input_data: ProjectStatusInput,
) -> ProjectStatusResult:
  normalized_name = input_data.project_name.strip().lower()

  for project in PROJECTS:
    project_name = project["name"]

    if normalized_name in project_name.lower():
      return ProjectStatusResult(
        success=True,
        project_name=project_name,
        status=project["status"],
        branch=project["branch"],
        repository=project["repository"],
        message="Project status retrieved successfully."
      )

  return ProjectStatusResult(
    success=False,
    project_name=input_data.project_name,
    message="The requested project was not found."
  )

