# Architecture — Fraud/Risk Triage Agent (Prototype)

## High-level goal
Turn a flat alert backlog into a risk-ranked, investigator-ready queue with:
- deterministic prioritization and reason codes
- evidence enrichment + link analysis
- LLM-generated narrative summaries (evidence-bounded)
- auditability + human override feedback

## System diagram (conceptual)

[Next.js Dashboard]  <--->  [FastAPI Backend]
   |                           |
   | GET /cases                | loads mock cases from data/mock_cases.json
   | POST /triage              | runs pipeline, writes out/triage_results.json
   | POST /override            | records analyst overrides (out/overrides.jsonl)
   | GET /results              | returns latest triage results
   v                           v
Ranked queue UI           Triage pipeline:
                          1) Normalize + validate schema
                          2) Enrich (local mock “tools”)
                          3) Dedup + entity linking
                          4) Guardrails / policy gates (“no-go” rules)
                          5) Deterministic scoring + reason codes + confidence
                          6) Tier + SLA mapping + recommended action
                          7) Narrative generation (LLM, summary-only)
                          8) Persist outputs + audit logs

## Key design choices
### Single “L1 Triage Engine”
One engine owns:
- enrichment orchestration
- rule gates
- scoring/tiering
- output packet assembly

### LLM is narrative-only
- The LLM never sets score/tier/action.
- It receives only a structured “evidence pack” + decision fields and writes a short summary.
- Summary must not introduce new facts.

### Local-only data sources (prototype)
Enrichment is mocked:
- data/mock_cases.json is the source of truth
- “tools” are functions that pull from that structured mock data

## Auto-clear policy
Auto-clear is allowed only if ALL are true:
- risk_tier == LOW (or AUTO_CLEAR if you use a separate tier)
- confidence == HIGH
- no-go rules not triggered
- evidence_completeness >= threshold (defined in security_and_guardrails.md)

## Outputs
The backend produces:
- out/triage_results.json (structured results for UI + metrics)
- out/audit_log.jsonl (append-only decision log)
- out/overrides.jsonl (append-only human override log)