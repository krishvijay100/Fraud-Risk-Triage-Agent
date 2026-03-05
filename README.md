# Fraud / Risk Triage Agent

A lightweight, auditable AI-assisted triage system for fintech fraud alert queues. Converts a flat alert backlog into a risk-ranked queue with deterministic scoring, investigator-ready narratives, and human override support.

## What it does

- Ranks alerts by a deterministic risk score (0–100) with stable reason codes
- Applies no-go rules to block unsafe automation (sanctions hits, device rings, high-risk geo combos)
- Auto-clears only LOW-risk, HIGH-confidence cases with no flags — safety-gated
- Generates LLM narrative summaries (evidence-bounded, never decision-making)
- Logs every decision to an append-only audit trail
- Provides a dashboard UI for review, acceptance, and analyst overrides

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, Pydantic v2 |
| Narrative | Anthropic Claude (claude-haiku-4-5) |
| Frontend | Next.js 14, TypeScript |
| Data | JSON mock dataset (25 labeled cases) |

## Project structure

```
backend/
  app/
    config.py       # thresholds, geo sets, SLA maps
    models.py       # Pydantic schemas
    scoring.py      # deterministic risk scoring
    rules.py        # no-go rules + auto-clear gating
    enrichment.py   # mock enrichment tools + entity linking
    narrative.py    # LLM narrative (failure-safe)
    pipeline.py     # 8-step triage orchestration
    outputs.py      # file persistence helpers
    main.py         # FastAPI endpoints
  tests/            # 49 unit tests
  eval.py           # offline evaluation script
web/
  src/app/page.tsx  # single-page dashboard
data/
  mock_cases.json   # 25 labeled alert cases
out/                # triage_results.json, audit_log.jsonl, overrides.jsonl
```

## Setup

**Backend** — from `backend/`:
```bash
# Windows (use native Python, not msys2)
py -3.11 -m venv .venv311
.venv311\Scripts\activate
pip install -r requirements.txt

# macOS / Linux
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env`:
```
ANTHROPIC_API_KEY=your_key_here
```

Start the server:
```bash
uvicorn app.main:app --reload --port 8000
```

**Frontend** — from `web/`:
```bash
npm install
npm run dev   # http://localhost:3000
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/triage` | Run pipeline over all cases, write outputs |
| `GET` | `/results` | Return latest `out/triage_results.json` |
| `POST` | `/override` | Record analyst accept or override |

## Tests & evaluation

```bash
# Unit tests (from backend/)
python -m pytest tests/ -v

# Offline eval — requires a prior POST /triage run
python eval.py
```

Verified metrics on the 25-case dataset:

| Metric | Result |
|--------|--------|
| Precision@10 | 0.90 |
| Auto-clear error rate | 0.00 |
| Unit tests | 49 / 49 passed |
