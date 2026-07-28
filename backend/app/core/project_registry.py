import json
from functools import lru_cache
from pathlib import Path

from app.schemas.project import ProjectConfig

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_CONFIG_PATH = BACKEND_ROOT / "data" / "projects.json"

class ProjectRegistryError(RuntimeError):
  pass

@lru_cache
def load_projects() -> tuple[ProjectConfig, ...]:
  try:
    raw_content = PROJECT_CONFIG_PATH.read_text(
      encoding="utf-8",
    )
    raw_projects = json.loads(raw_content)
  except FileNotFoundError as error:
      raise ProjectRegistryError(
          "Project configuration file was not found."
      ) from error
  except json.JSONDecodeError as error:
      raise ProjectRegistryError(
          "Project configuration contains invalid JSON."
      ) from error
  projects = tuple(
      ProjectConfig.model_validate(item)
      for item in raw_projects
  )
  return projects

def list_enabled_projects() -> list[ProjectConfig]:
    return [
        project
        for project in load_projects()
        if project.enabled
    ]


def find_project(
    project_query: str,
) -> ProjectConfig | None:
    normalized_query = project_query.strip().lower()

    if not normalized_query:
        return None

    projects = list_enabled_projects()

    # 第一轮：精确匹配
    for project in projects:
        candidates = [
            project.id,
            project.name,
            *project.aliases,
        ]

        if any(
            normalized_query == candidate.lower()
            for candidate in candidates
        ):
            return project

    # 第二轮：包含匹配
    for project in projects:
        candidates = [
            project.id,
            project.name,
            *project.aliases,
        ]

        if any(
            normalized_query in candidate.lower()
            or candidate.lower() in normalized_query
            for candidate in candidates
        ):
            return project

    return None