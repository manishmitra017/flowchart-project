# Flowchart Conversational Agent

A conversational AI agent built with [Google ADK](https://google.github.io/adk-docs/) that parses **any** Mermaid flowchart, asks questions following the flowchart logic, stores answers in SQLite, and skips already-answered questions.

## How It Works

The agent reads a Mermaid flowchart definition and uses it to drive a conversation. It:

- Walks the flowchart graph node-by-node, asking one question per turn
- Handles conditional branching (e.g., age-based paths, yes/no follow-ups)
- Persists answers to SQLite so users can resume across sessions
- Skips questions that have already been answered
- Adapts its persona, tone, and domain language based on frontmatter metadata

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- A Google AI Studio API key ([get one here](https://aistudio.google.com/apikey))

## Setup

1. **Clone and enter the project:**

   ```bash
   cd flowchart_project
   ```

2. **Add your API key** to the `.env` file:

   ```
   GOOGLE_API_KEY=your_actual_api_key
   ```

3. **Install dependencies:**

   ```bash
   uv sync
   ```

## Running the Agent

### With the default flowchart (health intake demo)

```bash
uv run adk web .
```

### With a custom flowchart

```bash
FLOWCHART_PATH=./my_flowchart.md uv run adk web .
```

The `FLOWCHART_PATH` environment variable points to any `.md` file containing a Mermaid flowchart (with optional frontmatter). When omitted, the bundled health intake demo is used.

### ADK CLI

```bash
uv run adk run flowchart_agent
```

## Creating a Custom Flowchart

Create a `.md` file with optional YAML frontmatter and a Mermaid flowchart:

```markdown
---
title: Customer Onboarding
persona: a friendly customer success representative
domain: onboarding questionnaire
tone_notes: Be encouraging and welcoming to new customers.
completion_message: Welcome aboard! Your onboarding is complete.
---
```mermaid
flowchart TD
    Q1["What is your company name?"]
    Q2["How many employees do you have?"]
    Q2 -->|"< 50"| Q3_small["Which plan interests you? (Starter/Growth)"]
    Q2 -->|">= 50"| Q3_enterprise["Would you like a dedicated account manager? (Yes/No)"]
    Q3_small --> Q4["How did you hear about us?"]
    Q3_enterprise --> Q4
    Q4 --> END_DONE["Onboarding complete!"]

    Q1 --> Q2
` ` `
```

### Frontmatter Fields

All fields are optional. When omitted, sensible defaults are used.

| Field | Default | Description |
|-------|---------|-------------|
| `title` | `Questionnaire` | Flowchart name (also used as database namespace) |
| `persona` | `a friendly, professional assistant` | How the agent introduces itself |
| `domain` | `questionnaire` | Domain context used in the system prompt |
| `tone_notes` | *(empty)* | Extra tone guidance (e.g., "Be empathetic for sensitive topics") |
| `completion_message` | `All questions have been answered.` | Message shown when the flowchart is complete |

### Flowchart Syntax

- **Node definitions:** `Q1["Your question text here"]`
- **Unconditional edges:** `Q1 --> Q2`
- **Conditional edges:** `Q1 -->|"Yes"| Q2` or `Q1 -->|">= 18"| Q3`
- **Terminal nodes:** Any node with "complete", "end", "finish", "done", or "thank" in its text
- **Question type inference:** `(Yes/No)` → yes/no, `(A/B/C)` → multiple choice, "how many" → numeric, otherwise → free text

## Special Commands During the Chat

- **"What's my status?"** — shows how many questions you've answered
- **"Start over"** / **"Restart"** — clears all answers and begins again
- **"I want to change my answer to Q3"** — updates a previous answer

## Resuming a Session

Answers are saved to SQLite (`flowchart_agent/database/answers.db`), namespaced by flowchart title. If you stop and restart the agent, it loads your previous answers and picks up where you left off.

## Project Structure

```
flowchart_project/
├── pyproject.toml                          # uv/hatch project config
├── .env                                    # GOOGLE_API_KEY
└── flowchart_agent/
    ├── __init__.py                         # Exports root_agent
    ├── agent.py                            # LlmAgent definition + init callback
    ├── config.py                           # FlowchartConfig dataclass + defaults
    ├── prompt.py                           # Dynamic system instruction (InstructionProvider)
    ├── flowchart/
    │   ├── parser.py                       # Mermaid text + frontmatter → graph dict
    │   ├── navigator.py                    # Graph traversal + branching logic
    │   └── sample_flowchart.md             # Demo health assessment flowchart
    ├── tools/
    │   └── flowchart_tools.py              # 6 ADK function tools
    └── database/
        └── models.py                       # SQLite schema + CRUD (with flowchart_id)
```
