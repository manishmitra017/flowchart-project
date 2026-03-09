"""Root agent definition for the flowchart multi-agent system."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from flowchart_agent.flowchart.parser import parse_mermaid_flowchart
from flowchart_agent.database.models import init_db
from flowchart_agent.prompt import (
    build_pa_instruction,
    build_question_tracker_instruction,
    build_validator_instruction,
)
from flowchart_agent.tools.flowchart_tools import (
    get_next_question,
    save_user_answer,
    save_multiple_answers,
    load_user_history,
    load_prefilled_answers,
    check_assessment_status,
    restart_assessment,
    get_current_question_details,
    get_all_questions,
)


def _before_agent(callback_context: CallbackContext) -> Optional[types.Content]:
    """Initialize flowchart graph and database on the first invocation."""
    # Only initialize once — check if graph is already in app state
    if callback_context.state.get("app:flowchart_graph") is not None:
        return None  # Already initialized, proceed normally

    # Load flowchart from FLOWCHART_PATH env var, or fall back to the bundled sample
    flowchart_path = os.environ.get("FLOWCHART_PATH")
    if flowchart_path:
        mermaid_text = Path(flowchart_path).read_text()
    else:
        mermaid_text = None  # parser falls back to sample_flowchart.md

    graph, metadata = parse_mermaid_flowchart(mermaid_text)
    callback_context.state["app:flowchart_graph"] = graph

    # Store metadata in app-scoped state for the instruction providers
    callback_context.state["app:flowchart_title"] = metadata.get(
        "title", "Questionnaire"
    )
    callback_context.state["app:agent_persona"] = metadata.get(
        "persona", "a friendly, professional assistant"
    )
    callback_context.state["app:domain"] = metadata.get(
        "domain", "questionnaire"
    )
    callback_context.state["app:tone_notes"] = metadata.get("tone_notes", "")
    callback_context.state["app:completion_message"] = metadata.get(
        "completion_message", "All questions have been answered."
    )

    # Derive a flowchart_id from the title for database namespacing
    title = callback_context.state["app:flowchart_title"]
    flowchart_id = title.lower().replace(" ", "_")
    callback_context.state["app:flowchart_id"] = flowchart_id

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


# --- Sub-agents ---

question_tracker_agent = LlmAgent(
    name="question_tracker_agent",
    model="gemini-2.5-flash",
    instruction=build_question_tracker_instruction,
    description="Determines and presents the next question in the flowchart. Transfer to this agent when it's time to ask the next question.",
    tools=[get_next_question],
)

answer_validator_agent = LlmAgent(
    name="answer_validator_agent",
    model="gemini-2.5-flash",
    instruction=build_validator_instruction,
    description="Validates the user's answer against the question type and saves it if valid. Transfer to this agent when the user provides an answer.",
    tools=[save_user_answer, save_multiple_answers, get_current_question_details, get_all_questions],
)


# --- Principal Agent (root) ---

root_agent = LlmAgent(
    name="flowchart_agent",
    model="gemini-2.5-flash",
    instruction=build_pa_instruction,
    description="A conversational agent that follows any Mermaid flowchart to ask questions using a multi-agent architecture.",
    tools=[
        load_user_history,
        load_prefilled_answers,
        check_assessment_status,
        restart_assessment,
    ],
    sub_agents=[question_tracker_agent, answer_validator_agent],
    before_agent_callback=_before_agent,
)
