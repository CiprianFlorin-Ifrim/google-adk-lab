"""
MCP server exposing financial tools over HTTP/SSE.

Wraps the existing local financial tools as MCP tools, served
over the network so any MCP client can discover and call them.

Run: python mcp_servers/financial_tools_server.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP

from tools.mortgage import (
    calculate_monthly_payment,
    calculate_amortization_schedule,
    calculate_affordability,
)
from tools.risk_assessment import calculate_credit_risk_score, assess_loan_risk
from tools.loan import calculate_dti_ratio, check_loan_eligibility, compare_loans
from tools.investment import calculate_compound_interest, calculate_roi, calculate_savings_goal

# -----------------------------------------------------------------------
# Create the MCP server
# -----------------------------------------------------------------------

mcp = FastMCP("Financial Tools Server")

# -----------------------------------------------------------------------
# Register each tool with the MCP server.
# FastMCP uses the function name, docstring, and type hints to
# auto-generate the MCP tool schema -- same as how ADK's FunctionTool
# works with local tools.
# -----------------------------------------------------------------------

# Mortgage tools
mcp.tool()(calculate_monthly_payment)
mcp.tool()(calculate_amortization_schedule)
mcp.tool()(calculate_affordability)

# Risk tools
mcp.tool()(calculate_credit_risk_score)
mcp.tool()(assess_loan_risk)

# Loan tools
mcp.tool()(calculate_dti_ratio)
mcp.tool()(check_loan_eligibility)
mcp.tool()(compare_loans)

# Investment tools
mcp.tool()(calculate_compound_interest)
mcp.tool()(calculate_roi)
mcp.tool()(calculate_savings_goal)


if __name__ == "__main__":
    import uvicorn
    app = mcp.sse_app()
    uvicorn.run(app, host="localhost", port=8010)
