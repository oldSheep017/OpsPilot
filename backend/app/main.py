from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest
from app.schemas.agent import (
  AgentChatRequest,
  AgentChatResponse,
)
from app.agent.service import run_agent
from app.services.llm import stream_chat_response

app = FastAPI(
  title="OpsPilot API",
  description="Backend API for the OpsPilot AI operations agent.",
  version="0.1.0",
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:5173"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"]
)


ProjectStatus = Literal["running", "stopped", "unknown"]


class Project(BaseModel):
  id: int
  name: str
  status: ProjectStatus
  repository: str
  branch: str


PROJECTS = [
  Project(
    id=1,
    name="OpsPilot Frontend",
    status="running",
    repository="https://github.com/oldSheep017/OpsPilot",
    branch="main"
  ),
  Project(
    id=2,
    name="Demo Service",
    status="stopped",
    repository="https://github.com/oldSheep017/demo-service",
    branch="develop"
  )
]

@app.get("/")
async def root() -> dict[str, str]:
  return {
    "name": "OpsPilot API",
    "status": "running"
  }

@app.get("/health")
async def health_check() -> dict[str, str]:
  return {
    "status": "healthy"
  }

@app.get("/api/projects", response_model=list[Project])
async def list_projects() -> list[Project]:
  return PROJECTS


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

@app.post(
    "/api/agent/chat",
    response_model=AgentChatResponse,
)
async def agent_chat(
    request: AgentChatRequest,
) -> AgentChatResponse:
    return await run_agent(request.message)