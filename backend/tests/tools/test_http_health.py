import pytest

from app.tools.http_health import check_http_health


@pytest.mark.asyncio
async def test_health_check_without_url() -> None:
    result = await check_http_health("Demo Service")

    assert result["success"] is False
    assert result["error"] == "health_url_not_configured"
