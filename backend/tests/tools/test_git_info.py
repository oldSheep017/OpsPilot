from app.tools.git_info import get_git_info


def test_get_git_info_returns_not_found() -> None:
    result = get_git_info("project-that-does-not-exist")

    assert result["success"] is False
    assert result["error"] == "project_not_found"
