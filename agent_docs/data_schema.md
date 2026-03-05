# Data & Output Schemas

This project uses one input file:
- data/mock_cases.json

And produces:
- out/triage_results.json
- out/audit_log.jsonl
- out/overrides.jsonl

## 1) Input schema: MockCase (data/mock_cases.json)
An array of cases, each with minimally:
- case_id (string)
- alert_type (string)
- created_at (ISO string)
- customer (object)
- event (object)               // the triggering activity
- signals (object)             // device, geo, velocity, etc.
- history (object)             // simplified aggregates and prior outcomes
- links (object)               // entities for linking (device_id, beneficiary_id, ip, etc.)
- free_text (object)           // memos/notes (untrusted)
- label (object)               // ground truth for eval

### Example (abbreviated)
{
  "case_id": "C-001",
  "alert_type": "unusual_transfer",
  "created_at": "2026-03-03T12:00:00Z",
  "customer": { "customer_id": "U-1001", "account_age_days": 12, "kyc_level": "BASIC" },
  "event": { "amount": 4200, "currency": "USD", "channel": "wallet_transfer" },
  "signals": { "new_device": true, "new_beneficiary": true, "country": "NG", "velocity_1h": 6 },
  "history": { "avg_amount_30d": 180, "prior_alerts_90d": 2, "prior_confirmed_fraud": 0 },
  "links": { "device_id": "D-777", "beneficiary_id": "B-900", "ip": "1.2.3.4" },
  "free_text": { "memo": "rent payment" },
  "label": { "outcome": "FRAUD" }
}

### label.outcome enum
- FRAUD
- BENIGN
- UNCERTAIN

## 2) Output schema: TriageResult (out/triage_results.json)
{
  "run_id": "string",
  "generated_at": "ISO string",
  "model_versions": {
    "scoring_version": "string",
    "rules_version": "string",
    "narrative_version": "string"
  },
  "results": [ TriageDecision, ... ],
  "metrics": { ... } // computed offline or by backend, see evaluation.md
}

### TriageDecision
Required fields:
- case_id
- risk_score              // 0-100
- risk_tier               // AUTO_CLEAR | LOW | MEDIUM | HIGH | URGENT
- confidence              // LOW | MEDIUM | HIGH
- sla_target_minutes
- recommendation          // CLEAR | ESCALATE_L2 | STEP_UP | HOLD_RECOMMENDED | MONITOR
- reason_codes            // array of stable strings
- no_go_flags             // array of strings for triggered no-go rules (can be empty)
- evidence                // structured evidence used
- narrative               // LLM summary (optional, may be empty if LLM disabled)
- linked_entities         // results of linking/dedup

## 3) Audit log schema (out/audit_log.jsonl)
Append-only JSON lines. Each line includes:
- timestamp
- run_id
- case_id
- input_hash (or a stable reference)
- scoring_version, rules_version
- features_used (list)
- risk_score, risk_tier, confidence
- recommendation
- reason_codes
- no_go_flags
- evidence_completeness
- narrative_used (boolean)

## 4) Overrides schema (out/overrides.jsonl)
Append-only JSON lines:
- timestamp
- run_id
- case_id
- analyst_action        // ACCEPT | OVERRIDE
- final_decision        // same enum as recommendation
- override_reason       // required if OVERRIDE
- notes (optional)

---

## Mock Dataset Expansion Rules (REQUIRED)

The repository initially includes **8 seed cases** in `data/mock_cases.json`.
These seed cases are the templates and distribution anchors.

When building the prototype dataset, expand this file to **20–30 total cases**.

### Expansion requirements
1) **Build off the 8 seed cases**
- Preserve the schema and field structure.
- Create new cases by varying:
  - amount, channel, velocity
  - new_device/new_beneficiary flags
  - country/geo risk
  - history aggregates and prior outcomes
  - entity links (device_id/beneficiary_id/ip/merchant_id)

2) **Maintain realistic fintech fraud patterns**
New cases should cover common scenarios:
- account takeover signals
- unusual transfers
- device reuse / rings
- onboarding anomalies
- velocity spikes
- sanctions name matches

3) **Maintain this label distribution across the final dataset**
- BENIGN: 40–50%
- FRAUD: 30–40%
- UNCERTAIN: 10–20%

Example for 25 cases:
- BENIGN: 10–12
- FRAUD: 8–10
- UNCERTAIN: 3–5

4) **Ensure each alert_type appears multiple times**
This supports clear evaluation of ranking behavior.

5) **Avoid duplicates**
Each case must have:
- unique case_id
- distinct combinations of signals/history/links