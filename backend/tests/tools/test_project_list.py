from app.tools.project_list import list_projects


def test_list_projects_returns_registered_projects() -> None:
    result = list_projects()

    assert result["success"] is True
    assert result["count"] >= 1
    assert isinstance(result["projects"], list)
