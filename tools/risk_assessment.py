"""
Risk assessment tools for ADK agents.

Provides credit risk scoring and loan risk evaluation.
These are simplified models for demonstration purposes,
not actual underwriting algorithms.
"""


def _score_from_thresholds(value, thresholds, ascending=True):
    """Return the points for a value based on a sorted threshold table.

    Args:
        value: The metric value to score.
        thresholds: List of (threshold, points) pairs. Must be sorted by
            threshold in the direction indicated by ascending.
        ascending: If True, thresholds are checked with >=  (higher value
            is better, e.g. credit score). If False, checked with <=
            (lower value is better, e.g. DTI ratio).

    Returns:
        The points matching the first satisfied threshold, or the fallback
        (last entry's points) if none match.
    """
    for threshold, points in thresholds:
        if ascending and value >= threshold:
            return points
        if not ascending and value <= threshold:
            return points
    return thresholds[-1][1]


# Scoring tables: (threshold, points) with floor as last entry.
# ascending=True means >= comparison (higher is better).
# ascending=False means <= comparison (lower is better).
# The flag text is appended when the floor (last entry) is reached.
_SCORING_COMPONENTS = [
    {
        "name": "credit_history",
        "max": 35,
        "ascending": True,
        "thresholds": [(750, 35), (700, 28), (650, 20), (600, 12), (0, 5)],
        "flag": "Very low credit score",
    },
    {
        "name": "debt_to_income",
        "max": 25,
        "ascending": False,
        "thresholds": [(20, 25), (30, 20), (36, 15), (43, 8), (9999, 2)],
        "flag": "DTI exceeds conventional loan limits",
    },
    {
        "name": "loan_to_value",
        "max": 20,
        "ascending": False,
        "thresholds": [(0.60, 20), (0.80, 15), (0.90, 10), (0.95, 5), (9999, 1)],
        "flag": "Very high LTV - likely requires PMI",
    },
    {
        "name": "employment_stability",
        "max": 10,
        "ascending": True,
        "thresholds": [(5, 10), (2, 7), (1, 4), (0, 1)],
        "flag": "Less than 1 year at current employer",
    },
]

_RISK_CATEGORIES = [(80, "LOW_RISK"), (60, "MODERATE_RISK"), (40, "ELEVATED_RISK"), (0, "HIGH_RISK")]


def calculate_credit_risk_score(
    credit_score: int,
    dti_ratio: float,
    ltv_ratio: float,
    employment_years: float,
    has_bankruptcy: bool = False,
    missed_payments_last_2y: int = 0,
) -> dict:
    """Calculate a composite credit risk score for a loan applicant.

    Use when the user wants a general risk profile score based on their
    financial background. Does not evaluate a specific loan -- use
    assess_loan_risk for that.

    Uses a weighted scoring model combining credit history, financial ratios,
    and employment stability. Returns a score from 0 (highest risk) to 100
    (lowest risk) along with a risk category.

    Args:
        credit_score: Applicant's credit score (300-850 range).
        dti_ratio: Debt-to-income ratio as a percentage (e.g. 35.0 for 35%).
        ltv_ratio: Loan-to-value ratio as a decimal (e.g. 0.80 for 80%).
        employment_years: Years at current employer.
        has_bankruptcy: Whether the applicant has a bankruptcy on record.
        missed_payments_last_2y: Number of missed payments in the last 2 years.

    Returns:
        Dictionary with composite_score, risk_category, component_scores
        breakdown, and flags for any risk concerns.
    """
    flags = []
    values = [credit_score, dti_ratio, ltv_ratio, employment_years]

    scores = {}
    for comp, value in zip(_SCORING_COMPONENTS, values):
        pts = _score_from_thresholds(value, comp["thresholds"], comp["ascending"])
        floor_pts = comp["thresholds"][-1][1]
        if pts == floor_pts:
            flags.append(comp["flag"])
        scores[comp["name"]] = {"score": pts, "max": comp["max"]}

    # Derogatory marks (0-10 points, penalty-based)
    derogatory_points = 10
    if has_bankruptcy:
        derogatory_points -= 7
        flags.append("Bankruptcy on record")
    derogatory_points -= min(missed_payments_last_2y * 2, 10)
    derogatory_points = max(derogatory_points, 0)
    if missed_payments_last_2y > 0:
        flags.append(f"{missed_payments_last_2y} missed payment(s) in last 2 years")
    scores["derogatory_marks"] = {"score": derogatory_points, "max": 10}

    composite = sum(s["score"] for s in scores.values())
    category = _score_from_thresholds(composite, _RISK_CATEGORIES, ascending=True)

    return {
        "composite_score": composite,
        "max_possible_score": 100,
        "risk_category": category,
        "component_scores": scores,
        "flags": flags,
        "input_summary": {
            "credit_score": credit_score,
            "dti_ratio": dti_ratio,
            "ltv_ratio": ltv_ratio,
            "employment_years": employment_years,
            "has_bankruptcy": has_bankruptcy,
            "missed_payments_last_2y": missed_payments_last_2y,
        },
    }


