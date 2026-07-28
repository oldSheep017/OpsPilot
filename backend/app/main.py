from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agent.service import run_agent
from app.core.project_registry import list_enabled_projects
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.schemas.chat import ChatRequest
from app.services.llm import stream_chat_response


class Project(BaseModel):
    id: str
    name: str
    status: str
    repository: str | None
    branch: str | None = None


app = FastAPI(
    title="OpsPilot API",
    description="Backend API for the OpsPilot AI operations agent.",
    version="0.5.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": "OpsPilot API", "status": "running"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/api/projects", response_model=list[Project])
async def list_projects() -> list[Project]:
    return [
        Project(
            id=project.id,
            name=project.name,
            status=project.status,
            repository=project.repository,
        )
        for project in list_enabled_projects()
    ]


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        stream_chat_response(request.message),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.post("/api/agent/chat", response_model=AgentChatResponse)
async def agent_chat(request: AgentChatRequest) -> AgentChatResponse:
    return await run_agent(request.message)
