"""ADK function tools for the flowchart assessment agent."""

from __future__ import annotations

import json
from google.adk.tools import ToolContext

from flowchart_agent.flowchart.navigator import find_next_unanswered, is_complete
from flowchart_agent.database.models import (
    save_answer as db_save_answer,
    load_answers as db_load_answers,
    clear_answers as db_clear_answers,
)


async def get_next_question(tool_context: ToolContext) -> dict:
    """Get the next unanswered question in the flowchart assessment.

    Call this tool to determine which question to ask the user next.
    It automatically skips questions the user has already answered
    and follows the correct branch based on previous answers.

    Returns a dict with question details or a completion message.
    """
    graph = tool_context.state.get("app:flowchart_graph")
    if not graph:
        return {"error": "Flowchart not initialized. Please try again."}

    answers = tool_context.state.get("answers", {})

    if is_complete(graph, answers):
        return {
            "status": "complete",
            "message": "The assessment is complete! All questions have been answered.",
            "total_answered": len(answers),
        }

    next_node = find_next_unanswered(graph, answers)
    if next_node is None:
        return {
            "status": "complete",
            "message": "The assessment is complete!",
            "total_answered": len(answers),
        }

    # Count total reachable questions for progress
    total_questions = sum(
        1 for n in graph["nodes"].values() if n["type"] == "question"
    )

    return {
        "status": "in_progress",
        "question_id": next_node["id"],
        "question_text": next_node["text"],
        "question_type": next_node["question_type"],
        "choices": next_node.get("choices", []),
        "answered_so_far": len(answers),
        "total_questions": total_questions,
    }


async def save_user_answer(
    question_id: str, answer: str, tool_context: ToolContext
) -> dict:
    """Save the user's answer to a specific question.

    Args:
        question_id: The ID of the question being answered (e.g. "Q1", "Q5").
        answer: The user's answer text.

    Persists the answer to session state and SQLite database.
    """
    graph = tool_context.state.get("app:flowchart_graph")
    if not graph:
        return {"error": "Flowchart not initialized."}

    if question_id not in graph["nodes"]:
        return {"error": f"Unknown question ID: {question_id}"}

    # Update session state
    answers = dict(tool_context.state.get("answers", {}))
    answers[question_id] = answer
    tool_context.state["answers"] = answers

    # Persist to SQLite
    user_id = tool_context.state.get("user_id", "default_user")
    await db_save_answer(user_id, question_id, answer)

    node = graph["nodes"][question_id]
    return {
        "status": "saved",
        "question_id": question_id,
        "question_text": node["text"],
        "answer": answer,
    }


async def load_user_history(tool_context: ToolContext) -> dict:
    """Load the user's previously saved answers from the database.

    Call this at the start of a conversation to restore any answers
    the user has already provided in past sessions. This allows the
    assessment to resume where they left off.
    """
    user_id = tool_context.state.get("user_id", "default_user")
    saved_answers = await db_load_answers(user_id)

    if saved_answers:
        # Merge into session state
        current = dict(tool_context.state.get("answers", {}))
        current.update(saved_answers)
        tool_context.state["answers"] = current

    return {
        "status": "loaded",
        "restored_count": len(saved_answers),
        "questions_answered": list(saved_answers.keys()),
    }


async def load_prefilled_answers(
    prefilled_data: str, tool_context: ToolContext
) -> dict:
    """Load pre-known answers to skip questions the system already knows.

    Args:
        prefilled_data: A JSON string of question_id to answer mappings,
                        e.g. '{"Q1": "John Doe", "Q2": "35"}'

    This lets you inject answers from external systems (EHR, CRM, etc.)
    so the user isn't asked questions with known answers.
    """
    try:
        data = json.loads(prefilled_data)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format for prefilled_data."}

    graph = tool_context.state.get("app:flowchart_graph")
    if not graph:
        return {"error": "Flowchart not initialized."}

    answers = dict(tool_context.state.get("answers", {}))
    loaded = []
    for qid, ans in data.items():
        if qid in graph["nodes"]:
            answers[qid] = str(ans)
            loaded.append(qid)

    tool_context.state["answers"] = answers

    # Also persist to DB
    user_id = tool_context.state.get("user_id", "default_user")
    for qid in loaded:
        await db_save_answer(user_id, qid, answers[qid])

    return {
        "status": "prefilled",
        "loaded_count": len(loaded),
        "loaded_questions": loaded,
    }


async def check_assessment_status(tool_context: ToolContext) -> dict:
    """Check the current progress of the assessment.

    Returns a summary of answered and remaining questions,
    along with the answers provided so far.
    """
    graph = tool_context.state.get("app:flowchart_graph")
    if not graph:
        return {"error": "Flowchart not initialized."}

    answers = tool_context.state.get("answers", {})
    total_questions = sum(
        1 for n in graph["nodes"].values() if n["type"] == "question"
    )
    complete = is_complete(graph, answers)

    # Build a readable summary of answers
    answer_summary = {}
    for qid, ans in answers.items():
        node = graph["nodes"].get(qid)
        if node:
            answer_summary[qid] = {
                "question": node["text"],
                "answer": ans,
            }

    return {
        "status": "complete" if complete else "in_progress",
        "answered": len(answers),
        "total_questions": total_questions,
        "is_complete": complete,
        "answers": answer_summary,
    }


async def restart_assessment(tool_context: ToolContext) -> dict:
    """Restart the assessment from the beginning.

    Clears all saved answers from both session state and the database.
    The user will be asked all questions again from the start.
    """
    user_id = tool_context.state.get("user_id", "default_user")

    # Clear session state
    tool_context.state["answers"] = {}

    # Clear database
    await db_clear_answers(user_id)

    return {
        "status": "restarted",
        "message": "Assessment has been restarted. All previous answers have been cleared.",
    }
