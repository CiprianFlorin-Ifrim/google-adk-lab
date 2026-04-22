"""
A2A mortgage agent server.

Exposes a mortgage specialist as an A2A service on port 8001.
Run: uvicorn agents.mortgage_agent:a2a_app --host localhost --port 8001
"""

import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so tools/ is importable.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from google.adk.agents import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from tools import MORTGAGE_TOOLS

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / "environment" / ".env")

MODEL = "gemini-3-flash-preview"

mortgage_agent = Agent(
    model       = MODEL,
    name        = "mortgage_agent",
    description = "Calculates mortgage payments, amortization schedules, and affordability.",
    instruction = (
        "You are a mortgage specialist. Answer the user's mortgage-related "
        "question using the available tools. Be precise with numbers."
    ),
    tools = MORTGAGE_TOOLS,
)

a2a_app = to_a2a(mortgage_agent, port=8001)
