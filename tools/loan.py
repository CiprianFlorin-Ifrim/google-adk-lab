"""
Loan calculation tools for ADK agents.

Provides debt-to-income ratio calculation, loan eligibility
checks across program types, and side-by-side loan comparison.
"""


def calculate_dti_ratio(
    annual_income: float,
    monthly_debts: float,
    proposed_monthly_payment: float = 0.0,
) -> dict:
    """Calculate the debt-to-income ratio with and without a proposed new payment.

    Use when the user wants to check how a new monthly obligation (e.g. a
    mortgage payment) would affect their DTI ratio. Not needed if the user
    is only asking for a payment amount or affordability estimate.

    Args:
        annual_income: Gross annual income in dollars.
        monthly_debts: Total existing monthly debt payments in dollars
            (car loans, credit cards, student loans, etc.).
        proposed_monthly_payment: A proposed new monthly payment to include
            in the calculation (e.g. a mortgage payment). Defaults to 0.

    Returns:
        Dictionary with current_dti (without proposed payment),
        projected_dti (with proposed payment), monthly_income,
        remaining_capacity, and a qualitative assessment.
    """
    if annual_income <= 0:
        return {"error": "Annual income must be positive."}

    monthly_income = annual_income / 12
    current_dti = (monthly_debts / monthly_income) * 100
    projected_dti = ((monthly_debts + proposed_monthly_payment) / monthly_income) * 100

    # How much room is left before hitting 43% DTI
    max_at_43 = monthly_income * 0.43
    remaining_capacity = max_at_43 - monthly_debts - proposed_monthly_payment

    if projected_dti <= 20:
        assessment = "EXCELLENT"
    elif projected_dti <= 36:
        assessment = "GOOD"
    elif projected_dti <= 43:
        assessment = "ACCEPTABLE"
    elif projected_dti <= 50:
        assessment = "STRETCHED"
    else:
        assessment = "OVEREXTENDED"

    return {
        "monthly_income": round(monthly_income, 2),
        "monthly_debts": monthly_debts,
        "proposed_monthly_payment": proposed_monthly_payment,
        "current_dti": round(current_dti, 2),
        "projected_dti": round(projected_dti, 2),
        "remaining_monthly_capacity_at_43pct": round(max(remaining_capacity, 0), 2),
        "assessment": assessment,
    }


