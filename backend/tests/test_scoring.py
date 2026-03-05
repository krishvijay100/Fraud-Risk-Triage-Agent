"""
Unit tests for deterministic risk scoring.
Verifies additive factor logic and reason code stability.
"""
import pytest
from tests.conftest import make_case
from app.scoring import compute_risk_score, compute_evidence_completeness


# ── Amount ratio scoring ──────────────────────────────────────────────────────

def test_amount_far_exceeds_history_adds_20():
    case = make_case(amount=2100.0, avg_amount_30d=100.0)  # ratio = 21x
    score, codes = compute_risk_score(case)
    assert "AMOUNT_FAR_EXCEEDS_HISTORY" in codes


def test_amount_greatly_exceeds_history_adds_15():
    case = make_case(amount=1100.0, avg_amount_30d=100.0)  # ratio = 11x
    score, codes = compute_risk_score(case)
    assert "AMOUNT_GREATLY_EXCEEDS_HISTORY" in codes


def test_amount_exceeds_history_adds_10():
    case = make_case(amount=600.0, avg_amount_30d=100.0)  # ratio = 6x
    score, codes = compute_risk_score(case)
    assert "AMOUNT_EXCEEDS_HISTORY" in codes


def test_amount_above_average_adds_5():
    case = make_case(amount=250.0, avg_amount_30d=100.0)  # ratio = 2.5x
    score, codes = compute_risk_score(case)
    assert "AMOUNT_ABOVE_AVERAGE" in codes


def test_large_amount_no_history():
    case = make_case(amount=600.0, avg_amount_30d=0.0)
    score, codes = compute_risk_score(case)
    assert "LARGE_AMOUNT_NO_HISTORY" in codes


# ── Geo risk ──────────────────────────────────────────────────────────────────

def test_high_risk_geo_adds_15():
    case = make_case(country="NG")
    score, codes = compute_risk_score(case)
    assert "HIGH_RISK_GEO" in codes


def test_medium_risk_geo_adds_8():
    case = make_case(country="PH")
    score, codes = compute_risk_score(case)
    assert "MEDIUM_RISK_GEO" in codes


def test_low_risk_geo_no_code():
    case = make_case(country="US")
    score, codes = compute_risk_score(case)
    assert "HIGH_RISK_GEO" not in codes
    assert "MEDIUM_RISK_GEO" not in codes


# ── Device + beneficiary signals ──────────────────────────────────────────────

def test_new_device_adds_reason_code():
    case = make_case(new_device=True)
    _, codes = compute_risk_score(case)
    assert "NEW_DEVICE" in codes


def test_known_device_no_code():
    case = make_case(new_device=False)
    _, codes = compute_risk_score(case)
    assert "NEW_DEVICE" not in codes


def test_new_beneficiary_adds_reason_code():
    case = make_case(new_beneficiary=True)
    _, codes = compute_risk_score(case)
    assert "NEW_BENEFICIARY" in codes


# ── Velocity ──────────────────────────────────────────────────────────────────

def test_high_velocity_adds_code():
    case = make_case(velocity_1h=12)
    _, codes = compute_risk_score(case)
    assert "HIGH_VELOCITY" in codes


def test_elevated_velocity_adds_code():
    case = make_case(velocity_1h=7)
    _, codes = compute_risk_score(case)
    assert "ELEVATED_VELOCITY" in codes


# ── Account age ───────────────────────────────────────────────────────────────

def test_very_new_account_adds_code():
    case = make_case(account_age_days=3)
    _, codes = compute_risk_score(case)
    assert "VERY_NEW_ACCOUNT" in codes


def test_old_account_no_age_code():
    case = make_case(account_age_days=500)
    _, codes = compute_risk_score(case)
    assert "VERY_NEW_ACCOUNT" not in codes
    assert "NEW_ACCOUNT" not in codes
    assert "YOUNG_ACCOUNT" not in codes


# ── Prior fraud ───────────────────────────────────────────────────────────────

def test_prior_confirmed_fraud_adds_code():
    case = make_case(prior_confirmed_fraud=1)
    _, codes = compute_risk_score(case)
    assert "PRIOR_CONFIRMED_FRAUD" in codes


# ── Score is capped at 100 ────────────────────────────────────────────────────

def test_score_capped_at_100():
    # Maximise every signal
    case = make_case(
        country="NG", amount=10000.0, avg_amount_30d=100.0,
        new_device=True, new_beneficiary=True, velocity_1h=15,
        account_age_days=1, kyc_level="NONE",
        prior_confirmed_fraud=1, prior_alerts_90d=5,
        alert_type="sanctions_name_match",
    )
    score, _ = compute_risk_score(case)
    assert score == 100


# ── Reason code stability ─────────────────────────────────────────────────────

def test_same_input_produces_same_reason_codes():
    case = make_case(
        country="RU", amount=2000.0, avg_amount_30d=200.0,
        new_device=True, velocity_1h=8,
    )
    _, codes_a = compute_risk_score(case)
    _, codes_b = compute_risk_score(case)
    assert codes_a == codes_b


def test_different_inputs_produce_different_codes():
    case_a = make_case(country="NG", amount=5000.0, avg_amount_30d=100.0)
    case_b = make_case(country="US", amount=80.0, avg_amount_30d=100.0)
    _, codes_a = compute_risk_score(case_a)
    _, codes_b = compute_risk_score(case_b)
    assert codes_a != codes_b


# ── Evidence completeness ─────────────────────────────────────────────────────

def test_full_evidence_completeness_is_1():
    case = make_case()
    assert compute_evidence_completeness(case) == 1.0


def test_completeness_less_than_1_when_device_missing():
    from app.models import MockCase, MockCaseCustomer, MockCaseEvent, MockCaseSignals
    from app.models import MockCaseHistory, MockCaseLinks, MockCaseFreeText, MockCaseLabel
    case = MockCase(
        case_id="T-INC",
        alert_type="unusual_transfer",
        created_at="2026-03-03T12:00:00Z",
        customer=MockCaseCustomer(customer_id="U-INC", account_age_days=100, kyc_level="FULL"),
        event=MockCaseEvent(amount=100, currency="USD", channel="card"),
        signals=MockCaseSignals(new_device=False, new_beneficiary=False, country="US", velocity_1h=1),
        history=MockCaseHistory(avg_amount_30d=100, prior_alerts_90d=0, prior_confirmed_fraud=0),
        links=MockCaseLinks(device_id=None),
        free_text=MockCaseFreeText(memo=""),
        label=MockCaseLabel(outcome="BENIGN"),
    )
    completeness = compute_evidence_completeness(case)
    assert completeness < 1.0
