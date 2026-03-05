from pydantic import BaseModel, Field
from typing import Optional, Any


# ── Input schema ──────────────────────────────────────────────────────────────

class MockCaseCustomer(BaseModel):
    customer_id: str
    account_age_days: int
    kyc_level: str  # NONE | BASIC | FULL


class MockCaseEvent(BaseModel):
    amount: float
    currency: str
    channel: str


class MockCaseSignals(BaseModel):
    new_device: bool
    new_beneficiary: bool
    country: str
    velocity_1h: int


class MockCaseHistory(BaseModel):
    avg_amount_30d: float
    prior_alerts_90d: int
    prior_confirmed_fraud: int


class MockCaseLinks(BaseModel):
    device_id: Optional[str] = None
    beneficiary_id: Optional[str] = None
    merchant_id: Optional[str] = None
    ip: Optional[str] = None


class MockCaseFreeText(BaseModel):
    memo: Optional[str] = None


class MockCaseLabel(BaseModel):
    outcome: str  # FRAUD | BENIGN | UNCERTAIN


class MockCase(BaseModel):
    case_id: str
    alert_type: str
    created_at: str
    customer: MockCaseCustomer
    event: MockCaseEvent
    signals: MockCaseSignals
    history: MockCaseHistory
    links: MockCaseLinks
    free_text: MockCaseFreeText
    label: MockCaseLabel


# ── Output schema ─────────────────────────────────────────────────────────────

class TriageDecision(BaseModel):
    case_id: str
    alert_type: str
    created_at: str
    risk_score: int                    # 0–100
    risk_tier: str                     # AUTO_CLEAR | LOW | MEDIUM | HIGH | URGENT
    confidence: str                    # LOW | MEDIUM | HIGH
    sla_target_minutes: int
    recommendation: str                # CLEAR | MONITOR | STEP_UP | ESCALATE_L2 | HOLD_RECOMMENDED
    reason_codes: list[str]
    no_go_flags: list[str]
    evidence: dict[str, Any]
    evidence_completeness: float
    narrative: str
    linked_entities: dict[str, Any]


class ModelVersions(BaseModel):
    scoring_version: str
    rules_version: str
    narrative_version: str


class TriageResult(BaseModel):
    run_id: str
    generated_at: str
    model_versions: ModelVersions
    results: list[TriageDecision]
    metrics: dict[str, Any] = Field(default_factory=dict)


# ── Override schema ───────────────────────────────────────────────────────────

class OverrideRequest(BaseModel):
    run_id: str
    case_id: str
    analyst_action: str               # ACCEPT | OVERRIDE
    final_decision: Optional[str] = None
    override_reason: Optional[str] = None
    notes: Optional[str] = None
