"""
FastAPI application — triage endpoints.
All recommendations are advisory only; no real holds or blocks are issued.
"""
import json
import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import DATA_FILE, OUT_DIR
from .models import MockCase, OverrideRequest, TriageResult
from .outputs import append_override_log, load_triage_results
from .pipeline import run_triage

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Fraud Triage Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track the latest run_id for override validation
_latest_run_id: str | None = None


def _load_cases() -> list[MockCase]:
    if not DATA_FILE.exists():
        raise HTTPException(status_code=500, detail="mock_cases.json not found")
    raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return [MockCase.model_validate(c) for c in raw]


@app.post("/triage", response_model=TriageResult)
def triage():
    """
    Run the full triage pipeline over all mock cases.
    Writes out/triage_results.json and appends to out/audit_log.jsonl.
    Returns the ranked triage result.
    """
    global _latest_run_id
    cases = _load_cases()
    result = run_triage(cases)
    _latest_run_id = result.run_id
    return result


@app.get("/results")
def results():
    """
    Return the latest triage results from out/triage_results.json.
    Returns 404 if no triage has been run yet.
    """
    data = load_triage_results()
    if data is None:
        raise HTTPException(status_code=404, detail="No triage results found. Run POST /triage first.")
    return data


@app.post("/override")
def override(req: OverrideRequest):
    """
    Record an analyst override or acceptance.
    Appends to out/overrides.jsonl.
    """
    if req.analyst_action not in ("ACCEPT", "OVERRIDE"):
        raise HTTPException(status_code=400, detail="analyst_action must be ACCEPT or OVERRIDE")
    if req.analyst_action == "OVERRIDE" and not req.override_reason:
        raise HTTPException(status_code=400, detail="override_reason is required for OVERRIDE action")

    # Use provided run_id or fall back to latest
    run_id = req.run_id or _latest_run_id or "unknown"
    append_override_log(req, run_id)
    return {"status": "recorded", "case_id": req.case_id, "action": req.analyst_action}


@app.get("/health")
def health():
    return {"status": "ok"}
