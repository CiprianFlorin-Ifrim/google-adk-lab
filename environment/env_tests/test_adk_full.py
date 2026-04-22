"""
Full stack test: Ollama -> LiteLLM -> ADK.

Properly separates thought parts (part.thought=True) from content parts
when reading the agent response.

Run: python test_adk_full.py
"""

import os
import asyncio
import logging

logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt = "%H:%M:%S",
)
log = logging.getLogger(__name__)

os.environ.setdefault("OPENAI_API_BASE", "http://localhost:11434/v1")
os.environ.setdefault("OPENAI_API_KEY", "unused")

from google.adk.agents   import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.adk.runners  import Runner
from google.genai         import types

MODEL = LiteLlm(model="openai/gemma4:e4b")


# -----------------------------------------------------------------------
# Tool
# -----------------------------------------------------------------------

def multiply(a: float, b: float) -> dict:
    """Multiply two numbers together.

    Use when the user asks to multiply two specific numbers.

    Args:
        a: First number.
        b: Second number.

    Returns:
        Dictionary with the result.
    """
    return {"result": a * b}


# -----------------------------------------------------------------------
# Response handler that separates thought from content
# -----------------------------------------------------------------------

async def run_agent(agent, query):
    """Send a query and return (content_text, thinking_text)."""
    runner = Runner(
        agent           = agent,
        app_name        = "test",
        session_service = InMemorySessionService(),
    )
    session = await runner.session_service.create_session(
        app_name = "test",
        user_id  = "tester",
    )
    content = types.Content(
        role  = "user",
        parts = [types.Part(text=query)],
    )

    content_parts  = []
    thinking_parts = []

    async for event in runner.run_async(
        user_id     = "tester",
        session_id  = session.id,
        new_message = content,
    ):
        author = getattr(event, "author", "unknown")

        if event.content and event.content.parts:
            for part in event.content.parts:
                # Log tool calls
                if hasattr(part, "function_call") and part.function_call:
                    log.info("[%s] tool_call: %s(%s)",
                             author, part.function_call.name,
                             dict(part.function_call.args or {}))
                if hasattr(part, "function_response") and part.function_response:
                    log.info("[%s] tool_response: %s -> %s",
                             author, part.function_response.name,
                             str(part.function_response.response)[:200])

        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if not hasattr(part, "text") or not part.text:
                    continue
                if getattr(part, "thought", False):
                    thinking_parts.append(part.text)
                else:
                    content_parts.append(part.text)

    content_text  = "\n".join(content_parts) if content_parts else None
    thinking_text = "\n".join(thinking_parts) if thinking_parts else None

    return content_text, thinking_text


# -----------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------

async def main():
    # --- Test 1: basic completion ---
    log.info("=" * 60)
    log.info("TEST 1: basic completion (no tools)")
    log.info("=" * 60)

    basic_agent = Agent(
        model       = MODEL,
        name        = "basic_agent",
        description = "Simple test agent.",
        instruction = "Answer in one sentence.",
    )

    content, thinking = await run_agent(basic_agent, "What is the capital of France?")
    log.info("content:  %s", content)
    log.info("thinking: %s", thinking)

    # --- Test 2: tool calling ---
    log.info("=" * 60)
    log.info("TEST 2: tool calling")
    log.info("=" * 60)

    tool_agent = Agent(
        model       = MODEL,
        name        = "tool_agent",
        description = "Agent that multiplies numbers.",
        instruction = "Use the multiply tool to answer the user's question.",
        tools       = [multiply],
    )

    content, thinking = await run_agent(tool_agent, "What is 17 times 23?")
    log.info("content:  %s", content)
    log.info("thinking: %s", thinking)


if __name__ == "__main__":
    asyncio.run(main())