def check_loan_eligibility(
    credit_score: int,
    annual_income: float,
    monthly_debts: float,
    loan_amount: float,
    property_value: float,
    is_first_time_buyer: bool = False,
    is_veteran: bool = False,
) -> dict:
    """Check eligibility across multiple loan program types.

    Use when the user wants to know which loan programs (Conventional,
    FHA, VA) they qualify for. Requires a specific loan amount and
    property value. Not for general affordability questions.

    Evaluates whether the applicant qualifies for Conventional, FHA,
    and VA loan programs based on credit score, DTI, and LTV requirements.

    Args:
        credit_score: Applicant's credit score (300-850).
        annual_income: Gross annual income in dollars.
        monthly_debts: Existing monthly debt payments in dollars.
        loan_amount: Requested loan amount in dollars.
        property_value: Property value or purchase price in dollars.
        is_first_time_buyer: Whether the applicant is a first-time home buyer.
        is_veteran: Whether the applicant is a veteran or active military.

    Returns:
        Dictionary with eligibility results for each loan program,
        including whether qualified, reasons for disqualification,
        and estimated rate premium.
    """
    monthly_income = annual_income / 12
    ltv = loan_amount / property_value if property_value > 0 else 999

    # Estimate a rough monthly payment for DTI (using 6.5% / 30yr as baseline)
    rate = 0.065 / 12
    n = 360
    est_payment = loan_amount * (rate * (1 + rate) ** n) / ((1 + rate) ** n - 1)
    dti = ((monthly_debts + est_payment) / monthly_income) * 100

    programs = {}

    # --- Conventional ---
    conv_issues = []
    conv_eligible = True
    if credit_score < 620:
        conv_issues.append("Credit score below 620 minimum")
        conv_eligible = False
    if dti > 45:
        conv_issues.append(f"DTI of {dti:.1f}% exceeds 45% limit")
        conv_eligible = False
    if ltv > 0.97:
        conv_issues.append("LTV exceeds 97% maximum")
        conv_eligible = False

    conv_rate_adj = 0.0
    if credit_score < 700:
        conv_rate_adj += 0.25
    if ltv > 0.90:
        conv_rate_adj += 0.125

    programs["conventional"] = {
        "eligible": conv_eligible,
        "issues": conv_issues,
        "min_down_payment_pct": 3.0 if is_first_time_buyer else 5.0,
        "requires_pmi": ltv > 0.80,
        "estimated_rate_adjustment": conv_rate_adj,
    }

    # --- FHA ---
    fha_issues = []
    fha_eligible = True
    if credit_score < 500:
        fha_issues.append("Credit score below 500 absolute minimum")
        fha_eligible = False
    elif credit_score < 580:
        if ltv > 0.90:
            fha_issues.append("Credit 500-579 requires at least 10% down (LTV <= 90%)")
            fha_eligible = False
    if dti > 50:
        fha_issues.append(f"DTI of {dti:.1f}% exceeds FHA 50% limit")
        fha_eligible = False

    min_down_fha = 10.0 if credit_score < 580 else 3.5

    programs["fha"] = {
        "eligible": fha_eligible,
        "issues": fha_issues,
        "min_down_payment_pct": min_down_fha,
        "requires_mip": True,  # FHA always requires mortgage insurance premium
        "estimated_rate_adjustment": 0.0,  # FHA rates are generally competitive
    }

    # --- VA ---
    va_issues = []
    va_eligible = is_veteran
    if not is_veteran:
        va_issues.append("VA loans require veteran or active military status")
    else:
        if credit_score < 580:
            va_issues.append("Most VA lenders require 580+ credit score")
            va_eligible = False
        if dti > 41:
            va_issues.append(f"DTI of {dti:.1f}% exceeds VA guideline of 41% (waivable with residual income)")

    programs["va"] = {
        "eligible": va_eligible,
        "issues": va_issues,
        "min_down_payment_pct": 0.0,
        "requires_pmi": False,  # VA has funding fee instead
        "has_funding_fee": True,
        "estimated_rate_adjustment": -0.25,  # VA rates often slightly lower
    }

    best_option = None
    for name, prog in programs.items():
        if prog["eligible"]:
            if best_option is None:
                best_option = name
            elif prog["min_down_payment_pct"] < programs[best_option]["min_down_payment_pct"]:
                best_option = name

    return {
        "applicant_summary": {
            "credit_score": credit_score,
            "estimated_dti": round(dti, 2),
            "ltv": round(ltv, 4),
            "is_first_time_buyer": is_first_time_buyer,
            "is_veteran": is_veteran,
        },
        "programs": programs,
        "best_option": best_option,
    }


def compare_loans(
    loan_amount: float,
    rates: list[float],
    terms: list[int],
) -> dict:
    """Compare multiple loan scenarios side by side.

    Use when the user wants to compare different rate and term combinations
    for the same loan amount. Not needed for single-scenario calculations.

    Calculates monthly payment, total cost, and total interest for each
    combination of rate and term provided.

    Args:
        loan_amount: The loan amount in dollars (same for all scenarios).
        rates: List of annual interest rates as percentages (e.g. [5.5, 6.0, 6.5]).
        terms: List of loan terms in years (e.g. [15, 30]).

    Returns:
        Dictionary with a list of scenario results, each containing
        rate, term, monthly_payment, total_paid, and total_interest.
        Also includes the cheapest_monthly and cheapest_total scenarios.
    """
    if not rates or not terms:
        return {"error": "Must provide at least one rate and one term."}

    scenarios = []

    for rate in rates:
        for term in terms:
            monthly_rate = (rate / 100) / 12
            n = term * 12

            if rate == 0:
                payment = loan_amount / n
            else:
                payment = loan_amount * (
                    monthly_rate * (1 + monthly_rate) ** n
                ) / ((1 + monthly_rate) ** n - 1)

            total = payment * n
            interest = total - loan_amount

            scenarios.append({
                "annual_rate": rate,
                "term_years": term,
                "monthly_payment": round(payment, 2),
                "total_paid": round(total, 2),
                "total_interest": round(interest, 2),
            })

    cheapest_monthly = min(scenarios, key=lambda s: s["monthly_payment"])
    cheapest_total = min(scenarios, key=lambda s: s["total_paid"])

    return {
        "loan_amount": loan_amount,
        "scenarios": scenarios,
        "cheapest_monthly_payment": {
            "rate": cheapest_monthly["annual_rate"],
            "term": cheapest_monthly["term_years"],
            "monthly_payment": cheapest_monthly["monthly_payment"],
        },
        "cheapest_total_cost": {
            "rate": cheapest_total["annual_rate"],
            "term": cheapest_total["term_years"],
            "total_paid": cheapest_total["total_paid"],
        },
    }
