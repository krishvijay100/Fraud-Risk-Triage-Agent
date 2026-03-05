"""
Deterministic risk scoring.
All logic here is rule-based and reproducible — no LLM involved.
"""
from .models import MockCase
from .config import HIGH_RISK_COUNTRIES, MEDIUM_RISK_COUNTRIES


def compute_risk_score(case: MockCase) -> tuple[int, list[str]]:
    """Return (risk_score 0-100, reason_codes list)."""
    score = 0
    reason_codes: list[str] = []

    # 1. Amount vs history ratio
    avg = case.history.avg_amount_30d
    amount = case.event.amount
    if avg > 0:
        ratio = amount / avg
        if ratio > 20:
            score += 20
            reason_codes.append("AMOUNT_FAR_EXCEEDS_HISTORY")
        elif ratio > 10:
            score += 15
            reason_codes.append("AMOUNT_GREATLY_EXCEEDS_HISTORY")
        elif ratio > 5:
            score += 10
            reason_codes.append("AMOUNT_EXCEEDS_HISTORY")
        elif ratio > 2:
            score += 5
            reason_codes.append("AMOUNT_ABOVE_AVERAGE")
    else:
        # No transaction history — score by raw amount
        if amount > 500:
            score += 15
            reason_codes.append("LARGE_AMOUNT_NO_HISTORY")
        elif amount > 100:
            score += 8
            reason_codes.append("MODERATE_AMOUNT_NO_HISTORY")

    # 2. Geographic risk
    country = case.signals.country
    if country in HIGH_RISK_COUNTRIES:
        score += 15
        reason_codes.append("HIGH_RISK_GEO")
    elif country in MEDIUM_RISK_COUNTRIES:
        score += 8
        reason_codes.append("MEDIUM_RISK_GEO")

    # 3. New device
    if case.signals.new_device:
        score += 10
        reason_codes.append("NEW_DEVICE")

    # 4. New beneficiary
    if case.signals.new_beneficiary:
        score += 8
        reason_codes.append("NEW_BENEFICIARY")

    # 5. Transaction velocity
    vel = case.signals.velocity_1h
    if vel > 10:
        score += 15
        reason_codes.append("HIGH_VELOCITY")
    elif vel > 5:
        score += 10
        reason_codes.append("ELEVATED_VELOCITY")
    elif vel > 3:
        score += 5
        reason_codes.append("MODERATE_VELOCITY")

    # 6. Account age
    age = case.customer.account_age_days
    if age < 7:
        score += 15
        reason_codes.append("VERY_NEW_ACCOUNT")
    elif age < 30:
        score += 10
        reason_codes.append("NEW_ACCOUNT")
    elif age < 90:
        score += 5
        reason_codes.append("YOUNG_ACCOUNT")

    # 7. KYC level
    kyc = case.customer.kyc_level
    if kyc == "NONE":
        score += 10
        reason_codes.append("NO_KYC")
    elif kyc == "BASIC":
        score += 5
        reason_codes.append("BASIC_KYC")

    # 8. Prior confirmed fraud
    if case.history.prior_confirmed_fraud > 0:
        score += 20
        reason_codes.append("PRIOR_CONFIRMED_FRAUD")

    # 9. Prior alerts (90-day window)
    alerts = case.history.prior_alerts_90d
    if alerts > 3:
        score += 10
        reason_codes.append("MULTIPLE_PRIOR_ALERTS")
    elif alerts > 1:
        score += 5
        reason_codes.append("PRIOR_ALERTS")
    elif alerts > 0:
        score += 3
        reason_codes.append("PRIOR_ALERT")

    # 10. Alert type base risk
    alert_type_scores = {
        "sanctions_name_match": 10,
        "account_takeover_signals": 8,
        "device_reuse_cluster": 5,
        "unusual_transfer": 3,
        "velocity_spike": 2,
        "onboarding_anomaly": 2,
    }
    at_score = alert_type_scores.get(case.alert_type, 2)
    score += at_score
    reason_codes.append(f"ALERT_TYPE_{case.alert_type.upper()}")

    return min(score, 100), reason_codes


def compute_evidence_completeness(case: MockCase) -> float:
    """Return ratio of expected evidence fields that are present (0.0–1.0)."""
    checks = [
        case.event.amount is not None,
        case.event.currency is not None,
        case.signals.new_device is not None,
        case.signals.new_beneficiary is not None,
        case.signals.country is not None,
        case.signals.velocity_1h is not None,
        case.history.avg_amount_30d is not None,
        case.history.prior_alerts_90d is not None,
        case.history.prior_confirmed_fraud is not None,
        case.links.device_id is not None,
    ]
    return sum(checks) / len(checks)


def compute_confidence(completeness: float, no_go_flags: list[str]) -> str:
    """Determine confidence level based on evidence quality."""
    if "EVIDENCE_INCOMPLETE_CRITICAL_FIELDS" in no_go_flags:
        return "LOW"
    if completeness >= 0.85:
        return "HIGH"
    if completeness >= 0.6:
        return "MEDIUM"
    return "LOW"


def compute_amount_ratio(case: MockCase) -> float:
    avg = case.history.avg_amount_30d
    if avg > 0:
        return round(case.event.amount / avg, 2)
    return 0.0
