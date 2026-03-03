"""Root agent definition for the flowchart assessment agent."""

from __future__ import annotations

import asyncio
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from flowchart_agent.flowchart.parser import parse_mermaid_flowchart
from flowchart_agent.database.models import init_db
from flowchart_agent.prompt import SYSTEM_INSTRUCTION
from flowchart_agent.tools.flowchart_tools import (
    get_next_question,
    save_user_answer,
    load_user_history,
    load_prefilled_answers,
    check_assessment_status,
    restart_assessment,
)


def _before_agent(callback_context: CallbackContext) -> Optional[types.Content]:
    """Initialize flowchart graph and database on the first invocation."""
    # Only initialize once — check if graph is already in app state
    if callback_context.state.get("app:flowchart_graph") is not None:
        return None  # Already initialized, proceed normally

    # Parse the flowchart and store in app-scoped state
    graph = parse_mermaid_flowchart()
    callback_context.state["app:flowchart_graph"] = graph

    # Initialize answers dict if not present
    if callback_context.state.get("answers") is None:
        callback_context.state["answers"] = {}

    # Set a default user_id
    if callback_context.state.get("user_id") is None:
        callback_context.state["user_id"] = "default_user"

    # Initialize the database (fire-and-forget via event loop)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(init_db())
        else:
            loop.run_until_complete(init_db())
    except RuntimeError:
        asyncio.run(init_db())

    return None  # Proceed with normal agent execution


root_agent = LlmAgent(
    name="health_intake_agent",
    model="gemini-2.0-flash",
    instruction=SYSTEM_INSTRUCTION,
    description="A health assessment intake agent that follows a flowchart to ask questions.",
    tools=[
        get_next_question,
        save_user_answer,
        load_user_history,
        load_prefilled_answers,
        check_assessment_status,
        restart_assessment,
    ],
    before_agent_callback=_before_agent,
)
