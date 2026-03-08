"""
Triage pipeline — orchestrates all deterministic steps then LLM narrative.
Step order matches agent_docs/architecture.md:
  1) Normalize + validate schema
  2) Enrich
  3) Link entities + dedup
  4) No-go rules
  5) Scoring + reason codes + confidence
  6) Tier + SLA + recommendation
  7) Narrative (LLM, summary-only; failure-safe)
  8) Persist outputs + audit logs
"""
import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone

from .config import SCORING_VERSION, RULES_VERSION, NARRATIVE_MODEL
from .enrichment import build_device_customer_map, link_entities
from .models import MockCase, ModelVersions, TriageDecision, TriageResult
from .narrative import generate_narrative
from .outputs import append_audit_log, write_triage_results
from .rules import evaluate_no_go_rules, compute_tier_sla_recommendation
from .scoring import (
    compute_amount_ratio,
    compute_confidence,
    compute_evidence_completeness,
    compute_risk_score,
)

logger = logging.getLogger(__name__)


def _case_hash(case: MockCase) -> str:
    raw = json.dumps(case.model_dump(), sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _build_evidence_pack(case: MockCase) -> dict:
    amount_ratio = compute_amount_ratio(case)
    return {
        "case_id": case.case_id,
        "alert_type": case.alert_type,
        "amount": case.event.amount,
        "currency": case.event.currency,
        "channel": case.event.channel,
        "country": case.signals.country,
        "new_device": case.signals.new_device,
        "new_beneficiary": case.signals.new_beneficiary,
        "velocity_1h": case.signals.velocity_1h,
        "account_age_days": case.customer.account_age_days,
        "kyc_level": case.customer.kyc_level,
        "avg_amount_30d": case.history.avg_amount_30d,
        "amount_ratio": amount_ratio,
        "prior_alerts_90d": case.history.prior_alerts_90d,
        "prior_confirmed_fraud": case.history.prior_confirmed_fraud,
        # Free-text is untrusted; labeled as such for LLM
        "memo_UNTRUSTED": case.free_text.memo or "",
    }


def run_triage(cases: list[MockCase]) -> TriageResult:
    run_id = str(uuid.uuid4())
    generated_at = datetime.now(timezone.utc).isoformat()

    # Build device→customer map once for the whole batch (entity linking)
    device_customer_map = build_device_customer_map(cases)

    decisions: list[TriageDecision] = []

    for case in cases:
        # ── Step 2: Enrich ────────────────────────────────────────────────
        evidence = _build_evidence_pack(case)

        # ── Step 3: Link entities ─────────────────────────────────────────
        linked = link_entities(case, cases)

        # ── Step 4: No-go rules ───────────────────────────────────────────
        no_go_flags = evaluate_no_go_rules(case, device_customer_map)

        # ── Step 5: Scoring + reason codes + confidence ───────────────────
        risk_score, reason_codes = compute_risk_score(case)
        completeness = compute_evidence_completeness(case)
        confidence = compute_confidence(completeness, no_go_flags)

        # ── Step 6: Tier + SLA + recommendation ───────────────────────────
        tier, sla, recommendation = compute_tier_sla_recommendation(
            risk_score, confidence, no_go_flags, completeness
        )

        # ── Step 7: Narrative (LLM, failure-safe) ────────────────────────
        narrative = ""
        narrative_used = False
        try:
            decision_fields = {
                "risk_score": risk_score,
                "risk_tier": tier,
                "confidence": confidence,
                "reason_codes": reason_codes,
                "no_go_flags": no_go_flags,
                "recommendation": recommendation,
            }
            narrative = generate_narrative(evidence, decision_fields)
            narrative_used = bool(narrative)
        except Exception as exc:
            logger.error("Narrative step failed for %s: %s", case.case_id, exc)
            # Log failure; deterministic decision is unchanged
            append_audit_log({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "run_id": run_id,
                "case_id": case.case_id,
                "event": "NARRATIVE_FAILURE",
                "error": str(exc),
            })

        # ── Step 8: Assemble decision + audit record ──────────────────────
        decision = TriageDecision(
            case_id=case.case_id,
            alert_type=case.alert_type,
            created_at=case.created_at,
            risk_score=risk_score,
            risk_tier=tier,
            confidence=confidence,
            sla_target_minutes=sla,
            recommendation=recommendation,
            reason_codes=reason_codes,
            no_go_flags=no_go_flags,
            evidence=evidence,
            evidence_completeness=round(completeness, 3),
            narrative=narrative,
            linked_entities=linked,
        )
        decisions.append(decision)

        audit_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "case_id": case.case_id,
            "input_hash": _case_hash(case),
            "scoring_version": SCORING_VERSION,
            "rules_version": RULES_VERSION,
            "features_used": [
                "amount", "avg_amount_30d", "country", "new_device",
                "new_beneficiary", "velocity_1h", "account_age_days",
                "kyc_level", "prior_confirmed_fraud", "prior_alerts_90d",
            ],
            "risk_score": risk_score,
            "risk_tier": tier,
            "confidence": confidence,
            "recommendation": recommendation,
            "reason_codes": reason_codes,
            "no_go_flags": no_go_flags,
            "evidence_completeness": round(completeness, 3),
            "narrative_used": narrative_used,
        }
        append_audit_log(audit_record)

    # Sort by tier first, then by risk_score descending within each tier
    _TIER_ORDER = {"URGENT": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "AUTO_CLEAR": 4}
    decisions.sort(key=lambda d: (_TIER_ORDER.get(d.risk_tier, 9), -d.risk_score))

    result = TriageResult(
        run_id=run_id,
        generated_at=generated_at,
        model_versions=ModelVersions(
            scoring_version=SCORING_VERSION,
            rules_version=RULES_VERSION,
            narrative_version=NARRATIVE_MODEL,
        ),
        results=decisions,
    )

    write_triage_results(result)
    return result
