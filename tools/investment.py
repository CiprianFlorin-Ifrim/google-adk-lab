"""
Investment and savings calculation tools for ADK agents.

Provides compound interest projection, ROI calculation,
and savings goal planning.
"""


def calculate_compound_interest(
    principal: float,
    annual_rate: float,
    years: int,
    monthly_contribution: float = 0.0,
    compounding_frequency: int = 12,
) -> dict:
    """Project the future value of an investment with compound interest.

    Use when the user wants to know how an investment will grow over time
    given an initial amount, regular contributions, and a return rate.
    Not for loan or mortgage calculations.

    Args:
        principal: Initial investment amount in dollars.
        annual_rate: Annual return rate as a percentage (e.g. 7.0 for 7%).
        years: Investment time horizon in years.
        monthly_contribution: Additional monthly contribution in dollars. Defaults to 0.
        compounding_frequency: Number of times interest compounds per year.
            Defaults to 12 (monthly).

    Returns:
        Dictionary with future_value, total_contributions, total_interest_earned,
        and a year-by-year growth summary.
    """
    if years <= 0:
        return {"error": "Investment period must be positive."}
    if compounding_frequency <= 0:
        return {"error": "Compounding frequency must be positive."}

    rate_per_period = (annual_rate / 100) / compounding_frequency
    total_periods = years * compounding_frequency
    contributions_per_compound = monthly_contribution * (12 / compounding_frequency)

    balance = principal
    total_contributed = principal
    yearly_summary = []

    for period in range(1, total_periods + 1):
        balance = balance * (1 + rate_per_period) + contributions_per_compound
        total_contributed += contributions_per_compound

        if period % compounding_frequency == 0:
            year = period // compounding_frequency
            yearly_summary.append({
                "year": year,
                "balance": round(balance, 2),
                "total_contributed": round(total_contributed, 2),
                "interest_earned": round(balance - total_contributed, 2),
            })

    return {
        "principal": principal,
        "annual_rate": annual_rate,
        "years": years,
        "monthly_contribution": monthly_contribution,
        "future_value": round(balance, 2),
        "total_contributions": round(total_contributed, 2),
        "total_interest_earned": round(balance - total_contributed, 2),
        "yearly_summary": yearly_summary,
    }


def calculate_roi(
    initial_investment: float,
    final_value: float,
    years: float = 0,
    annual_cash_flows: float = 0.0,
) -> dict:
    """Calculate return on investment with optional annualized return.

    Use when the user knows the purchase price and current value of an
    existing investment and wants to measure performance. Not for
    projecting future growth -- use calculate_compound_interest for that.

    Args:
        initial_investment: The initial amount invested in dollars.
        final_value: The current or exit value of the investment in dollars.
        years: Holding period in years. If provided and greater than 0,
            calculates annualized return. Defaults to 0 (simple ROI only).
        annual_cash_flows: Total annual income received from the investment
            (e.g. dividends, rent) in dollars per year. Defaults to 0.

    Returns:
        Dictionary with simple_roi percentage, total_gain, and
        optionally annualized_return if years is provided.
    """
    if initial_investment <= 0:
        return {"error": "Initial investment must be positive."}

    total_cash_flows = annual_cash_flows * years if years > 0 else 0
    total_gain = (final_value - initial_investment) + total_cash_flows
    simple_roi = (total_gain / initial_investment) * 100

    result = {
        "initial_investment": initial_investment,
        "final_value": final_value,
        "total_cash_flows": round(total_cash_flows, 2),
        "total_gain": round(total_gain, 2),
        "simple_roi_pct": round(simple_roi, 2),
    }

    if years > 0:
        # Annualized return: (ending / beginning)^(1/years) - 1
        total_return_factor = (final_value + total_cash_flows) / initial_investment
        if total_return_factor > 0:
            annualized = (total_return_factor ** (1 / years) - 1) * 100
            result["annualized_return_pct"] = round(annualized, 2)
            result["years"] = years
        else:
            result["annualized_return_pct"] = None
            result["note"] = "Cannot annualize a total loss."

    return result


def calculate_savings_goal(
    target_amount: float,
    current_savings: float,
    annual_rate: float,
    monthly_contribution: float = 0.0,
) -> dict:
    """Determine how long it takes to reach a savings goal, or how much to save monthly.

    Use when the user has a specific dollar target they want to reach and
    wants to know either how long it will take or how much to contribute
    per month. Not for general investment growth projections.

    If monthly_contribution is provided and greater than 0, calculates
    the number of months to reach the target. If monthly_contribution is 0,
    calculates the required monthly contribution assuming a 10-year horizon.

    Args:
        target_amount: The savings goal in dollars.
        current_savings: Current amount already saved in dollars.
        annual_rate: Expected annual return rate as a percentage (e.g. 5.0 for 5%).
        monthly_contribution: Planned monthly contribution in dollars.
            If 0, the function will calculate the required contribution
            for a 10-year timeline.

    Returns:
        Dictionary with either months_to_goal and years_to_goal, or
        required_monthly_contribution, along with total_contributed
        and interest_earned projections.
    """
    if target_amount <= current_savings:
        return {
            "message": "You have already reached your savings goal.",
            "current_savings": current_savings,
            "target_amount": target_amount,
            "surplus": round(current_savings - target_amount, 2),
        }

    gap = target_amount - current_savings
    monthly_rate = (annual_rate / 100) / 12

    if monthly_contribution > 0:
        # Calculate time to reach goal
        balance = current_savings
        months = 0
        max_months = 12 * 60  # cap at 60 years

        while balance < target_amount and months < max_months:
            balance = balance * (1 + monthly_rate) + monthly_contribution
            months += 1

        if months >= max_months:
            return {
                "error": "Goal not reachable within 60 years at this contribution rate.",
                "projected_balance_at_60y": round(balance, 2),
            }

        total_contributed = current_savings + (monthly_contribution * months)

        return {
            "target_amount": target_amount,
            "current_savings": current_savings,
            "monthly_contribution": monthly_contribution,
            "annual_rate": annual_rate,
            "months_to_goal": months,
            "years_to_goal": round(months / 12, 1),
            "total_contributed": round(total_contributed, 2),
            "interest_earned": round(balance - total_contributed, 2),
        }
    else:
        # Calculate required monthly contribution for 10 years
        n = 120  # 10 years
        if monthly_rate == 0:
            required = gap / n
        else:
            # Future value of annuity formula, solved for payment
            # Also account for growth of current savings
            future_current = current_savings * (1 + monthly_rate) ** n
            remaining_gap = target_amount - future_current
            if remaining_gap <= 0:
                return {
                    "message": "Current savings will grow to meet the goal without additional contributions.",
                    "current_savings": current_savings,
                    "projected_value_10y": round(future_current, 2),
                    "target_amount": target_amount,
                }
            required = remaining_gap * monthly_rate / ((1 + monthly_rate) ** n - 1)

        total_contributed = current_savings + (required * n)
        projected_balance = current_savings
        for _ in range(n):
            projected_balance = projected_balance * (1 + monthly_rate) + required

        return {
            "target_amount": target_amount,
            "current_savings": current_savings,
            "annual_rate": annual_rate,
            "assumed_timeline_years": 10,
            "required_monthly_contribution": round(required, 2),
            "total_contributed_over_period": round(total_contributed, 2),
            "projected_interest_earned": round(projected_balance - total_contributed, 2),
        }
