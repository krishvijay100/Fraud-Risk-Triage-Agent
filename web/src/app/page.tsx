"use client";

import { useState, useCallback } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Types ────────────────────────────────────────────────────────────────────

interface Evidence {
  amount?: number;
  currency?: string;
  channel?: string;
  country?: string;
  new_device?: boolean;
  new_beneficiary?: boolean;
  velocity_1h?: number;
  account_age_days?: number;
  kyc_level?: string;
  avg_amount_30d?: number;
  amount_ratio?: number;
  prior_alerts_90d?: number;
  prior_confirmed_fraud?: number;
  memo_UNTRUSTED?: string;
}

interface LinkedEntities {
  device_id?: string;
  beneficiary_id?: string;
  merchant_id?: string;
  ip?: string;
  shared_device_cases?: { case_id: string; alert_type: string }[];
  ring_suspicions?: string[];
}

interface TriageCase {
  case_id: string;
  alert_type: string;
  created_at: string;
  risk_score: number;
  risk_tier: string;
  confidence: string;
  sla_target_minutes: number;
  recommendation: string;
  reason_codes: string[];
  no_go_flags: string[];
  evidence: Evidence;
  evidence_completeness: number;
  narrative: string;
  linked_entities: LinkedEntities;
}

interface TriageResult {
  run_id: string;
  generated_at: string;
  results: TriageCase[];
}

// ── Helpers ──────────────────────────────────────────────────────────────────

const TIER_COLOR: Record<string, string> = {
  URGENT: "#ff4444",
  HIGH: "#ff8800",
  MEDIUM: "#ffcc00",
  LOW: "#44aaff",
  AUTO_CLEAR: "#44ff88",
};

const REC_COLOR: Record<string, string> = {
  HOLD_RECOMMENDED: "#ff4444",
  ESCALATE_L2: "#ff8800",
  STEP_UP: "#ffcc00",
  MONITOR: "#44aaff",
  CLEAR: "#44ff88",
};

function tierColor(tier: string) {
  return TIER_COLOR[tier] ?? "#888";
}

function recColor(rec: string) {
  return REC_COLOR[rec] ?? "#888";
}

function slaLabel(mins: number) {
  if (mins === 0) return "Auto";
  if (mins < 60) return `${mins}m`;
  return `${mins / 60}h`;
}

// ── Override Modal ────────────────────────────────────────────────────────────

interface OverrideModalProps {
  kase: TriageCase;
  runId: string;
  onClose: () => void;
  onDone: (msg: string) => void;
}

