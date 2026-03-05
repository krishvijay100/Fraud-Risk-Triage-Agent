# Evaluation & Verification

Goal: produce simple, defensible metrics on mock labeled data.

## Ground-truth labels
Each mock case includes:
label.outcome in {FRAUD, BENIGN, UNCERTAIN}

UNCERTAIN cases are excluded from metric denominators unless explicitly included.

## Metrics (required)
### 1) Precision@10
Definition:
- Take the 10 highest risk-scored cases (or fewer if <10).
- Precision@10 = (# of FRAUD in top 10) / (10)

If fewer than 10 cases, use K = total cases.

Why it matters:
- Demonstrates the ranked queue puts true risk at the top.

### 2) Auto-clear error rate (false negative rate for auto-clear)
Definition:
- Among cases auto-cleared (risk_tier == AUTO_CLEAR OR auto_clear == true):
- Auto-clear error rate = (# labeled FRAUD among auto-cleared) / (# auto-cleared)

Target:
- As close to 0 as possible in a demo.

Why it matters:
- Directly measures safety of automation.

## Verification steps (recommended)
1) Run backend unit tests:
- rules/no-go evaluation
- reason code mapping
- auto-clear gating logic

2) Run offline eval script:
- loads out/triage_results.json + data/mock_cases.json
- prints Precision@10 and Auto-clear error rate
- optionally prints tier distribution and top reason codes summary

3) Smoke test UI:
- dashboard loads results
- clicking a case shows evidence + narrative + reason codes
- override produces an entry in out/overrides.jsonl