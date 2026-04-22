"""
A2A investment agent server.

Exposes an investment specialist as an A2A service on port 8003.
Run: uvicorn agents.investment_agent:a2a_app --host localhost --port 8003
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from google.adk.agents import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from tools import INVESTMENT_TOOLS

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / "environment" / ".env")

MODEL = "gemini-3-flash-preview"

investment_agent = Agent(
    model       = MODEL,
    name        = "investment_agent",
    description = "Projects investment growth, calculates ROI, and plans savings goals.",
    instruction = (
        "You are an investment analyst. Use the available tools to project "
        "returns, calculate ROI, or plan savings goals."
    ),
    tools = INVESTMENT_TOOLS,
)

a2a_app = to_a2a(investment_agent, port=8003)
