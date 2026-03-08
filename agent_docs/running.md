# Running the Project (Local)

## Prereqs
- Node.js + npm
- Python 3.11+ (native installer; not msys2 Python on Windows)
- Create backend/.env with ANTHROPIC_API_KEY=...

## Start the web app (Next.js)
From web/:
- npm install
- npm run dev

## Start the backend (FastAPI)
From backend/:

  Windows (PowerShell — use native Python):
    py -3.11 -m venv .venv311
    .venv311\Scripts\activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000

  macOS / Linux:
    python3.11 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000

## Run unit tests
From backend/:
  .venv311\Scripts\python.exe -m pytest tests/ -v   (Windows)
  python -m pytest tests/ -v                        (macOS/Linux)

## Run offline evaluation
After running POST /triage at least once, from backend/:
  python eval.py

## Typical demo flow
1) Start backend (uvicorn on :8000)
2) Start web (next dev on :3000)
3) In UI, click "Run Triage" (POST /triage)
4) UI displays ranked results (GET /results)
5) Click a case to view evidence, narrative, reason codes
6) Override a case; confirm entry in out/overrides.jsonl

## Output locations
- out/triage_results.json
- out/audit_log.jsonl
- out/overrides.jsonl
