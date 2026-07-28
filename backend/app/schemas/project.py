from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


Environment = Literal[
    "development",
    "test",
    "staging",
    "production",
]
ProjectStatus = Literal["running", "stopped", "unknown"]


class ProjectConfig(BaseModel):
    id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9][a-z0-9-_]*$",
    )
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    aliases: list[str] = Field(default_factory=list)
    repository: str | None = None
    local_path: str | None = None
    health_url: HttpUrl | None = None
    environment: Environment
    status: ProjectStatus = "unknown"
    enabled: bool = True
