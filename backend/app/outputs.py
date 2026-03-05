"""
Write tools — persist triage outputs.
All writes are append-only for audit/override logs.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from .config import OUT_DIR
from .models import TriageResult, OverrideRequest


def _ensure_out_dir() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def write_triage_results(result: TriageResult) -> None:
    _ensure_out_dir()
    path = OUT_DIR / "triage_results.json"
    path.write_text(result.model_dump_json(indent=2), encoding="utf-8")


def append_audit_log(record: dict) -> None:
    _ensure_out_dir()
    path = OUT_DIR / "audit_log.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def append_override_log(override: OverrideRequest, run_id: str) -> None:
    _ensure_out_dir()
    path = OUT_DIR / "overrides.jsonl"
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "case_id": override.case_id,
        "analyst_action": override.analyst_action,
        "final_decision": override.final_decision,
        "override_reason": override.override_reason,
        "notes": override.notes,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def load_triage_results() -> dict | None:
    path = OUT_DIR / "triage_results.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
