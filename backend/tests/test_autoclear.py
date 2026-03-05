"""
Unit tests for auto-clear gating logic.
All conditions must hold simultaneously — any single failure blocks auto-clear.
"""
import pytest
from app.rules import check_auto_clear, compute_tier_sla_recommendation


# ── check_auto_clear ──────────────────────────────────────────────────────────

def test_autoclear_allowed_when_all_conditions_met():
    assert check_auto_clear(
        risk_score=5,
        confidence="HIGH",
        no_go_flags=[],
        completeness=1.0,
    ) is True


def test_autoclear_allowed_at_score_boundary():
    # score < 20 → allowed; score == 20 → blocked
    assert check_auto_clear(19, "HIGH", [], 1.0) is True
    assert check_auto_clear(20, "HIGH", [], 1.0) is False


def test_autoclear_blocked_by_any_no_go_flag():
    for flag in ["SANCTIONS_HIT", "HIGH_RISK_GEO_LARGE_AMOUNT_NEW_DEVICE",
                 "ENTITY_RING_CLUSTER_ABOVE_THRESHOLD", "EVIDENCE_INCOMPLETE_CRITICAL_FIELDS"]:
        result = check_auto_clear(5, "HIGH", [flag], 1.0)
        assert result is False, f"Auto-clear should be blocked by {flag}"


def test_autoclear_blocked_by_medium_confidence():
    assert check_auto_clear(5, "MEDIUM", [], 1.0) is False


def test_autoclear_blocked_by_low_confidence():
    assert check_auto_clear(5, "LOW", [], 1.0) is False


def test_autoclear_blocked_by_low_completeness():
    # threshold is 0.85
    assert check_auto_clear(5, "HIGH", [], 0.84) is False
    assert check_auto_clear(5, "HIGH", [], 0.85) is True


def test_autoclear_blocked_by_high_score():
    assert check_auto_clear(50, "HIGH", [], 1.0) is False


def test_autoclear_requires_all_conditions_simultaneously():
    # Pass all except one at a time
    assert check_auto_clear(5, "HIGH", [], 1.0) is True

    # Fail score
    assert check_auto_clear(25, "HIGH", [], 1.0) is False
    # Fail confidence
    assert check_auto_clear(5, "MEDIUM", [], 1.0) is False
    # Fail flags
    assert check_auto_clear(5, "HIGH", ["SANCTIONS_HIT"], 1.0) is False
    # Fail completeness
    assert check_auto_clear(5, "HIGH", [], 0.5) is False


# ── compute_tier_sla_recommendation (auto-clear path) ────────────────────────

def test_tier_is_auto_clear_when_all_gates_pass():
    tier, sla, rec = compute_tier_sla_recommendation(5, "HIGH", [], 1.0)
    assert tier == "AUTO_CLEAR"
    assert sla == 0
    assert rec == "CLEAR"


def test_tier_is_low_when_score_too_high_for_autoclear():
    tier, sla, rec = compute_tier_sla_recommendation(25, "HIGH", [], 1.0)
    assert tier == "LOW"
    assert sla == 1440
    assert rec == "MONITOR"


def test_tier_is_medium_when_no_go_flag_present():
    # Low score but has a no-go flag — must route to MEDIUM
    tier, sla, rec = compute_tier_sla_recommendation(5, "HIGH", ["SANCTIONS_HIT"], 1.0)
    assert tier == "MEDIUM"
    assert sla == 240
    assert rec == "STEP_UP"


def test_tier_urgent_for_very_high_score():
    tier, sla, rec = compute_tier_sla_recommendation(90, "HIGH", [], 1.0)
    assert tier == "URGENT"
    assert sla == 15
    assert rec == "HOLD_RECOMMENDED"


def test_tier_high_for_high_score():
    tier, sla, rec = compute_tier_sla_recommendation(65, "HIGH", [], 1.0)
    assert tier == "HIGH"
    assert sla == 60
    assert rec == "ESCALATE_L2"


def test_tier_medium_for_medium_score():
    tier, sla, rec = compute_tier_sla_recommendation(45, "HIGH", [], 1.0)
    assert tier == "MEDIUM"
    assert sla == 240
    assert rec == "STEP_UP"


def test_no_go_flag_upgrades_low_to_medium():
    tier, _, _ = compute_tier_sla_recommendation(10, "HIGH", ["SANCTIONS_HIT"], 1.0)
    assert tier == "MEDIUM"


def test_no_go_flag_does_not_downgrade_high():
    # If score is already HIGH, no-go flag shouldn't reduce the tier
    tier, _, _ = compute_tier_sla_recommendation(65, "HIGH", ["SANCTIONS_HIT"], 1.0)
    assert tier == "HIGH"
