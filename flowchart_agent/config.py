"""Default configuration for the flowchart agent."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FlowchartConfig:
    """Metadata about the loaded flowchart, stored in app-scoped session state."""

    title: str = "Questionnaire"
    persona: str = "a friendly, professional assistant"
    domain: str = "questionnaire"
    tone_notes: str = ""
    completion_message: str = "All questions have been answered."
