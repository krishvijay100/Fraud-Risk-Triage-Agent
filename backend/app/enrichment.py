"""
Mock enrichment tools — deterministic, side-effect free.
In prototype, all enrichment data comes from the mock case fields themselves.
"""
from .models import MockCase


def get_customer_profile(case: MockCase) -> dict:
    c = case.customer
    return {
        "customer_id": c.customer_id,
        "account_age_days": c.account_age_days,
        "kyc_level": c.kyc_level,
    }


def get_tx_history_aggregates(case: MockCase) -> dict:
    h = case.history
    return {
        "avg_amount_30d": h.avg_amount_30d,
        "prior_alerts_90d": h.prior_alerts_90d,
        "prior_confirmed_fraud": h.prior_confirmed_fraud,
    }


def get_device_context(case: MockCase) -> dict:
    return {
        "device_id": case.links.device_id,
        "new_device": case.signals.new_device,
        "ip": case.links.ip,
    }


def check_sanctions_pep(case: MockCase) -> dict:
    """
    In prototype: sanctions hit is inferred from alert_type.
    A real implementation would query a sanctions screening service.
    """
    hit = case.alert_type == "sanctions_name_match"
    return {
        "hit": hit,
        "match_type": "NAME_MATCH" if hit else "NONE",
    }


def build_device_customer_map(cases: list[MockCase]) -> dict[str, set[str]]:
    """
    Build {device_id -> set(customer_ids)} across all cases.
    Used to detect device-sharing rings.
    """
    device_map: dict[str, set[str]] = {}
    for case in cases:
        did = case.links.device_id
        if did:
            device_map.setdefault(did, set()).add(case.customer.customer_id)
    return device_map


def link_entities(case: MockCase, all_cases: list[MockCase]) -> dict:
    """
    Return linked entity context:
    - cases sharing the same device_id
    - ring suspicion notes
    """
    device_id = case.links.device_id
    shared_cases = []
    ring_suspicions = []

    if device_id:
        for other in all_cases:
            if other.case_id != case.case_id and other.links.device_id == device_id:
                shared_cases.append({
                    "case_id": other.case_id,
                    "customer_id": other.customer.customer_id,
                    "alert_type": other.alert_type,
                })

        if len(shared_cases) >= 1:
            ring_suspicions.append(
                f"Device {device_id} shared across {len(shared_cases) + 1} accounts"
            )

    return {
        "device_id": device_id,
        "beneficiary_id": case.links.beneficiary_id,
        "merchant_id": case.links.merchant_id,
        "ip": case.links.ip,
        "shared_device_cases": shared_cases,
        "ring_suspicions": ring_suspicions,
    }
