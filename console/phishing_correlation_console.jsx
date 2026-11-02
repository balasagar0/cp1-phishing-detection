import { useEffect, useState } from "react";

// Multi-Channel Phishing Correlation Console.
// Every score comes from the trained models behind the FastAPI backend. No scoring rules live in this file: it calls
// /health, /presets, /correlate, /events, /campaigns and /alerts and shows what they return.
// Served by the API at http://127.0.0.1:8000/ (uvicorn api:app --port 8000). In development (npm run dev, port 5173) it calls :8000.
// Presets come from the API (src/demo_cases.py): TC-01 to TC-08 and four Indian stories, all hand-written, not a test set.

const API_DEFAULT = typeof window !== "undefined" && window.location.port !== "5173" && window.location.protocol.startsWith("http") ? window.location.origin : "http://localhost:8000";
const CHANNELS = ["email", "sms", "url", "call", "video"];
const NOT_ASSESSED = ["call", "voice", "video"];
const blank = () => ({ channel: "sms", text: "", subject: "", identity: "", time: "0" });

const C = { maroon: "#7a1f2b", gold: "#c9a227", red: "#b3261e", green: "#1b7f3b", amber: "#8a6d00", ink: "#1f2328", mute: "#6b7280", line: "#e5e7eb", bg: "#f7f6f3" };
const card = { background: "#fff", border: `1px solid ${C.line}`, borderRadius: 10, padding: 14 };
const input = { width: "100%", boxSizing: "border-box", padding: "7px 9px", border: `1px solid ${C.line}`, borderRadius: 6, font: "inherit", fontSize: 13 };
const btn = (on) => ({ padding: "7px 12px", borderRadius: 8, cursor: "pointer", border: `1px solid ${on ? C.maroon : C.line}`, background: on ? C.maroon : "#fff", color: on ? "#fff" : C.ink, font: "inherit", fontSize: 13 });
const pct = (x) => (x === null || x === undefined ? "–" : `${(x * 100).toFixed(x > 0.995 || x < 0.005 ? 2 : 1)}%`);
const th = { textAlign: "left", padding: "6px 8px", borderBottom: `1px solid ${C.line}`, fontSize: 12, color: C.mute };
const td = { padding: "6px 8px", borderBottom: `1px solid ${C.line}`, fontSize: 13 };

function Bar({ value, mark = 0.5 }) {
  return (
    <div style={{ position: "relative", height: 10, background: "#eee", borderRadius: 5 }}>
      <div style={{ width: `${Math.max(1, (value || 0) * 100)}%`, height: "100%", borderRadius: 5, background: value >= mark ? C.red : C.green }} />
      <div style={{ position: "absolute", left: `${mark * 100}%`, top: -3, height: 16, width: 2, background: C.ink }} title="alert line" />
    </div>
  );
}

function Chips({ items, tone }) {
  return <span>{items.slice(0, 5).map(([t]) => <span key={t} style={{ display: "inline-block", margin: "2px 4px 2px 0", padding: "1px 7px", borderRadius: 10, fontSize: 12, background: tone === "bad" ? "#fde8e6" : "#e6f4ea", color: tone === "bad" ? C.red : C.green }}>{t}</span>)}</span>;
}

