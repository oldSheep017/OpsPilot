import time
from typing import Any

import httpx

from app.core.project_registry import find_project


HTTP_TIMEOUT_SECONDS = 5.0
MAX_RESPONSE_PREVIEW_LENGTH = 200


async def check_http_health(
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

    if project.health_url is None:
        return {
            "success": False,
            "error": "health_url_not_configured",
            "project_id": project.id,
            "project_name": project.name,
            "message": (
                "No health check URL is configured "
                "for this project."
            ),
        }

    url = str(project.health_url)
    started_at = time.perf_counter()

    try:
        async with httpx.AsyncClient(
            timeout=HTTP_TIMEOUT_SECONDS,
            follow_redirects=True,
        ) as client:
            response = await client.get(url)

    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "http_timeout",
            "project_id": project.id,
            "project_name": project.name,
            "url": url,
            "healthy": False,
            "message": "The health check request timed out.",
        }

    except httpx.RequestError as error:
        return {
            "success": False,
            "error": "http_request_failed",
            "project_id": project.id,
            "project_name": project.name,
            "url": url,
            "healthy": False,
            "message": (
                f"Unable to reach the health check URL: "
                f"{type(error).__name__}."
            ),
        }

    elapsed_ms = round(
        (time.perf_counter() - started_at) * 1000,
        2,
    )

    healthy = 200 <= response.status_code < 400

    content_type = response.headers.get(
        "content-type",
        "",
    )

    response_preview: str | None = None

    if (
        "text/" in content_type
        or "application/json" in content_type
    ):
        response_preview = response.text[
            :MAX_RESPONSE_PREVIEW_LENGTH
        ]

    return {
        "success": True,
        "project_id": project.id,
        "project_name": project.name,
        "url": str(response.url),
        "healthy": healthy,
        "status_code": response.status_code,
        "response_time_ms": elapsed_ms,
        "content_type": content_type,
        "response_preview": response_preview,
        "message": (
            "The project passed the HTTP health check."
            if healthy
            else "The project failed the HTTP health check."
        ),
    }