def assess_loan_risk(
    loan_amount: float,
    property_value: float,
    annual_income: float,
    monthly_debts: float,
    credit_score: int,
    monthly_payment: float,
) -> dict:
    """Perform a holistic loan risk assessment combining multiple financial metrics.

    Use when a specific loan amount, property value, and monthly payment are
    already known and the user wants an approval recommendation (approve,
    deny, review). Requires outputs from calculate_monthly_payment or
    equivalent figures.

    Args:
        loan_amount: Requested loan amount in dollars.
        property_value: Appraised property value in dollars.
        annual_income: Gross annual income in dollars.
        monthly_debts: Existing monthly debt payments in dollars (excluding the new mortgage).
        credit_score: Applicant's credit score (300-850).
        monthly_payment: The calculated monthly mortgage payment for the requested loan.

    Returns:
        Dictionary with approval_recommendation, overall_risk_level,
        individual metric evaluations, and reasons for the recommendation.
    """
    monthly_income = annual_income / 12
    ltv = loan_amount / property_value if property_value > 0 else 999
    dti_with_mortgage = ((monthly_debts + monthly_payment) / monthly_income) * 100
    payment_to_income = (monthly_payment / monthly_income) * 100

    issues = []
    strengths = []

    # DTI check
    if dti_with_mortgage > 50:
        issues.append(f"DTI of {dti_with_mortgage:.1f}% far exceeds safe limits")
        dti_status = "FAIL"
    elif dti_with_mortgage > 43:
        issues.append(f"DTI of {dti_with_mortgage:.1f}% exceeds conventional limit of 43%")
        dti_status = "WARNING"
    elif dti_with_mortgage > 36:
        dti_status = "ACCEPTABLE"
    else:
        strengths.append(f"Strong DTI of {dti_with_mortgage:.1f}%")
        dti_status = "GOOD"

    # LTV check
    if ltv > 0.97:
        issues.append("LTV exceeds 97% - most programs will not approve")
        ltv_status = "FAIL"
    elif ltv > 0.90:
        issues.append("High LTV - PMI required, higher rates likely")
        ltv_status = "WARNING"
    elif ltv > 0.80:
        ltv_status = "ACCEPTABLE"
    else:
        strengths.append(f"Solid equity position with {(1-ltv)*100:.0f}% down")
        ltv_status = "GOOD"

    # Payment-to-income (front-end ratio)
    if payment_to_income > 35:
        issues.append("Housing payment exceeds 35% of gross income")
        pti_status = "WARNING"
    elif payment_to_income > 28:
        pti_status = "ACCEPTABLE"
    else:
        strengths.append("Housing payment well within income")
        pti_status = "GOOD"

    # Credit check
    if credit_score < 580:
        issues.append("Credit score below FHA minimum")
        credit_status = "FAIL"
    elif credit_score < 620:
        issues.append("Credit score limits loan options to FHA")
        credit_status = "WARNING"
    elif credit_score < 700:
        credit_status = "ACCEPTABLE"
    else:
        strengths.append("Strong credit score")
        credit_status = "GOOD"

    # Determine recommendation
    fail_count = sum(1 for s in [dti_status, ltv_status, credit_status] if s == "FAIL")
    warning_count = sum(1 for s in [dti_status, ltv_status, pti_status, credit_status] if s == "WARNING")

    if fail_count > 0:
        recommendation = "DENY"
        risk_level = "HIGH"
    elif warning_count >= 2:
        recommendation = "REVIEW"
        risk_level = "ELEVATED"
    elif warning_count == 1:
        recommendation = "CONDITIONAL_APPROVE"
        risk_level = "MODERATE"
    else:
        recommendation = "APPROVE"
        risk_level = "LOW"

    # PMI needed?
    requires_pmi = ltv > 0.80

    return {
        "approval_recommendation": recommendation,
        "overall_risk_level": risk_level,
        "metrics": {
            "dti_with_mortgage": {"value": round(dti_with_mortgage, 2), "status": dti_status},
            "ltv": {"value": round(ltv, 4), "status": ltv_status},
            "payment_to_income": {"value": round(payment_to_income, 2), "status": pti_status},
            "credit_score": {"value": credit_score, "status": credit_status},
        },
        "requires_pmi": requires_pmi,
        "strengths": strengths,
        "issues": issues,
    }
