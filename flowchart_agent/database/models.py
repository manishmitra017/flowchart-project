"""SQLite persistence for flowchart answers."""

from __future__ import annotations

import asyncio
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "answers.db"
_init_lock = asyncio.Lock()
_initialized = False


async def init_db() -> None:
    """Create the answers table if it doesn't exist."""
    global _initialized
    async with _init_lock:
        if _initialized:
            return
        _run_sync(
            """
            CREATE TABLE IF NOT EXISTS answers (
                user_id       TEXT NOT NULL,
                flowchart_id  TEXT NOT NULL DEFAULT 'default',
                question_id   TEXT NOT NULL,
                answer        TEXT NOT NULL,
                timestamp     TEXT NOT NULL,
                PRIMARY KEY (user_id, flowchart_id, question_id)
            )
            """
        )
        _initialized = True


async def save_answer(
    user_id: str, question_id: str, answer: str, flowchart_id: str = "default"
) -> None:
    """Upsert a single answer."""
    await init_db()
    _run_sync(
        """
        INSERT INTO answers (user_id, flowchart_id, question_id, answer, timestamp)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, flowchart_id, question_id)
        DO UPDATE SET answer = excluded.answer, timestamp = excluded.timestamp
        """,
        (
            user_id,
            flowchart_id,
            question_id,
            answer,
            datetime.now(timezone.utc).isoformat(),
        ),
    )


async def load_answers(
    user_id: str, flowchart_id: str = "default"
) -> dict[str, str]:
    """Load all answers for a user/flowchart as {question_id: answer}."""
    await init_db()
    rows = _run_sync(
        "SELECT question_id, answer FROM answers WHERE user_id = ? AND flowchart_id = ?",
        (user_id, flowchart_id),
        fetch=True,
    )
    return {r[0]: r[1] for r in rows}


async def clear_single_answer(
    user_id: str, question_id: str, flowchart_id: str = "default"
) -> None:
    """Delete a single answer for a user/flowchart/question."""
    await init_db()
    _run_sync(
        "DELETE FROM answers WHERE user_id = ? AND flowchart_id = ? AND question_id = ?",
        (user_id, flowchart_id, question_id),
    )


async def clear_answers(
    user_id: str, flowchart_id: str = "default"
) -> None:
    """Delete all answers for a user/flowchart."""
    await init_db()
    _run_sync(
        "DELETE FROM answers WHERE user_id = ? AND flowchart_id = ?",
        (user_id, flowchart_id),
    )


def _run_sync(sql: str, params: tuple = (), *, fetch: bool = False):
    """Run a synchronous SQLite operation (safe for single-writer workloads)."""
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.execute(sql, params)
        if fetch:
            return cur.fetchall()
        conn.commit()
    finally:
        conn.close()
