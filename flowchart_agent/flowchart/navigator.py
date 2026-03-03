"""Graph traversal logic for the flowchart agent."""

from __future__ import annotations


def find_next_unanswered(graph: dict, answers: dict[str, str]) -> dict | None:
    """Walk the graph from start, following answered branches, and return the
    first unanswered question node.  Returns None when the assessment is complete.

    Returns a node dict or None.
    """
    start = graph.get("start_node")
    if not start:
        return None

    visited: set[str] = set()
    current = start
    max_depth = 50

    for _ in range(max_depth):
        if current in visited:
            return None  # loop detected
        visited.add(current)

        node = graph["nodes"].get(current)
        if node is None:
            return None

        if node["type"] == "terminal":
            return None  # assessment complete

        # If this question hasn't been answered yet, it's the next one
        if current not in answers:
            return node

        # Already answered — resolve which edge to follow
        answer = answers[current]
        next_id = get_next_question_id(graph, current, answer)
        if next_id is None:
            return None  # dead end
        current = next_id

    return None  # max depth exceeded


def get_next_question_id(
    graph: dict, current_id: str, answer: str
) -> str | None:
    """Given the current node and the user's answer, determine which node
    comes next by evaluating edge conditions."""
    edges = [e for e in graph["edges"] if e["from"] == current_id]

    if not edges:
        return None

    # Unconditional edge (single, no condition)
    unconditional = [e for e in edges if e["condition"] is None]
    if len(edges) == 1 and unconditional:
        return edges[0]["to"]

    # Conditional edges — try to match the answer
    conditional = [e for e in edges if e["condition"] is not None]
    for edge in conditional:
        if _condition_matches(edge["condition"], answer):
            return edge["to"]

    # Fallback: unconditional edge if no condition matched
    if unconditional:
        return unconditional[0]["to"]

    # Last resort: first conditional edge (shouldn't normally happen)
    return conditional[0]["to"] if conditional else None


def is_complete(graph: dict, answers: dict[str, str]) -> bool:
    """Return True when traversal reaches a terminal node."""
    return find_next_unanswered(graph, answers) is None


def _condition_matches(condition: str, answer: str) -> bool:
    """Evaluate whether an answer satisfies an edge condition.

    Supports:
      - Numeric comparisons: "< 18", ">= 18", "> 5"
      - Exact match (case-insensitive): "Yes", "No"
      - Substring match (case-insensitive): "Diabetes"
    """
    condition = condition.strip()
    answer = answer.strip()

    # Numeric comparison: "< 18", ">= 18", etc.
    num_match = _try_numeric_comparison(condition, answer)
    if num_match is not None:
        return num_match

    # Exact match (case-insensitive)
    if condition.lower() == answer.lower():
        return True

    # Substring match
    if condition.lower() in answer.lower():
        return True

    return False


def _try_numeric_comparison(condition: str, answer: str) -> bool | None:
    """Return True/False for numeric conditions, or None if not numeric."""
    import re

    match = re.match(r"^([<>]=?|==|!=)\s*(\d+(?:\.\d+)?)$", condition)
    if not match:
        return None

    try:
        answer_num = float(answer)
    except (ValueError, TypeError):
        return None

    op, threshold_str = match.groups()
    threshold = float(threshold_str)

    ops = {
        "<": answer_num < threshold,
        "<=": answer_num <= threshold,
        ">": answer_num > threshold,
        ">=": answer_num >= threshold,
        "==": answer_num == threshold,
        "!=": answer_num != threshold,
    }
    return ops.get(op)
