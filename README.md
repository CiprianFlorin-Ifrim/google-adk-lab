# Google ADK Agent Exploration Lab

A hands-on exploration of Google Agent Development Kit (ADK) 1.31.1 across nine Jupyter notebooks. Covers every ADK primitive, delegation pattern, inter-agent protocol, and observability approach -- from single agents to multi-level orchestration graphs with mixed model tiers.


## What This Covers

- All ADK agent types: LlmAgent, SequentialAgent, ParallelAgent, LoopAgent.
- Delegation patterns: sub_agents with transfer_to_agent, AgentTool, small-to-big model routing.
- Agent-to-Agent (A2A) protocol with both ADK and LangGraph orchestrators.
- Multi-turn conversational agents with persistent session state.
- MCP network-hosted tools via FastMCP and SSE transport.
- OpenTelemetry tracing and Python logging to SQLite.


## Notebooks

| # | Notebook | What It Does |
|---|----------|-------------|
| 1 | Tool Testing | Validates 11 financial tools (mortgage, risk, loan, investment) against Gemini Flash. |
| 2 | Agent Types | Builds and runs all ADK primitives: LlmAgent, SequentialAgent, ParallelAgent, LoopAgent. Tests session state passing between agents via output_key. |
| 3 | Delegation Patterns | Three approaches: sub_agents/transfer_to_agent for LLM-driven routing, AgentTool for programmatic delegation, small-to-big with gemini-3.1-flash-lite routing to gemini-3-flash. Includes a multi-level 3-tier agent graph with matplotlib visualisation. |
| 4 | A2A with ADK | Three standalone agent servers (mortgage port 8001, risk port 8002, investment port 8003) using ADK's to_a2a. An ADK coordinator discovers and calls them via RemoteA2aAgent. |
| 5 | A2A with LangGraph | Same three A2A servers orchestrated by a LangGraph StateGraph with MemorySaver. Raw httpx JSON-RPC calls to each agent's message/send endpoint. |
| 6 | Multi-Turn ADK | Persistent conversation with an ADK agent using InMemorySessionService. Interactive input() loop demonstrating session state across turns. |
| 7 | Multi-Turn LangGraph | Persistent conversation with a LangGraph agent using MemorySaver checkpointer. CALL: prefix protocol for agent delegation. |
| 8 | MCP Network Tools | FastMCP server exposing financial tools over SSE (port 8010). ADK agent connects via McpToolset with SseConnectionParams and uses the tools as if they were local. |
| 9 | Telemetry | Custom SQLiteSpanExporter and SQLiteLogHandler capturing OpenTelemetry traces and Python log records to SQLite. Trace-log correlation via trace_id and span_id. |


## Model Configuration

Two tiers used throughout:

- Standard: `gemini-3-flash-preview` -- orchestrators and complex reasoning.
- Lite: `gemini-3.1-flash-lite-preview` -- leaf agents, single tool calls, fast and cheap.

Configured as plain strings in `config.py`. No LiteLlm wrapper needed for Gemini API models.


## Tools

Eleven financial calculation tools organised into four groups:

- MORTGAGE_TOOLS: calculate_mortgage, check_eligibility, compare_rates.
- RISK_TOOLS: assess_credit_risk, calculate_dti, portfolio_risk_score.
- LOAN_TOOLS: amortization_schedule, loan_comparison.
- INVESTMENT_TOOLS: investment_return, risk_adjusted_return, retirement_projection.

All tools are pure Python functions with typed arguments and docstrings. No external API calls.


## Project Structure

```
adk-exploration/
  config.py                         Shared config (MODEL, make_runner, strip_emojis)
  environment/
    .env                            GOOGLE_API_KEY
    setup.sh                        Conda environment setup
    requirements.txt                google-adk>=1.31.1, litellm>=1.83.0
    env_tests/                      Raw Ollama/LiteLLM test scripts
  tools/
    __init__.py                     Exports ALL_TOOLS, MORTGAGE_TOOLS, etc.
    mortgage.py                     Mortgage calculation tools
    risk_assessment.py              Credit risk tools
    loan.py                         Loan comparison tools
    investment.py                   Investment projection tools
  agents/
    __init__.py
    mortgage_agent.py               A2A server, port 8001
    risk_agent.py                   A2A server, port 8002
    investment_agent.py             A2A server, port 8003
  mcp_servers/
    financial_tools_server.py       MCP server via FastMCP, port 8010
  notebooks/
    1_tool_testing.ipynb
    2_agent_types.ipynb
    3_delegation_patterns.ipynb
    4_a2a_adk.ipynb
    5_a2a_langgraph.ipynb
    6_multi_turn_adk.ipynb
    7_multi_turn_langgraph.ipynb
    8_mcp_tools.ipynb
    9_telemetry.ipynb
  docs/
    writeup.md                      Full technical writeup (10 sections)
    writeup.docx                    Word document version
    diagrams/
      single_agent.svg
      sequential_pipeline.svg
      parallel_fanout.svg
      loop_agent.svg
      multi_level_graph.svg
      a2a_protocol.svg
      small_to_big.svg
```


## Setup

Prerequisites: Python 3.11+, a Google API key with Gemini access.

```bash
conda create -n adk-env python=3.13
conda activate adk-env
pip install google-adk litellm jupyter pandas matplotlib
echo "GOOGLE_API_KEY=your-key" > environment/.env
jupyter notebook
```

For A2A notebooks (4 and 5), start the agent servers first:

```bash
python -m agents.mortgage_agent   # port 8001
python -m agents.risk_agent       # port 8002
python -m agents.investment_agent # port 8003
```

For the MCP notebook (8), start the MCP server:

```bash
python mcp_servers/financial_tools_server.py   # port 8010
```


## Key ADK Patterns Demonstrated

Agent as sub_agent (notebook 2, 3):

```
coordinator = LlmAgent(
    name="coordinator",
    sub_agents=[mortgage_agent, risk_agent, investment_agent],
)
```

The LLM decides which sub-agent to transfer to via transfer_to_agent.

Agent as tool (notebook 3):

```
from google.adk.tools.agent_tool import AgentTool

orchestrator = LlmAgent(
    name="orchestrator",
    tools=[AgentTool(agent=specialist_agent)],
)
```

The orchestrator calls the specialist as a function, gets the result back, and keeps control.

Small-to-big delegation (notebook 3):

```
triage = LlmAgent(
    name="triage",
    model="gemini-3.1-flash-lite-preview",
    tools=[AgentTool(agent=complex_analyst)],
)
complex_analyst = LlmAgent(
    name="complex_analyst",
    model="gemini-3-flash-preview",
    tools=ALL_TOOLS,
)
```

Cheap model handles simple queries. Complex queries escalate to the bigger model.

A2A protocol (notebook 4):

```
from google.adk.a2a.utils.agent_to_a2a import to_a2a
app = to_a2a(agent=mortgage_agent, port=8001)
```

Exposes any ADK agent as a JSON-RPC A2A server with automatic agent card generation.


## Documentation

The `docs/` directory contains a full technical writeup covering all nine notebooks and seven SVG architecture diagrams illustrating each pattern. Available as both markdown and Word document.


## ADK Version Notes

Built and tested against ADK 1.31.1. Key compatibility points:

- AgentTool import: `from google.adk.tools.agent_tool import AgentTool`
- A2A import: `from google.adk.a2a.utils.agent_to_a2a import to_a2a` with `port=N` parameter.
- Session service methods require `**kwargs` to accept the `config` parameter added in 1.31.1.
- Model strings are passed directly (e.g. "gemini-3-flash-preview"), not wrapped in LiteLlm.