async function call(url, path, body) {
  const r = await fetch(`${url}${path}`, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(typeof j.detail === "string" ? j.detail : j.detail ? JSON.stringify(j.detail) : `HTTP ${r.status}`);
  return j;
}

export default function Console() {
  const [base, setBase] = useState(API_DEFAULT);
  const [health, setHealth] = useState(null);
  const [api, setApi] = useState("checking");
  const [presets, setPresets] = useState([]);
  const [win, setWin] = useState("60");
  const [events, setEvents] = useState([blank()]);
  const [active, setActive] = useState("custom");
  const [res, setRes] = useState(null);
  const [store, setStore] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [timeline, setTimeline] = useState(null);
  const [recipient, setRecipient] = useState("demo-user@example.test");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const url = base.replace(/\/$/, "");
  const fail = (x) => setErr(x.message === "Failed to fetch" ? `Cannot reach ${url}. Start the backend (start_demo.bat, or uvicorn api:app --port 8000) and press Retry.` : x.message);

  function connect() {
    setApi("checking");
    call(url, "/health").then((h) => { setHealth(h); setApi(h.status === "ok" ? "up" : "degraded"); if (h.window_minutes) setWin(String(h.window_minutes)); }).catch(() => setApi("down"));
    call(url, "/presets").then((p) => { setPresets(p); if (active === "custom" && p.length && events.length === 1 && !events[0].text) load(p.find((x) => x.id === "TC-04") || p[0]); }).catch(() => {});
    call(url, "/alerts").then(setAlerts).catch(() => {});
  }
  useEffect(() => { const t = setTimeout(connect, 250); return () => clearTimeout(t); }, [url]); // eslint-disable-line react-hooks/exhaustive-deps

  const load = (p) => { setActive(p.id); setEvents(p.events.map((e) => ({ subject: "", identity: "", ...e }))); setRes(null); setStore(null); setTimeline(null); setErr(""); };
  const edit = (i, k, v) => { setActive("custom"); setEvents(events.map((e, j) => (j === i ? { ...e, [k]: v } : e))); };
  const ready = events.length > 0 && events.every((e) => e.text.trim());
  const payload = () => events.map((e) => ({ channel: e.channel, text: e.text, subject: e.subject, identity: e.identity, time: e.time === "" ? null : String(e.time) }));

  async function analyze() {
    const w = Number(win);
    if (!(w > 0 && w <= 10080)) { setErr("The window must be a number of minutes above 0 and up to 10080 (one week)."); return; }
    setBusy(true); setErr(""); setRes(null);
    try { setRes(await call(url, "/correlate", { events: payload(), window_minutes: w })); } catch (x) { fail(x); }
    setBusy(false);
  }

  async function replay() {
    setBusy(true); setErr(""); setStore(null); setTimeline(null);
    try {
      const who = `${recipient.trim() || "demo-user@example.test"}#${active}-${Date.now()}`;      // a fresh recipient per replay, so earlier replays do not mix in
      const j = await call(url, "/events", { recipient: who, events: payload() });
      setStore(j); setAlerts(await call(url, "/alerts"));
      if (!res) { try { setRes(await call(url, "/correlate", { events: payload() })); } catch (x) { /* the store result is still shown */ } }
    } catch (x) { fail(x); }
    setBusy(false);
  }

  async function ack(id) { try { await call(url, `/alerts/${id}/ack`, {}); setAlerts(await call(url, "/alerts")); } catch (x) { fail(x); } }
  async function openCampaign(id) { try { setTimeline(await call(url, `/campaigns/${id}`)); } catch (x) { fail(x); } }

  const scored = res ? res.events.filter((e) => e.score !== null) : [];
  const top = scored.length ? Math.max(...scored.map((e) => e.score)) : null;
  const cannot = res && res.status === "CANNOT_ASSESS";
  const risky = res && !cannot && res.bundle_risk >= res.alert_threshold;
  const preset = presets.find((p) => p.id === active);
  const group = (k) => presets.filter((p) => p.kind === k);

  return (
    <div style={{ fontFamily: "Calibri, 'Segoe UI', Arial, sans-serif", background: C.bg, color: C.ink, minHeight: "100vh", paddingBottom: 30 }}>
      <div style={{ background: C.maroon, color: "#fff", padding: "14px 20px", borderBottom: `4px solid ${C.gold}` }}>
        <div style={{ fontFamily: "'Times New Roman', serif", fontSize: 22 }}>Multi-Channel Phishing Correlation Console</div>
        <div style={{ fontSize: 13, opacity: 0.9 }}>Trained email, SMS and URL detectors, one correlation model on top, an event store for campaigns. No hand-written scoring rules.</div>
      </div>

      <div style={{ maxWidth: 1180, margin: "0 auto", padding: "14px 16px" }}>
        <div style={{ ...card, display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <b style={{ fontSize: 13 }}>Backend</b>
          <input style={{ ...input, width: 240 }} value={base} onChange={(e) => setBase(e.target.value)} aria-label="backend address" />
          <span data-testid="health" style={{ fontSize: 13, color: api === "up" ? C.green : api === "degraded" ? C.amber : api === "down" ? C.red : C.mute }}>
            {api === "up" ? "● connected" : api === "degraded" ? `● degraded: ${Object.keys(health?.not_available || {}).join(", ")} not loaded` : api === "down" ? "● not reachable" : "● checking"}
          </span>
          {api === "down" && <button style={btn(false)} onClick={connect}>Retry</button>}
          <b style={{ fontSize: 13 }}>Window</b>
          <input style={{ ...input, width: 70 }} value={win} onChange={(e) => setWin(e.target.value)} title="Events further apart than this are not combined or linked" aria-label="window minutes" />
          <span style={{ fontSize: 13, color: C.mute }}>minutes</span>
          <span data-testid="voice-video" style={{ fontSize: 12, color: C.mute, marginLeft: "auto" }}>Voice and video: not assessed (not built)</span>
        </div>

        {["demo case", "Indian story"].map((k) => group(k).length > 0 && (
          <div key={k} style={{ margin: "12px 0 0", display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
            <span style={{ fontSize: 12, color: C.mute, width: 96 }}>{k === "demo case" ? "Demo cases" : "Indian stories"}</span>
            {group(k).map((p) => <button key={p.id} data-testid={`preset-${p.id}`} onClick={() => load(p)} style={btn(active === p.id)} title={p.name} aria-label={`${p.id}: ${p.name}`}>{p.id}</button>)}
            {k === "demo case" && <button data-testid="preset-custom" onClick={() => { setActive("custom"); setEvents([blank()]); setRes(null); setStore(null); setErr(""); }} style={btn(active === "custom")}>Custom</button>}
          </div>
        ))}
        <div style={{ fontSize: 13, color: C.mute, margin: "8px 0 10px" }}>
          {preset ? <><b style={{ color: C.ink }}>{preset.id}: {preset.name}.</b> {preset.note || ""} <i>({preset.label})</i></> : "Write your own events. Identity is optional (sender number, address or domain). Time is in minutes."}
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 12 }}>
          {events.map((e, i) => (
            <div key={i} style={card} data-testid={`event-editor-${i}`}>
              <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
                <select style={{ ...input, width: 90 }} value={e.channel} onChange={(x) => edit(i, "channel", x.target.value)} aria-label="channel">{CHANNELS.map((c) => <option key={c}>{c}</option>)}</select>
                <input style={input} placeholder="identity (optional)" value={e.identity} onChange={(x) => edit(i, "identity", x.target.value)} aria-label="identity" />
                <input style={{ ...input, width: 70 }} title="minutes" value={e.time} onChange={(x) => edit(i, "time", x.target.value)} aria-label="time" />
                <button onClick={() => { setActive("custom"); setEvents(events.filter((_, j) => j !== i)); }} style={{ border: "none", background: "none", cursor: "pointer", color: C.mute, fontSize: 16 }} title="remove">×</button>
              </div>
              {e.channel === "email" && <input style={{ ...input, marginBottom: 8 }} placeholder="subject" value={e.subject} onChange={(x) => edit(i, "subject", x.target.value)} aria-label="subject" />}
              {NOT_ASSESSED.includes(e.channel) && <div style={{ fontSize: 12, color: C.amber, marginBottom: 6 }}>Not assessed: no {e.channel} detector is built. It is stored and shown, never scored.</div>}
              <textarea style={{ ...input, minHeight: 84, resize: "vertical" }} placeholder={e.channel === "url" ? "paste a URL" : e.channel === "email" ? "paste the email body" : "paste the message or a note about it"} value={e.text} onChange={(x) => edit(i, "text", x.target.value)} aria-label="text" />
            </div>
          ))}
          {events.length < 6 && <button onClick={() => { setActive("custom"); setEvents([...events, blank()]); }} style={{ ...card, cursor: "pointer", color: C.mute, borderStyle: "dashed", minHeight: 80 }}>+ Add event</button>}
        </div>

        <div style={{ margin: "14px 0", display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <button data-testid="analyze" disabled={!ready || busy} onClick={analyze} style={{ padding: "10px 22px", borderRadius: 8, border: "none", background: !ready || busy ? "#c9c9c9" : C.maroon, color: "#fff", font: "inherit", fontSize: 15, cursor: !ready || busy ? "default" : "pointer" }}>{busy ? "Working…" : "Analyze events"}</button>
          <button data-testid="replay" disabled={!ready || busy} onClick={replay} style={{ ...btn(false), padding: "9px 16px", fontSize: 14 }}>Replay into event store</button>
          <input style={{ ...input, width: 230 }} value={recipient} onChange={(e) => setRecipient(e.target.value)} title="recipient (stored only as a hash)" aria-label="recipient" />
          {err && <span data-testid="error" style={{ color: C.red, fontSize: 13 }}>{err}</span>}
        </div>

        {res && (
          <div data-testid="results">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 12, marginBottom: 12 }}>
              <div style={card} data-testid="single-view">
                <div style={{ fontSize: 12, color: C.mute }}>SINGLE-CHANNEL VIEW</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: cannot ? C.amber : res.single_channel_alert ? C.red : C.green }}>{cannot ? "Nothing to assess" : res.single_channel_alert ? "Alert raised" : "No alert"}</div>
                <div style={{ fontSize: 13, color: C.mute }}>{top === null ? "No event could be scored." : `Highest single score ${pct(top)}. Each event is judged alone, alert line 50%.`}</div>
              </div>
              <div style={{ ...card, borderColor: cannot ? C.amber : risky ? C.red : C.green, borderWidth: 2 }} data-testid="bundle-view">
                <div style={{ fontSize: 12, color: C.mute }}>CORRELATED VIEW</div>
                {cannot ? (
                  <><div data-testid="bundle-risk" style={{ fontSize: 20, fontWeight: 700, color: C.amber }}>CANNOT_ASSESS</div>
                    <div style={{ fontSize: 13, color: C.mute }}>{res.reason}</div></>
                ) : (
                  <><div data-testid="bundle-risk" style={{ fontSize: 20, fontWeight: 700, color: risky ? C.red : C.green }}>{res.bundle_label} · {pct(res.bundle_risk)}</div>
                    <Bar value={res.bundle_risk} />
                    <div style={{ fontSize: 13, color: C.mute, marginTop: 6 }}>All events pooled, with no link or timing evidence, would score {pct(res.bundle_risk_without_correlation)}.</div>
                    <div style={{ fontSize: 13, marginTop: 4 }}>{res.shared_identity_tokens.length ? <>Linked by <b>{res.shared_identity_tokens.join(", ")}</b></> : "No shared identity between the events in this window"}; window span {res.window_time_span_minutes} min.</div>
                    {res.n_windows > 1 && <div style={{ fontSize: 13, color: C.mute, marginTop: 4 }}>The events are {res.time_span_minutes} min apart in total, so they fall into {res.n_windows} windows of {res.window_minutes} min. Only the highest-risk window counts, and events in different windows are not combined.</div>}</>
                )}
              </div>
            </div>

            <div style={{ ...card, marginBottom: 12, overflowX: "auto" }}>
              <div style={{ fontSize: 12, color: C.mute, marginBottom: 6 }}>SIDE BY SIDE: each event alone, and the bundle</div>
              <table style={{ borderCollapse: "collapse", width: "100%" }} data-testid="side-by-side">
                <thead><tr><th style={th}>#</th><th style={th}>Channel</th><th style={th}>Time (min)</th><th style={th}>Event score</th><th style={th}>Alerts on its own</th><th style={th}>In the scored window</th><th style={th}>Identity tokens</th></tr></thead>
                <tbody>
                  {res.events.map((e, i) => (
                    <tr key={i} data-testid={`event-row-${i}`}>
                      <td style={td}>{i + 1}</td><td style={{ ...td, textTransform: "uppercase" }}>{e.channel}</td><td style={td}>{e.t_minutes}</td>
                      <td style={{ ...td, fontWeight: 700, color: e.score === null ? C.amber : e.score >= 0.5 ? C.red : C.green }}>{e.score === null ? "not assessed" : pct(e.score)}</td>
                      <td style={td}>{e.score === null ? "–" : e.score >= 0.5 ? "yes" : "no"}</td><td style={td}>{e.in_window ? "yes" : "no"}</td>
                      <td style={{ ...td, fontSize: 12, color: C.mute }}>{(e.identity_tokens || []).join(", ")}</td>
                    </tr>
                  ))}
                  <tr><td style={{ ...td, fontWeight: 700 }} colSpan={3}>Bundle</td><td style={{ ...td, fontWeight: 700, color: cannot ? C.amber : risky ? C.red : C.green }} data-testid="bundle-cell">{cannot ? "CANNOT_ASSESS" : pct(res.bundle_risk)}</td>
                    <td style={td} colSpan={3}>{cannot ? "no risk is given" : risky ? "alerts" : "no alert"}</td></tr>
                </tbody>
              </table>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 12 }}>
              {res.events.map((e, i) => {
                if (e.score === null) return <div key={i} style={{ ...card, opacity: 0.8 }}><b style={{ textTransform: "uppercase", fontSize: 13 }}>{e.channel} · t={e.t_minutes} min</b><div style={{ color: C.amber, marginTop: 6 }}>Not assessed. {e.reason}</div></div>;
                const pos = Object.entries(e).find(([k]) => k.startsWith("top_") && !/legit|ham/.test(k))?.[1] || [];
                const neg = Object.entries(e).find(([k]) => k.startsWith("top_") && /legit|ham/.test(k))?.[1] || [];
                return (
                  <div key={i} style={{ ...card, opacity: res.n_windows > 1 && !e.in_window ? 0.65 : 1 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                      <b style={{ textTransform: "uppercase", fontSize: 13 }}>{e.channel} · t={e.t_minutes} min</b>
                      <b style={{ color: e.score >= 0.5 ? C.red : C.green }}>{pct(e.score)}</b>
                    </div>
                    <Bar value={e.score} />
                    {res.n_windows > 1 && !e.in_window && <div style={{ fontSize: 12, color: C.mute, marginTop: 6 }}>Outside the highest-risk window</div>}
                    {e.class_probabilities && <div style={{ fontSize: 12, color: C.mute, marginTop: 6 }}>ham {pct(e.class_probabilities.ham)} · spam {pct(e.class_probabilities.spam)} · smishing {pct(e.class_probabilities.smishing)}</div>}
                    {e.domain_reputation && <div style={{ fontSize: 12, color: C.mute, marginTop: 6 }}>{e.domain_reputation.registered_domain}: {e.domain_reputation.popularity_rank ? `in the top-10k popularity list (rank ${e.domain_reputation.popularity_rank})` : "not in the top-10k popularity list"}</div>}
                    {pos.length > 0 && <div style={{ marginTop: 6, fontSize: 12 }}>Pushed up: <Chips items={pos} tone="bad" /></div>}
                    {neg.length > 0 && <div style={{ fontSize: 12 }}>Pushed down: <Chips items={neg} tone="good" /></div>}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {store && (
          <div style={{ ...card, marginTop: 14 }} data-testid="store-panel">
            <div style={{ fontSize: 12, color: C.mute }}>EVENT STORE: replayed for recipient {store.recipient} (stored as a hash; message text {store.content_stored ? "stored" : "not stored"})</div>
            <div style={{ fontSize: 15, margin: "6px 0" }}>Highest campaign risk <b data-testid="store-risk">{store.highest_campaign_risk === null ? "none (nothing assessable)" : pct(store.highest_campaign_risk)}</b>
              {store.new_alerts.length > 0 ? <b style={{ color: C.red }}> · {store.new_alerts.length} new alert{store.new_alerts.length > 1 ? "s" : ""}</b> : <span style={{ color: C.green }}> · no new alert</span>}</div>
            <table style={{ borderCollapse: "collapse", width: "100%" }}>
              <thead><tr><th style={th}>Campaign</th><th style={th}>Events</th><th style={th}>Risk</th><th style={th}>Alert</th><th style={th}>Shared tokens (hashed)</th><th style={th}></th></tr></thead>
              <tbody>{store.campaigns.map((c) => (
                <tr key={c.id}><td style={td}>{c.id}</td><td style={td}>{c.n_events}</td><td style={{ ...td, color: c.alert ? C.red : C.green, fontWeight: 700 }}>{pct(c.risk)}</td><td style={td}>{c.alert ? "yes" : "no"}</td>
                  <td style={{ ...td, fontSize: 12, color: C.mute }}>{c.shared_identity_tokens.join(", ") || "none"}</td><td style={td}><button style={btn(false)} onClick={() => openCampaign(c.id)}>Timeline</button></td></tr>))}</tbody>
            </table>
            {store.new_alerts.map((a) => <div key={a.id} style={{ fontSize: 13, marginTop: 8, color: C.red }} data-testid="new-alert">Alert {a.id}: {a.reason}. Linked by {a.shared_identity_tokens.join(", ") || "time only"}.</div>)}
            {timeline && (
              <div style={{ marginTop: 10 }}>
                <div style={{ fontSize: 12, color: C.mute }}>TIMELINE of campaign {timeline.id} ({timeline.window_minutes}-minute window)</div>
                {timeline.timeline.map((e) => <div key={e.id} style={{ fontSize: 13, opacity: e.in_campaign ? 1 : 0.7 }}>t={e.t_minutes} · {e.channel.toUpperCase()} · {e.assessed ? pct(e.score) : "not assessed"}{e.in_campaign ? "" : " (not part of the score)"}</div>)}
              </div>
            )}
          </div>
        )}

        {alerts.length > 0 && (
          <div style={{ ...card, marginTop: 14 }} data-testid="alerts-panel">
            <div style={{ fontSize: 12, color: C.mute }}>OPEN ALERTS ({alerts.length})</div>
            {alerts.slice(-8).reverse().map((a) => (
              <div key={a.id} style={{ display: "flex", gap: 10, alignItems: "center", fontSize: 13, marginTop: 6 }} data-testid="alert-item">
                <span style={{ color: C.red, fontWeight: 700 }}>{pct(a.risk)}</span><span style={{ flex: 1 }}>{a.reason}</span>
                <button style={btn(false)} onClick={() => ack(a.id)}>Acknowledge</button>
              </div>
            ))}
          </div>
        )}

        <div style={{ ...card, marginTop: 16, fontSize: 12, color: C.mute, lineHeight: 1.5 }}>
          <b>What is measured and what is assumed.</b> Event scores come from models trained on public email, SMS and URL data (held-out numbers are in reports/).{" "}
          {/simulated/.test(health?.fusion_trained_on || "simulated")
            ? "The bundle score comes from a model trained on SIMULATED bundles, because no public dataset links one attacker's email, SMS and URL events. Its use of link and timing evidence reflects those simulation assumptions, not field data. Events further apart than the window are not combined or linked, and an event alone in its window is judged by its own detector. The bundle risk is not a calibrated probability."
            : `The bundle score comes from a model refit on ${health.fusion_trained_on}.`}{" "}
          Presets are hand-written, not a test set. Calls and video are not assessed.
        </div>
      </div>
    </div>
  );
}
