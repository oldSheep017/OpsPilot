from typing import Literal

from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from app.agent.state import OpsPilotState
from app.config import get_settings
from app.tools.langchain_tools import TOOLS

AGENT_SYSTEM_PROMPT = """
You are OpsPilot, an AI operations assistant for developers.

Available capabilities:
- List projects registered in OpsPilot.
- Read stored project status information.
- Inspect real local Git repository information.
- Perform live HTTP health checks.

Tool selection rules:
1. Use query_registered_projects when the user asks which projects exist.
2. Use query_git_info for branches, commits, remote URLs, or local changes.
3. Use query_http_health for website availability or live HTTP status.
4. Use query_project_status only for stored project information.
5. When the user requests a complete project check, use both Git and HTTP
   tools when their results are relevant.
6. Never claim that a tool was executed unless its result exists.
7. Never invent project data, Git data, HTTP status, or response time.
8. Clearly distinguish stored information from live inspection results.
9. If a tool reports missing configuration, explain what is missing.
10. Stop calling tools once enough information is available.

Answer rules:
- Give the conclusion first.
- Mention which checks were performed.
- Clearly identify failed or unavailable checks.
- Keep general explanations concise.
- Always reply me in Chinese.
""".strip()


MAX_LLM_CALLS = 3


def create_chat_model() -> ChatOpenAI:
    settings = get_settings()

    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=0,
        timeout=60,
        max_retries=2,
    )


model = create_chat_model()
model_with_tools = model.bind_tools(TOOLS)

tool_node = ToolNode(
    TOOLS,
    handle_tool_errors=True,
)


def call_model(state: OpsPilotState) -> dict:
    response = model_with_tools.invoke(
        [
            SystemMessage(
                content=AGENT_SYSTEM_PROMPT,
            ),
            *state["messages"],
        ]
    )

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def route_after_model(
    state: OpsPilotState,
) -> Literal["tools", "limit_reached", "__end__"]:
    last_message = state["messages"][-1]

    if not getattr(last_message, "tool_calls", None):
        return "__end__"

    if state.get("llm_calls", 0) >= MAX_LLM_CALLS:
        return "limit_reached"

    return "tools"


def handle_limit_reached(
    state: OpsPilotState,
) -> dict:
    return {
        "messages": [
            AIMessage(
                content=(
                    "The agent stopped because it reached the maximum "
                    "number of model execution steps."
                )
            )
        ]
    }


builder = StateGraph(OpsPilotState)

builder.add_node(
    "agent",
    call_model,
)

builder.add_node(
    "tools",
    tool_node,
)

builder.add_node(
    "limit_reached",
    handle_limit_reached,
)

builder.add_edge(
    START,
    "agent",
)

builder.add_conditional_edges(
    "agent",
    route_after_model,
    {
        "tools": "tools",
        "limit_reached": "limit_reached",
        "__end__": END,
    },
)

builder.add_edge(
    "tools",
    "agent",
)

builder.add_edge(
    "limit_reached",
    END,
)

opspilot_graph = builder.compile()