function OverrideModal({ kase, runId, onClose, onDone }: OverrideModalProps) {
  const [reason, setReason] = useState("");
  const [decision, setDecision] = useState("STEP_UP");
  const [submitting, setSubmitting] = useState(false);

  const submit = useCallback(async () => {
    if (!reason.trim()) return;
    setSubmitting(true);
    try {
      await fetch(`${API}/override`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          run_id: runId,
          case_id: kase.case_id,
          analyst_action: "OVERRIDE",
          final_decision: decision,
          override_reason: reason,
        }),
      });
      onDone(`Override recorded for ${kase.case_id}`);
    } finally {
      setSubmitting(false);
    }
  }, [reason, decision, kase.case_id, runId, onDone]);

  const overlay: React.CSSProperties = {
    position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)",
    display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100,
  };
  const box: React.CSSProperties = {
    background: "#1a1a1a", border: "1px solid #333", borderRadius: 6,
    padding: 24, width: 400, display: "flex", flexDirection: "column", gap: 12,
  };

  return (
    <div style={overlay} onClick={onClose}>
      <div style={box} onClick={(e) => e.stopPropagation()}>
        <div style={{ fontWeight: "bold", fontSize: 14 }}>Override — {kase.case_id}</div>
        <div>
          <label style={{ display: "block", marginBottom: 4, color: "#aaa" }}>Final Decision</label>
          <select value={decision} onChange={(e) => setDecision(e.target.value)} style={{ width: "100%" }}>
            <option>CLEAR</option>
            <option>MONITOR</option>
            <option>STEP_UP</option>
            <option>ESCALATE_L2</option>
            <option>HOLD_RECOMMENDED</option>
          </select>
        </div>
        <div>
          <label style={{ display: "block", marginBottom: 4, color: "#aaa" }}>Override Reason (required)</label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            style={{ width: "100%", resize: "vertical" }}
            placeholder="Explain the override..."
          />
        </div>
        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <button onClick={onClose} style={{ background: "#333", color: "#e0e0e0", border: "none", borderRadius: 3, padding: "6px 14px" }}>
            Cancel
          </button>
          <button
            onClick={submit}
            disabled={submitting || !reason.trim()}
            style={{ background: "#ff8800", color: "#000", border: "none", borderRadius: 3, padding: "6px 14px", fontWeight: "bold" }}
          >
            {submitting ? "Submitting…" : "Submit Override"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Case Row ──────────────────────────────────────────────────────────────────

function CaseRow({ kase, selected, onClick }: { kase: TriageCase; selected: boolean; onClick: () => void }) {
  const color = tierColor(kase.risk_tier);
  return (
    <div
      onClick={onClick}
      style={{
        padding: "8px 10px",
        borderBottom: "1px solid #222",
        cursor: "pointer",
        background: selected ? "#1e1e1e" : "transparent",
        borderLeft: selected ? `3px solid ${color}` : "3px solid transparent",
        display: "grid",
        gridTemplateColumns: "60px 55px 40px 1fr 50px",
        gap: 6,
        alignItems: "center",
      }}
    >
      <span style={{ color, fontWeight: "bold", fontSize: 11 }}>{kase.risk_tier === "AUTO_CLEAR" ? "CLEAR" : kase.risk_tier}</span>
      <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{kase.case_id}</span>
      <span style={{ color, textAlign: "center", fontWeight: "bold" }}>{kase.risk_score}</span>
      <span style={{ color: "#888", fontSize: 11 }}>{kase.alert_type.replace(/_/g, " ")}</span>
      <span style={{ color: "#555", fontSize: 11, textAlign: "right" }}>SLA {slaLabel(kase.sla_target_minutes)}</span>
    </div>
  );
}

// ── Case Detail ───────────────────────────────────────────────────────────────

function Tag({ text, color }: { text: string; color: string }) {
  return (
    <span style={{
      display: "inline-block", padding: "1px 7px", borderRadius: 3,
      background: color + "22", color, border: `1px solid ${color}55`,
      fontSize: 11, margin: "2px 3px 2px 0",
    }}>
      {text}
    </span>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div style={{ display: "flex", gap: 8, padding: "3px 0", borderBottom: "1px solid #1a1a1a" }}>
      <span style={{ color: "#666", minWidth: 170, flexShrink: 0 }}>{label}</span>
      <span>{value}</span>
    </div>
  );
}

interface CaseDetailProps {
  kase: TriageCase;
  runId: string;
  onAccept: (id: string) => void;
}

function CaseDetail({ kase, runId, onAccept }: CaseDetailProps) {
  const [showOverride, setShowOverride] = useState(false);
  const [toast, setToast] = useState("");

  const accept = useCallback(async () => {
    await fetch(`${API}/override`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        run_id: runId,
        case_id: kase.case_id,
        analyst_action: "ACCEPT",
        final_decision: kase.recommendation,
      }),
    });
    onAccept(kase.case_id);
    setToast(`Accepted recommendation for ${kase.case_id}`);
    setTimeout(() => setToast(""), 3000);
  }, [kase, runId, onAccept]);

  const ev = kase.evidence;
  const le = kase.linked_entities;
  const tc = tierColor(kase.risk_tier);
  const rc = recColor(kase.recommendation);

  return (
    <div style={{ padding: 20, overflowY: "auto", height: "100%" }}>
      {showOverride && (
        <OverrideModal
          kase={kase}
          runId={runId}
          onClose={() => setShowOverride(false)}
          onDone={(msg) => { setShowOverride(false); setToast(msg); setTimeout(() => setToast(""), 3000); }}
        />
      )}

      {toast && (
        <div style={{
          position: "fixed", bottom: 20, right: 20, background: "#222",
          border: "1px solid #555", padding: "8px 16px", borderRadius: 4, zIndex: 200,
        }}>
          {toast}
        </div>
      )}

      {/* Header */}
      <div style={{ marginBottom: 16, display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
        <span style={{ fontSize: 16, fontWeight: "bold" }}>{kase.case_id}</span>
        <Tag text={kase.risk_tier} color={tc} />
        <Tag text={kase.recommendation} color={rc} />
        <span style={{ marginLeft: "auto", color: "#888", fontSize: 11 }}>
          {new Date(kase.created_at).toLocaleString()}
        </span>
      </div>

      {/* Score row */}
      <div style={{ display: "flex", gap: 24, marginBottom: 16, flexWrap: "wrap" }}>
        <div>
          <div style={{ color: "#666", fontSize: 11 }}>RISK SCORE</div>
          <div style={{ fontSize: 28, fontWeight: "bold", color: tc }}>{kase.risk_score}</div>
        </div>
        <div>
          <div style={{ color: "#666", fontSize: 11 }}>CONFIDENCE</div>
          <div style={{ fontSize: 18, fontWeight: "bold" }}>{kase.confidence}</div>
        </div>
        <div>
          <div style={{ color: "#666", fontSize: 11 }}>SLA TARGET</div>
          <div style={{ fontSize: 18, fontWeight: "bold" }}>{slaLabel(kase.sla_target_minutes)}</div>
        </div>
        <div>
          <div style={{ color: "#666", fontSize: 11 }}>COMPLETENESS</div>
          <div style={{ fontSize: 18, fontWeight: "bold" }}>{(kase.evidence_completeness * 100).toFixed(0)}%</div>
        </div>
      </div>

      {/* No-go flags */}
      {kase.no_go_flags.length > 0 && (
        <div style={{ background: "#2a0000", border: "1px solid #440000", borderRadius: 4, padding: "8px 12px", marginBottom: 12 }}>
          <div style={{ color: "#ff4444", fontWeight: "bold", marginBottom: 4 }}>NO-GO FLAGS</div>
          {kase.no_go_flags.map((f) => <Tag key={f} text={f} color="#ff4444" />)}
        </div>
      )}

      {/* Reason codes */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ color: "#666", fontSize: 11, marginBottom: 4 }}>REASON CODES</div>
        {kase.reason_codes.map((r) => <Tag key={r} text={r} color="#888" />)}
      </div>

      {/* Evidence */}
      <div style={{ marginBottom: 12, border: "1px solid #222", borderRadius: 4, padding: 10 }}>
        <div style={{ color: "#666", fontSize: 11, marginBottom: 6 }}>EVIDENCE</div>
        <Row label="Alert Type" value={kase.alert_type} />
        <Row label="Amount" value={`${ev.currency} ${ev.amount?.toLocaleString()}`} />
        <Row label="Channel" value={ev.channel} />
        <Row label="Country" value={ev.country} />
        <Row label="New Device" value={ev.new_device ? "Yes" : "No"} />
        <Row label="New Beneficiary" value={ev.new_beneficiary ? "Yes" : "No"} />
        <Row label="Velocity (1h)" value={ev.velocity_1h} />
        <Row label="Account Age" value={`${ev.account_age_days} days`} />
        <Row label="KYC Level" value={ev.kyc_level} />
        <Row label="Avg Amount (30d)" value={`${ev.currency} ${ev.avg_amount_30d}`} />
        <Row label="Amount Ratio" value={ev.amount_ratio ? `${ev.amount_ratio}×` : "N/A"} />
        <Row label="Prior Alerts (90d)" value={ev.prior_alerts_90d} />
        <Row label="Prior Confirmed Fraud" value={ev.prior_confirmed_fraud} />
        {ev.memo_UNTRUSTED && (
          <Row label="Memo (untrusted)" value={<span style={{ color: "#888", fontStyle: "italic" }}>"{ev.memo_UNTRUSTED}"</span>} />
        )}
      </div>

      {/* Linked entities */}
      {(le.ring_suspicions?.length || le.shared_device_cases?.length) ? (
        <div style={{ marginBottom: 12, border: "1px solid #332200", borderRadius: 4, padding: 10 }}>
          <div style={{ color: "#ff8800", fontSize: 11, marginBottom: 6 }}>LINKED ENTITIES</div>
          {le.device_id && <Row label="Device ID" value={`…${le.device_id.slice(-4)}`} />}
          {le.beneficiary_id && <Row label="Beneficiary ID" value={`…${le.beneficiary_id.slice(-4)}`} />}
          {le.ip && <Row label="IP" value={le.ip} />}
          {le.shared_device_cases?.map((c) => (
            <Row key={c.case_id} label="Shared Device Case" value={`${c.case_id} (${c.alert_type})`} />
          ))}
          {le.ring_suspicions?.map((s, i) => (
            <div key={i} style={{ color: "#ff8800", fontSize: 11, marginTop: 4 }}>{s}</div>
          ))}
        </div>
      ) : null}

      {/* Narrative */}
      {kase.narrative && (
        <div style={{ marginBottom: 16, border: "1px solid #1a2a1a", borderRadius: 4, padding: 10, background: "#0f1a0f" }}>
          <div style={{ color: "#44ff88", fontSize: 11, marginBottom: 6 }}>NARRATIVE (LLM SUMMARY)</div>
          <p style={{ color: "#c0d0c0", lineHeight: 1.6 }}>{kase.narrative}</p>
        </div>
      )}

      {/* Actions */}
      <div style={{ display: "flex", gap: 10, marginTop: 8 }}>
        <button
          onClick={accept}
          style={{
            background: "#003322", color: "#44ff88", border: "1px solid #44ff8844",
            borderRadius: 3, padding: "7px 18px", fontWeight: "bold",
          }}
        >
          Accept Recommendation
        </button>
        <button
          onClick={() => setShowOverride(true)}
          style={{
            background: "#331100", color: "#ff8800", border: "1px solid #ff880044",
            borderRadius: 3, padding: "7px 18px", fontWeight: "bold",
          }}
        >
          Override
        </button>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function Home() {
  const [result, setResult] = useState<TriageResult | null>(null);
  const [selected, setSelected] = useState<TriageCase | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [accepted, setAccepted] = useState<Set<string>>(new Set());

  const fetchResults = useCallback(async () => {
    try {
      const res = await fetch(`${API}/results`);
      if (res.ok) {
        const data: TriageResult = await res.json();
        setResult(data);
      }
    } catch {
      // no results yet — ignore
    }
  }, []);

  const runTriage = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API}/triage`, { method: "POST" });
      if (!res.ok) throw new Error(await res.text());
      const data: TriageResult = await res.json();
      setResult(data);
      setSelected(null);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  const handleAccept = useCallback((id: string) => {
    setAccepted((prev) => new Set(prev).add(id));
  }, []);

  // Load existing results on mount
  useState(() => { fetchResults(); });

  const cases = result?.results ?? [];

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      {/* Header */}
      <div style={{
        padding: "10px 18px", borderBottom: "1px solid #222",
        display: "flex", alignItems: "center", gap: 16, background: "#0a0a0a",
      }}>
        <span style={{ fontWeight: "bold", fontSize: 15, letterSpacing: 1 }}>FRAUD TRIAGE</span>
        {result && (
          <span style={{ color: "#555", fontSize: 11 }}>
            Run {result.run_id.slice(0, 8)} — {new Date(result.generated_at).toLocaleString(undefined, { year: "numeric", month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit", timeZoneName: "short" })}
          </span>
        )}
        <span style={{ marginLeft: "auto" }} />
        {error && <span style={{ color: "#ff4444", fontSize: 11 }}>{error}</span>}
        <button
          onClick={runTriage}
          disabled={loading}
          style={{
            background: "#1a3a1a", color: "#44ff88", border: "1px solid #44ff8844",
            borderRadius: 3, padding: "6px 18px", fontWeight: "bold", fontSize: 12,
          }}
        >
          {loading ? "Running…" : "Run Triage"}
        </button>
      </div>

      {/* Body */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {/* Case list */}
        <div style={{
          width: 340, flexShrink: 0, borderRight: "1px solid #222",
          overflowY: "auto", background: "#0d0d0d",
        }}>
          {/* List header */}
          <div style={{
            padding: "6px 10px", borderBottom: "1px solid #1a1a1a",
            color: "#555", fontSize: 11,
            display: "grid", gridTemplateColumns: "60px 55px 40px 1fr 50px", gap: 6,
          }}>
            <span style={{ textAlign: "center" }}>TIER</span><span style={{ textAlign: "center" }}>CASE</span><span style={{ textAlign: "center" }}>SCORE</span>
            <span style={{ textAlign: "center" }}>TYPE</span><span style={{ textAlign: "center" }}>SLA</span>
          </div>

          {cases.length === 0 ? (
            <div style={{ padding: 20, color: "#444", textAlign: "center" }}>
              No results — click Run Triage
            </div>
          ) : (
            cases.map((c) => (
              <CaseRow
                key={c.case_id}
                kase={c}
                selected={selected?.case_id === c.case_id}
                onClick={() => setSelected(c)}
              />
            ))
          )}
        </div>

        {/* Detail panel */}
        <div style={{ flex: 1, overflowY: "auto", background: "#111" }}>
          {selected ? (
            <CaseDetail
              kase={selected}
              runId={result?.run_id ?? ""}
              onAccept={handleAccept}
            />
          ) : (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "#333" }}>
              Select a case to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
