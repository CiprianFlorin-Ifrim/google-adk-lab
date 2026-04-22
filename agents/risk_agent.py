"""
A2A risk assessment agent server.

Exposes a risk specialist as an A2A service on port 8002.
Run: uvicorn agents.risk_agent:a2a_app --host localhost --port 8002
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from google.adk.agents import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from tools import RISK_TOOLS

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / "environment" / ".env")

MODEL = "gemini-3-flash-preview"

risk_agent = Agent(
    model       = MODEL,
    name        = "risk_agent",
    description = "Evaluates credit risk scores and performs loan risk assessments.",
    instruction = (
        "You are a risk analyst. Evaluate the applicant's risk profile "
        "using the available tools. Report the score, category, and any flags."
    ),
    tools = RISK_TOOLS,
)

a2a_app = to_a2a(risk_agent, port=8002)
