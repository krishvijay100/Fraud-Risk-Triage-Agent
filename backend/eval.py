"""
Offline evaluation script.
Computes Precision@10 and Auto-clear error rate as defined in agent_docs/evaluation.md.

Usage (from backend/ directory):
    python eval.py

Requires:
    - ../out/triage_results.json   (produced by POST /triage)
    - ../data/mock_cases.json      (ground truth labels)
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent.parent
RESULTS_FILE = ROOT / "out" / "triage_results.json"
CASES_FILE = ROOT / "data" / "mock_cases.json"


def main() -> int:
    # ── Load data ────────────────────────────────────────────────────────────
    if not RESULTS_FILE.exists():
        print(f"ERROR: {RESULTS_FILE} not found. Run POST /triage first.")
        return 1
    if not CASES_FILE.exists():
        print(f"ERROR: {CASES_FILE} not found.")
        return 1

    triage = json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
    cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))

    label_map: dict[str, str] = {c["case_id"]: c["label"]["outcome"] for c in cases}
    decisions: list[dict] = triage["results"]

    # ── Dataset validation ───────────────────────────────────────────────────
    total_cases = len(cases)
    label_counts = Counter(c["label"]["outcome"] for c in cases)
    fraud_count = label_counts["FRAUD"]
    benign_count = label_counts["BENIGN"]
    uncertain_count = label_counts["UNCERTAIN"]

    print("=" * 55)
    print("DATASET VALIDATION")
    print("=" * 55)
    print(f"  Total cases      : {total_cases}")
    print(f"  FRAUD            : {fraud_count}  ({fraud_count/total_cases*100:.1f}%)")
    print(f"  BENIGN           : {benign_count}  ({benign_count/total_cases*100:.1f}%)")
    print(f"  UNCERTAIN        : {uncertain_count}  ({uncertain_count/total_cases*100:.1f}%)")

    benign_pct = benign_count / total_cases
    fraud_pct = fraud_count / total_cases
    uncertain_pct = uncertain_count / total_cases
    ok = (0.40 <= benign_pct <= 0.50) and (0.30 <= fraud_pct <= 0.40) and (0.10 <= uncertain_pct <= 0.20)
    print(f"  Distribution OK  : {'YES' if ok else 'NO — check data_schema.md'}")

    # ── Triage results sorted by score ──────────────────────────────────────
    sorted_decisions = sorted(decisions, key=lambda d: d["risk_score"], reverse=True)

    # ── Metric 1: Precision@10 ───────────────────────────────────────────────
    K = min(10, len(sorted_decisions))
    top_k = sorted_decisions[:K]
    fraud_in_top_k = sum(1 for d in top_k if label_map.get(d["case_id"]) == "FRAUD")
    precision_at_k = fraud_in_top_k / K

    print()
    print("=" * 55)
    print(f"METRICS (on {len(decisions)} triaged cases)")
    print("=" * 55)
    print(f"  Precision@{K}      : {precision_at_k:.2f}  ({fraud_in_top_k}/{K} FRAUD in top {K})")

    print(f"\n  Top {K} cases by risk score:")
    for i, d in enumerate(top_k, 1):
        label = label_map.get(d["case_id"], "?")
        marker = "[FRAUD]" if label == "FRAUD" else "       "
        print(f"    {i:>2}. {d['case_id']}  score={d['risk_score']:>3}  tier={d['risk_tier']:<11}  label={label} {marker}")

    # ── Metric 2: Auto-clear error rate ──────────────────────────────────────
    auto_cleared = [d for d in decisions if d["risk_tier"] == "AUTO_CLEAR"]
    if auto_cleared:
        fraud_auto = sum(1 for d in auto_cleared if label_map.get(d["case_id"]) == "FRAUD")
        ac_error_rate = fraud_auto / len(auto_cleared)
        print(f"\n  Auto-clear count : {len(auto_cleared)}")
        print(f"  Auto-clear FRAUD : {fraud_auto}")
        print(f"  Auto-clear error : {ac_error_rate:.2f}  (target: 0.00)")
        if auto_cleared:
            print(f"\n  Auto-cleared cases:")
            for d in auto_cleared:
                label = label_map.get(d["case_id"], "?")
                print(f"    {d['case_id']}  score={d['risk_score']:>3}  label={label}")
    else:
        print(f"\n  Auto-clear count : 0  (no cases auto-cleared)")

    # ── Tier distribution ─────────────────────────────────────────────────────
    tier_counts = Counter(d["risk_tier"] for d in decisions)
    print()
    print("=" * 55)
    print("TIER DISTRIBUTION")
    print("=" * 55)
    for tier in ["URGENT", "HIGH", "MEDIUM", "LOW", "AUTO_CLEAR"]:
        count = tier_counts.get(tier, 0)
        print(f"  {tier:<12}: {count}")

    # ── Top reason codes ──────────────────────────────────────────────────────
    all_codes: list[str] = []
    for d in decisions:
        all_codes.extend(d.get("reason_codes", []))
    top_codes = Counter(all_codes).most_common(10)
    print()
    print("=" * 55)
    print("TOP REASON CODES")
    print("=" * 55)
    for code, cnt in top_codes:
        print(f"  {code:<40}: {cnt}")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
