"""
Unit tests for no-go rule evaluation.
Verifies each rule triggers (and doesn't trigger) under the correct conditions.
"""
import pytest
from tests.conftest import make_case
from app.rules import evaluate_no_go_rules


# ── SANCTIONS_HIT ──────────────────────────────────────────────────────────────

def test_sanctions_hit_triggers_for_sanctions_alert():
    case = make_case(alert_type="sanctions_name_match")
    flags = evaluate_no_go_rules(case, {})
    assert "SANCTIONS_HIT" in flags


def test_sanctions_hit_not_triggered_for_other_alert_types():
    for alert_type in ["unusual_transfer", "velocity_spike", "device_reuse_cluster",
                       "account_takeover_signals", "onboarding_anomaly"]:
        case = make_case(alert_type=alert_type)
        flags = evaluate_no_go_rules(case, {})
        assert "SANCTIONS_HIT" not in flags, f"Unexpected SANCTIONS_HIT for {alert_type}"


# ── HIGH_RISK_GEO_LARGE_AMOUNT_NEW_DEVICE ────────────────────────────────────

def test_high_risk_geo_combo_triggers_all_three_conditions():
    case = make_case(country="NG", amount=1500.0, new_device=True)
    flags = evaluate_no_go_rules(case, {})
    assert "HIGH_RISK_GEO_LARGE_AMOUNT_NEW_DEVICE" in flags


def test_high_risk_geo_combo_not_triggered_known_device():
    case = make_case(country="NG", amount=1500.0, new_device=False)
    flags = evaluate_no_go_rules(case, {})
    assert "HIGH_RISK_GEO_LARGE_AMOUNT_NEW_DEVICE" not in flags


def test_high_risk_geo_combo_not_triggered_small_amount():
    # amount must be > 1000
    case = make_case(country="NG", amount=999.0, new_device=True)
    flags = evaluate_no_go_rules(case, {})
    assert "HIGH_RISK_GEO_LARGE_AMOUNT_NEW_DEVICE" not in flags


def test_high_risk_geo_combo_not_triggered_low_risk_country():
    case = make_case(country="US", amount=5000.0, new_device=True)
    flags = evaluate_no_go_rules(case, {})
    assert "HIGH_RISK_GEO_LARGE_AMOUNT_NEW_DEVICE" not in flags


def test_all_high_risk_countries_trigger():
    for country in ["NG", "RU", "KP", "IR", "SY"]:
        case = make_case(country=country, amount=2000.0, new_device=True)
        flags = evaluate_no_go_rules(case, {})
        assert "HIGH_RISK_GEO_LARGE_AMOUNT_NEW_DEVICE" in flags, f"Missing flag for {country}"


# ── ENTITY_RING_CLUSTER_ABOVE_THRESHOLD ──────────────────────────────────────

def test_ring_cluster_triggers_when_device_shared_by_two_customers():
    # D-RING shared by U-A and U-B (threshold is 2)
    device_map = {"D-RING": {"U-A", "U-B"}}
    case = make_case(case_id="T-RING", device_id="D-RING")
    # case customer is U-T-RING; device_map has 2 customers → triggers
    flags = evaluate_no_go_rules(case, device_map)
    assert "ENTITY_RING_CLUSTER_ABOVE_THRESHOLD" in flags


def test_ring_cluster_not_triggered_single_customer():
    device_map = {"D-SOLO": {"U-ONLY"}}
    case = make_case(case_id="T-SOLO", device_id="D-SOLO")
    flags = evaluate_no_go_rules(case, device_map)
    assert "ENTITY_RING_CLUSTER_ABOVE_THRESHOLD" not in flags


def test_ring_cluster_not_triggered_unknown_device():
    device_map = {}
    case = make_case(device_id="D-UNKNOWN")
    flags = evaluate_no_go_rules(case, device_map)
    assert "ENTITY_RING_CLUSTER_ABOVE_THRESHOLD" not in flags


# ── EVIDENCE_INCOMPLETE_CRITICAL_FIELDS ──────────────────────────────────────

def test_incomplete_evidence_triggers_when_device_id_missing():
    from app.models import MockCase, MockCaseCustomer, MockCaseEvent, MockCaseSignals
    from app.models import MockCaseHistory, MockCaseLinks, MockCaseFreeText, MockCaseLabel
    case = MockCase(
        case_id="T-MISSING",
        alert_type="unusual_transfer",
        created_at="2026-03-03T12:00:00Z",
        customer=MockCaseCustomer(customer_id="U-MISS", account_age_days=100, kyc_level="FULL"),
        event=MockCaseEvent(amount=500, currency="USD", channel="card"),
        signals=MockCaseSignals(new_device=False, new_beneficiary=False, country="US", velocity_1h=1),
        history=MockCaseHistory(avg_amount_30d=100, prior_alerts_90d=0, prior_confirmed_fraud=0),
        links=MockCaseLinks(device_id=None),  # missing
        free_text=MockCaseFreeText(memo=""),
        label=MockCaseLabel(outcome="BENIGN"),
    )
    flags = evaluate_no_go_rules(case, {})
    assert "EVIDENCE_INCOMPLETE_CRITICAL_FIELDS" in flags


def test_no_flags_for_clean_low_risk_case():
    case = make_case(country="US", amount=50.0, new_device=False, alert_type="velocity_spike")
    flags = evaluate_no_go_rules(case, {"D-TEST": {"U-T-001"}})
    assert flags == []
