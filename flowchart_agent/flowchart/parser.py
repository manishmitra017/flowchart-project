"""Mermaid flowchart parser — converts Mermaid text into a graph dict."""

import re
from pathlib import Path


def parse_mermaid_flowchart(mermaid_text: str | None = None) -> dict:
    """Parse Mermaid flowchart TD syntax into a serializable graph dict.

    Returns:
        {
            "nodes": {
                "Q1": {"id": "Q1", "text": "What is your name?", "type": "question",
                        "question_type": "text", "choices": []},
                ...
            },
            "edges": [
                {"from": "Q1", "to": "Q2", "condition": None},
                {"from": "Q2", "to": "Q4_minor", "condition": "< 18"},
                ...
            ],
            "start_node": "Q1"
        }
    """
    if mermaid_text is None:
        sample = Path(__file__).parent / "sample_flowchart.md"
        mermaid_text = sample.read_text()

    # Strip markdown fences
    mermaid_text = re.sub(r"```mermaid\s*", "", mermaid_text)
    mermaid_text = re.sub(r"```\s*$", "", mermaid_text)

    lines = [ln.strip() for ln in mermaid_text.splitlines() if ln.strip()]

    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    for line in lines:
        if line.lower().startswith("flowchart"):
            continue

        # --- Node definitions: Q1["Some text"] ---
        node_match = re.match(r'^(\w+)\["(.+?)"\]\s*$', line)
        if node_match:
            node_id = node_match.group(1)
            text = node_match.group(2)
            nodes[node_id] = _make_node(node_id, text)
            continue

        # --- Edges: A -->|"cond"| B  or  A --> B ---
        edge_match = re.match(
            r'^(\w+)\s*-->\s*(?:\|"(.+?)"\|\s*)?(\w+)\s*$', line
        )
        if edge_match:
            src, cond, dst = edge_match.groups()
            edges.append({"from": src, "to": dst, "condition": cond})
            # Ensure referenced nodes exist (bare id without definition)
            for nid in (src, dst):
                if nid not in nodes:
                    nodes[nid] = _make_node(nid, nid)
            continue

    # Determine start node — first node that is never a destination
    dest_ids = {e["to"] for e in edges}
    start_node = None
    for nid in nodes:
        if nid not in dest_ids:
            start_node = nid
            break
    if start_node is None and nodes:
        start_node = next(iter(nodes))

    # Infer choices for nodes with multiple conditional outgoing edges
    _infer_choices(nodes, edges)

    return {"nodes": nodes, "edges": edges, "start_node": start_node}


def _make_node(node_id: str, text: str) -> dict:
    is_terminal = any(
        kw in text.lower()
        for kw in ("complete", "end", "finish", "done", "thank")
    )
    return {
        "id": node_id,
        "text": text,
        "type": "terminal" if is_terminal else "question",
        "question_type": _infer_question_type(text),
        "choices": [],
    }


def _infer_question_type(text: str) -> str:
    lower = text.lower()
    if "(yes/no)" in lower:
        return "yes_no"
    # Parenthesised list with slashes → multiple choice
    paren = re.search(r"\(([^)]+/[^)]+)\)", text)
    if paren:
        return "multiple_choice"
    if any(kw in lower for kw in ("how many", "how old", "number", "count")):
        return "numeric"
    return "text"


def _infer_choices(nodes: dict, edges: list) -> None:
    """Populate choices list for nodes whose outgoing edges carry conditions."""
    from collections import defaultdict

    outgoing: dict[str, list[str]] = defaultdict(list)
    for e in edges:
        if e["condition"]:
            outgoing[e["from"]].append(e["condition"])

    for nid, conds in outgoing.items():
        if nid in nodes and len(conds) >= 2:
            nodes[nid]["choices"] = conds
