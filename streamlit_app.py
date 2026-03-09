"""Streamlit chat UI for the Flowchart Agent."""

import asyncio
import uuid

import streamlit as st
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from flowchart_agent import root_agent

st.set_page_config(page_title="Flowchart Agent", page_icon="📋", layout="centered")
st.title("📋 Flowchart Agent")

# Initialize ADK Runner once per Streamlit session
if "runner" not in st.session_state:
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="flowchart_app",
        session_service=session_service,
    )
    st.session_state.runner = runner
    st.session_state.session_service = session_service
    st.session_state.user_id = f"streamlit_{uuid.uuid4().hex[:8]}"
    st.session_state.messages = []

    # Create the session explicitly — InMemorySessionService requires this
    _loop = asyncio.new_event_loop()
    _session = _loop.run_until_complete(
        session_service.create_session(
            app_name="flowchart_app",
            user_id=st.session_state.user_id,
        )
    )
    _loop.close()
    st.session_state.session_id = _session.id


async def _run_agent(user_message: str) -> str:
    """Send a message to the ADK agent and return the final agent response."""
    content = types.Content(
        role="user", parts=[types.Part(text=user_message)]
    )
    response_text = ""
    async for event in st.session_state.runner.run_async(
        user_id=st.session_state.user_id,
        session_id=st.session_state.session_id,
        new_message=content,
    ):
        # Debug: log all events to terminal
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    print(f"[DEBUG] {event.author} -> tool: {fc.name}({fc.args})")
                if hasattr(part, "text") and part.text and event.author != "user":
                    print(f"[DEBUG] {event.author} -> text: {part.text[:100]}")
                    response_text = part.text  # Keep the last agent text
    return response_text


def run_agent(user_message: str) -> str:
    """Sync wrapper around the async ADK runner."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run_agent(user_message))
    finally:
        loop.close()


# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Auto-trigger first message to start the questionnaire
if not st.session_state.messages:
    with st.chat_message("assistant"):
        with st.spinner("Starting..."):
            response = run_agent("Hello")
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

# Chat input
if prompt := st.chat_input("Type your answer..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = run_agent(prompt)
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
