# Security, Guardrails, and Hallucination Controls

## Threat model (prototype-level)
- Sensitive data exposure (PII, device IDs, IPs)
- Prompt injection via free_text (memo, support notes)
- Hallucinated narratives that invent evidence or relationships
- Over-automation (auto-clearing risky cases)

## Core guardrails (must implement)
### 1) Evidence-bounded narrative (LLM)
- LLM receives only:
  - structured evidence (numbers/flags)
  - reason codes
  - final deterministic decision fields
- LLM must NOT:
  - introduce new facts
  - claim prior fraud history unless present in evidence
  - state certainty when confidence is LOW/MEDIUM
- If evidence is missing, narrative must say “Not available.”

### 2) No-go rules (force human review / block auto-clear)
Examples (keep at least these categories):
- SANCTIONS_HIT
- EVIDENCE_INCOMPLETE_CRITICAL_FIELDS
- ENTITY_RING_CLUSTER_ABOVE_THRESHOLD
- HIGH_RISK_GEO_LARGE_AMOUNT_NEW_DEVICE (combo)

No-go rules must be recorded in:
- no_go_flags
- audit log

### 3) Auto-clear gating
Auto-clear permitted only when:
- risk_tier == LOW (or AUTO_CLEAR, if used)
- confidence == HIGH
- no_go_flags empty
- evidence_completeness >= threshold (e.g., 0.85)

### 4) Data minimization + logging hygiene
- Keep UI payload minimal (only what is needed to review).
- Mask sensitive identifiers where possible (e.g., show last 4).
- Never log secrets. Store ANTHROPIC_API_KEY only in .env.

### 5) Safe failure behavior
If:
- enrichment fails
- LLM fails
- schema validation fails
Then:
- do NOT auto-clear
- route to MEDIUM/HIGH (or explicit “NEEDS_REVIEW”) with low confidence
- write an audit record explaining the failure mode