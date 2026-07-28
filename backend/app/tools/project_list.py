from typing import Any

from app.core.project_registry import list_enabled_projects


def list_projects() -> dict[str, Any]:
    projects = list_enabled_projects()

    return {
        "success": True,
        "count": len(projects),
        "projects": [
            {
                "id": project.id,
                "name": project.name,
                "environment": project.environment,
                "repository": project.repository,
                "has_local_repository": (
                    project.local_path is not None
                ),
                "has_health_check": (
                    project.health_url is not None
                ),
            }
            for project in projects
        ],
        "message": (
            f"Retrieved {len(projects)} registered projects."
        ),
    }