"""
Financial calculation tools for agents.

Import individual functions or use the grouped dictionaries
for registering the tools with the agents.
"""

from tools.mortgage import (
    calculate_monthly_payment,
    calculate_amortization_schedule,
    calculate_affordability,
)
from tools.risk_assessment import (
    calculate_credit_risk_score,
    assess_loan_risk,
)
from tools.loan import (
    calculate_dti_ratio,
    check_loan_eligibility,
    compare_loans,
)
from tools.investment import (
    calculate_compound_interest,
    calculate_roi,
    calculate_savings_goal,
)

# Grouped by domain for easy agent registration
MORTGAGE_TOOLS = [
    calculate_monthly_payment,
    calculate_amortization_schedule,
    calculate_affordability,
]

RISK_TOOLS = [
    calculate_credit_risk_score,
    assess_loan_risk,
]

LOAN_TOOLS = [
    calculate_dti_ratio,
    check_loan_eligibility,
    compare_loans,
]

INVESTMENT_TOOLS = [
    calculate_compound_interest,
    calculate_roi,
    calculate_savings_goal,
]

ALL_TOOLS = MORTGAGE_TOOLS + RISK_TOOLS + LOAN_TOOLS + INVESTMENT_TOOLS
