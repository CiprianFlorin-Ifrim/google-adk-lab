"""
Mortgage calculation tools for ADK agents.

Provides monthly payment calculation, amortization schedules,
and affordability assessment.
"""


def calculate_monthly_payment(
    principal: float,
    annual_rate: float,
    term_years: int,
    down_payment: float = 0.0,
) -> dict:
    """Calculate the monthly mortgage payment for a home loan.

    Use when the user specifies a property price, rate, and term and wants
    to know the monthly payment. Do not use for affordability questions
    where no specific property price is given.

    Args:
        principal: Total property price in dollars.
        annual_rate: Annual interest rate as a percentage (e.g. 6.5 for 6.5%).
        term_years: Loan term in years (e.g. 30).
        down_payment: Down payment amount in dollars. Defaults to 0.

    Returns:
        Dictionary with loan_amount, monthly_payment, total_paid,
        total_interest, and loan_to_value ratio.
    """
    loan_amount = principal - down_payment

    if loan_amount <= 0:
        return {"error": "Down payment exceeds or equals property price."}
    if annual_rate < 0:
        return {"error": "Interest rate cannot be negative."}
    if term_years <= 0:
        return {"error": "Loan term must be positive."}

    ltv = loan_amount / principal

    if annual_rate == 0:
        monthly_payment = loan_amount / (term_years * 12)
    else:
        monthly_rate = (annual_rate / 100) / 12
        n_payments = term_years * 12
        monthly_payment = loan_amount * (
            monthly_rate * (1 + monthly_rate) ** n_payments
        ) / ((1 + monthly_rate) ** n_payments - 1)

    total_paid = monthly_payment * term_years * 12
    total_interest = total_paid - loan_amount

    return {
        "principal": principal,
        "down_payment": down_payment,
        "loan_amount": round(loan_amount, 2),
        "annual_rate": annual_rate,
        "term_years": term_years,
        "monthly_payment": round(monthly_payment, 2),
        "total_paid": round(total_paid, 2),
        "total_interest": round(total_interest, 2),
        "loan_to_value": round(ltv, 4),
    }


def calculate_amortization_schedule(
    loan_amount: float,
    annual_rate: float,
    term_years: int,
    num_periods: int = 0,
) -> dict:
    """Generate an amortization schedule showing principal and interest breakdown per period.

    Use when the user wants to see how payments are split between principal
    and interest over time, or how the balance decreases year by year.
    Requires a known loan amount -- use calculate_monthly_payment first
    if only the property price is given.

    Args:
        loan_amount: The total loan amount in dollars (after down payment).
        annual_rate: Annual interest rate as a percentage (e.g. 6.5 for 6.5%).
        term_years: Loan term in years.
        num_periods: Number of monthly periods to return. 0 means return
            a yearly summary instead of every month.

    Returns:
        Dictionary with monthly_payment and a schedule list. Each entry in
        the schedule contains period, principal_paid, interest_paid, and
        remaining_balance.
    """
    if loan_amount <= 0 or annual_rate < 0 or term_years <= 0:
        return {"error": "Invalid inputs. All values must be positive (rate can be 0)."}

    monthly_rate = (annual_rate / 100) / 12
    n_payments = term_years * 12

    if annual_rate == 0:
        monthly_payment = loan_amount / n_payments
    else:
        monthly_payment = loan_amount * (
            monthly_rate * (1 + monthly_rate) ** n_payments
        ) / ((1 + monthly_rate) ** n_payments - 1)

    schedule = []
    balance = loan_amount
    yearly_principal = 0.0
    yearly_interest = 0.0

    for period in range(1, n_payments + 1):
        interest_paid = balance * monthly_rate
        principal_paid = monthly_payment - interest_paid
        balance -= principal_paid

        if num_periods > 0 and period <= num_periods:
            schedule.append({
                "month": period,
                "principal_paid": round(principal_paid, 2),
                "interest_paid": round(interest_paid, 2),
                "remaining_balance": round(max(balance, 0), 2),
            })
        elif num_periods == 0:
            yearly_principal += principal_paid
            yearly_interest += interest_paid
            if period % 12 == 0:
                schedule.append({
                    "year": period // 12,
                    "principal_paid": round(yearly_principal, 2),
                    "interest_paid": round(yearly_interest, 2),
                    "remaining_balance": round(max(balance, 0), 2),
                })
                yearly_principal = 0.0
                yearly_interest = 0.0

    return {
        "loan_amount": loan_amount,
        "annual_rate": annual_rate,
        "term_years": term_years,
        "monthly_payment": round(monthly_payment, 2),
        "schedule": schedule,
    }


def calculate_affordability(
    annual_income: float,
    monthly_debts: float,
    annual_rate: float,
    term_years: int = 30,
    max_dti: float = 43.0,
    down_payment: float = 0.0,
) -> dict:
    """Estimate the maximum affordable home price based on income and debts.

    Use when the user wants to know the most expensive home they can buy
    given their income and debts, without a specific property in mind.
    Do not use when the user already has a specific property price and
    wants a payment calculation -- use calculate_monthly_payment instead.

    Uses the debt-to-income ratio to determine the maximum monthly payment,
    then works backward to find the maximum loan and home price.

    Args:
        annual_income: Gross annual income in dollars.
        monthly_debts: Total existing monthly debt payments in dollars
            (car loans, credit cards, student loans, etc.).
        annual_rate: Expected annual mortgage interest rate as a percentage.
        term_years: Expected loan term in years. Defaults to 30.
        max_dti: Maximum acceptable debt-to-income ratio as a percentage.
            Defaults to 43 (common conventional loan limit).
        down_payment: Available down payment in dollars. Defaults to 0.

    Returns:
        Dictionary with max_monthly_payment, max_loan_amount,
        max_home_price, and the resulting dti.
    """
    monthly_income = annual_income / 12
    max_total_debt = monthly_income * (max_dti / 100)
    max_mortgage_payment = max_total_debt - monthly_debts

    if max_mortgage_payment <= 0:
        return {
            "error": "Existing debts already exceed the maximum DTI threshold.",
            "current_dti": round((monthly_debts / monthly_income) * 100, 2),
            "max_dti": max_dti,
        }

    monthly_rate = (annual_rate / 100) / 12
    n_payments = term_years * 12

    if annual_rate == 0:
        max_loan = max_mortgage_payment * n_payments
    else:
        max_loan = max_mortgage_payment * (
            ((1 + monthly_rate) ** n_payments - 1)
            / (monthly_rate * (1 + monthly_rate) ** n_payments)
        )

    max_home_price = max_loan + down_payment

    return {
        "annual_income": annual_income,
        "monthly_debts": monthly_debts,
        "max_monthly_mortgage_payment": round(max_mortgage_payment, 2),
        "max_loan_amount": round(max_loan, 2),
        "max_home_price": round(max_home_price, 2),
        "down_payment": down_payment,
        "annual_rate": annual_rate,
        "term_years": term_years,
        "resulting_dti": round(max_dti, 2),
    }
