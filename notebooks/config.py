"""
Shared model and runner configuration for ADK notebooks.

Centralises the Ollama / LiteLLM setup so every notebook
imports a single MODEL constant instead of repeating it.
"""

import os
import logging
import re

from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions              import InMemorySessionService
from google.adk.runners               import Runner

log = logging.getLogger(__name__)

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / "environment" / ".env")

APP_NAME      = "adk_exploration"
USER_ID       = "notebook"
MAX_LLM_CALLS = 10

# -----------------------------------------------------------------------
# Ollama Path
# -----------------------------------------------------------------------

# -----------------------------------------------------------------------
# Ollama must be running locally before any notebook is executed.
# Uses the openai provider via Ollama's /v1 endpoint rather than
# ollama_chat, which has known tool-response serialisation bugs in
# LiteLLM that cause infinite tool-call loops.
# -----------------------------------------------------------------------

# os.environ.setdefault("OPENAI_API_BASE", "http://localhost:11434/v1")
# os.environ.setdefault("OPENAI_API_KEY", "unused")
# MODEL = LiteLlm(model="openai/qwen3.5:9b", temperature=0.0)
# MODEL = LiteLlm(model="openai/gemma3:e4b", temperature=0.0)

# def make_runner(agent, app_name=APP_NAME):
#     """Create a Runner with an in-memory session service."""
#     return Runner(
#         agent           = agent,
#         app_name        = app_name,
#         session_service = InMemorySessionService(),
#     )


# -----------------------------------------------------------------------
# Google AI Studio Path
# -----------------------------------------------------------------------

# Current models:
# models/gemini-2.5-flash
# models/gemini-2.0-flash
# models/gemini-2.0-flash-001
# models/gemini-2.0-flash-lite-001
# models/gemini-2.0-flash-lite
# models/gemini-2.5-flash-preview-tts
# models/gemini-flash-latest
# models/gemini-flash-lite-latest
# models/gemini-2.5-flash-lite
# models/gemini-2.5-flash-image
# models/gemini-3-flash-preview
# models/gemini-3.1-flash-lite-preview
# models/gemini-3.1-flash-image-preview
# models/gemini-3.1-flash-tts-preview

MODEL = "gemini-3-flash-preview"

def make_runner(agent, app_name=APP_NAME):
    from google.adk.sessions import InMemorySessionService
    from google.adk.runners  import Runner
    return Runner(
        agent           = agent,
        app_name        = app_name,
        session_service = InMemorySessionService(),
    )



_EMOJI_PATTERN = re.compile(
    "[\U0001f300-\U0001f9ff\U00002600-\U000027bf\U0000fe00-\U0000feff\u200d\u2640\u2642]+",
    flags=re.UNICODE,
)

def strip_emojis(text):
    """Remove emoji characters from text."""
    if not text:
        return text
    return _EMOJI_PATTERN.sub("", text)