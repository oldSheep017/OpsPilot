import subprocess
from pathlib import Path
from typing import Any

from app.core.project_registry import (
    BACKEND_ROOT,
    find_project,
)


GIT_COMMAND_TIMEOUT_SECONDS = 5


def resolve_project_path(
    configured_path: str,
) -> Path:
    path = (BACKEND_ROOT / configured_path).resolve()

    allowed_root = BACKEND_ROOT.parent.resolve()

    try:
        path.relative_to(allowed_root)
    except ValueError as error:
        raise ValueError(
            "The configured project path is outside the allowed root."
        ) from error

    return path


def run_git_command(
    repository_path: Path,
    arguments: list[str],
) -> str:
    completed_process = subprocess.run(
        ["git", "-C", str(repository_path), *arguments],
        capture_output=True,
        text=True,
        timeout=GIT_COMMAND_TIMEOUT_SECONDS,
        check=False,
    )

    if completed_process.returncode != 0:
        error_message = (
            completed_process.stderr.strip()
            or "Git command failed."
        )

        raise RuntimeError(error_message)

    return completed_process.stdout.strip()


def get_git_info(
    project_name: str,
) -> dict[str, Any]:
    project = find_project(project_name)

    if project is None:
        return {
            "success": False,
            "error": "project_not_found",
            "project_query": project_name,
            "message": "The requested project was not found.",
        }

    if project.local_path is None:
        return {
            "success": False,
            "error": "local_path_not_configured",
            "project_id": project.id,
            "project_name": project.name,
            "message": (
                "No local repository path is configured "
                "for this project."
            ),
        }

    try:
        repository_path = resolve_project_path(
            project.local_path,
        )
    except ValueError:
        return {
            "success": False,
            "error": "path_not_allowed",
            "project_id": project.id,
            "project_name": project.name,
            "message": (
                "The project path is outside the allowed root."
            ),
        }

    if not repository_path.exists():
        return {
            "success": False,
            "error": "repository_path_not_found",
            "project_id": project.id,
            "project_name": project.name,
            "message": "The configured repository path does not exist.",
        }

    if not (repository_path / ".git").exists():
        return {
            "success": False,
            "error": "not_a_git_repository",
            "project_id": project.id,
            "project_name": project.name,
            "message": (
                "The configured path is not a Git repository."
            ),
        }

    try:
        branch = run_git_command(
            repository_path,
            ["branch", "--show-current"],
        )

        commit_hash = run_git_command(
            repository_path,
            ["rev-parse", "--short", "HEAD"],
        )

        commit_message = run_git_command(
            repository_path,
            ["log", "-1", "--pretty=%s"],
        )

        commit_author = run_git_command(
            repository_path,
            ["log", "-1", "--pretty=%an"],
        )

        commit_time = run_git_command(
            repository_path,
            ["log", "-1", "--pretty=%cI"],
        )

        working_tree_status = run_git_command(
            repository_path,
            ["status", "--porcelain"],
        )

        remote_url = run_git_command(
            repository_path,
            ["remote", "get-url", "origin"],
        )

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "git_command_timeout",
            "project_id": project.id,
            "project_name": project.name,
            "message": "The Git command timed out.",
        }

    except RuntimeError as error:
        return {
            "success": False,
            "error": "git_command_failed",
            "project_id": project.id,
            "project_name": project.name,
            "message": str(error),
        }

    return {
        "success": True,
        "project_id": project.id,
        "project_name": project.name,
        "repository_path": str(repository_path),
        "branch": branch or None,
        "commit": {
            "hash": commit_hash,
            "message": commit_message,
            "author": commit_author,
            "committed_at": commit_time,
        },
        "remote_url": remote_url,
        "working_tree_clean": not bool(
            working_tree_status
        ),
        "changed_file_count": len(
            working_tree_status.splitlines()
        ),
        "message": "Git information retrieved successfully.",
    }