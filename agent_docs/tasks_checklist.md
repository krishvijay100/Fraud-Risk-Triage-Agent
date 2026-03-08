# Build Checklist (Sequence)

This is the required build order.

## Phase 0 — Repo skeleton
- Create backend/ (FastAPI) and web/ (Next.js)
- Create data/ and out/ directories
- Add agent_docs/ (these docs)

## Phase 1 — Schemas + mock data
1) Load the **8 seed cases** already present in `data/mock_cases.json`.

2) Expand the dataset to **20–30 total cases** by generating additional cases based on the seed templates.

3) Ensure the final dataset follows the distribution rules defined in `agent_docs/data_schema.md`:
- 40–50% BENIGN
- 30–40% FRAUD
- 10–20% UNCERTAIN

4) Ensure each alert type appears multiple times.

5) Validate the dataset:
- schema fields match the specification
- case_id values are unique
- label distribution falls within the required ranges

Suggested alert types to include repeatedly:
- unusual_transfer
- account_takeover_signals
- device_reuse_cluster
- velocity_spike
- sanctions_name_match
- onboarding_anomaly

## Phase 2 — Deterministic triage pipeline (backend)
- Normalize + validate
- Enrich (from mock fields)
- Link entities + dedup
- No-go rules
- Deterministic scoring -> reason codes -> confidence
- Tier + SLA mapping
- Auto-clear gating
- Write out/triage_results.json + out/audit_log.jsonl

## Phase 3 — LLM narrative (backend)
- Add narrative generation using Anthropic
- Ensure it only summarizes structured evidence + decision fields
- If LLM fails, leave narrative blank and log failure; do not change decision

## Phase 4 — UI (Next.js)
- Ranked list view + case detail panel
- “Run Triage” button (calls backend)
- Display reason codes, SLA, recommendation, no-go flags
- Override UI: accept/override + required reason, POST /override

## Phase 5 — Evaluation + tests
- Offline eval script prints Precision@10 and Auto-clear error rate
- Unit tests for no-go rules and auto-clear gating
- Final polish: ensure logs are append-only and structured