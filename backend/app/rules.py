"""
No-go rule evaluation — deterministic, reproducible.
No-go flags force human review and block auto-clear.
"""
from .models import MockCase
from .config import HIGH_RISK_COUNTRIES, LARGE_AMOUNT_THRESHOLD, RING_CLUSTER_THRESHOLD


def evaluate_no_go_rules(
    case: MockCase,
    device_customer_map: dict[str, set[str]],
) -> list[str]:
    """
    Return list of triggered no-go rule codes.

    Args:
        case: the alert case being triaged
        device_customer_map: {device_id -> set of customer_ids using that device}
                             built from the full case set before pipeline runs
    """
    flags: list[str] = []

    # Rule 1: SANCTIONS_HIT
    # Any sanctions_name_match alert mandates human review.
    if case.alert_type == "sanctions_name_match":
        flags.append("SANCTIONS_HIT")

    # Rule 2: HIGH_RISK_GEO_LARGE_AMOUNT_NEW_DEVICE
    # Combination of high-risk geography + large amount + new/unknown device.
    if (
        case.signals.country in HIGH_RISK_COUNTRIES
        and case.event.amount > LARGE_AMOUNT_THRESHOLD
        and case.signals.new_device
    ):
        flags.append("HIGH_RISK_GEO_LARGE_AMOUNT_NEW_DEVICE")

    # Rule 3: ENTITY_RING_CLUSTER_ABOVE_THRESHOLD
    # Device shared by RING_CLUSTER_THRESHOLD+ different customer accounts.
    device_id = case.links.device_id
    if device_id and device_id in device_customer_map:
        customers_using_device = device_customer_map[device_id]
        if len(customers_using_device) >= RING_CLUSTER_THRESHOLD:
            flags.append("ENTITY_RING_CLUSTER_ABOVE_THRESHOLD")

    # Rule 4: EVIDENCE_INCOMPLETE_CRITICAL_FIELDS
    # Missing critical fields needed to make a safe triage decision.
    critical_fields_missing = (
        case.links.device_id is None
        or case.signals.country is None
        or case.event.amount is None
    )
    if critical_fields_missing:
        flags.append("EVIDENCE_INCOMPLETE_CRITICAL_FIELDS")

    return flags


def check_auto_clear(
    risk_score: int,
    confidence: str,
    no_go_flags: list[str],
    completeness: float,
    score_threshold: int = 20,
    completeness_threshold: float = 0.85,
) -> bool:
    """
    Return True only when ALL auto-clear conditions are satisfied.
    This is the only path to automated clearing — all conditions must hold.
    """
    return (
        risk_score < score_threshold
        and confidence == "HIGH"
        and len(no_go_flags) == 0
        and completeness >= completeness_threshold
    )


def compute_tier_sla_recommendation(
    risk_score: int,
    confidence: str,
    no_go_flags: list[str],
    completeness: float,
) -> tuple[str, int, str]:
    """
    Return (risk_tier, sla_target_minutes, recommendation).
    No-go flags force minimum MEDIUM tier.
    Auto-clear is only allowed if check_auto_clear passes.
    """
    from .config import (
        TIER_URGENT_MIN, TIER_HIGH_MIN, TIER_MEDIUM_MIN,
        SLA_MAP, RECOMMENDATION_MAP,
    )

    auto_clear = check_auto_clear(risk_score, confidence, no_go_flags, completeness)

    if auto_clear:
        tier = "AUTO_CLEAR"
    elif risk_score >= TIER_URGENT_MIN:
        tier = "URGENT"
    elif risk_score >= TIER_HIGH_MIN:
        tier = "HIGH"
    elif risk_score >= TIER_MEDIUM_MIN:
        tier = "MEDIUM"
    else:
        tier = "LOW"

    # No-go flags upgrade tier to at least MEDIUM
    if no_go_flags and tier in ("LOW", "AUTO_CLEAR"):
        tier = "MEDIUM"

    return tier, SLA_MAP[tier], RECOMMENDATION_MAP[tier]
