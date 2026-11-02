import { useEffect, useState } from "react";

// Multi-Channel Phishing Correlation Console.
// Every score comes from the trained models behind the FastAPI backend (POST /correlate). No scoring rules live in this file.
// Start the backend first:  uvicorn api:app --port 8000
// The window (minutes) goes with every request: events further apart than it are not combined or linked. Its default comes from the backend.

const API_DEFAULT = "http://localhost:8000";
const CHANNELS = ["email", "sms", "url"];
const blank = () => ({ channel: "sms", text: "", subject: "", identity: "", time: "0" });

const PRESETS = [
  { id: "kyc", name: "Bank KYC campaign", note: "An SMS, a link and an email, minutes apart, all pointing at one domain.", events: [
    { channel: "sms", text: "Dear customer, your SBI account will be blocked today. Update your KYC now at http://sbi-kyc-update.top/verify-now.php or call 9876543210", subject: "", identity: "+91 98765 43210", time: "0" },
    { channel: "url", text: "http://sbi-kyc-update.top/verify-now.php", subject: "", identity: "", time: "4" },
    { channel: "email", text: "Dear customer, your bank account has been suspended. Verify your password within 24 hours at http://sbi-kyc-update.top/verify-now.php or your account will be closed.", subject: "Urgent: account suspended", identity: "", time: "12" } ] },
  { id: "benign", name: "Colleague shares an article", note: "Normal messages that happen to share a link. Should stay low.", events: [
    { channel: "sms", text: "Hey, can we move our project meeting to 4 pm tomorrow? I will email you the notes and an article on planning.", subject: "", identity: "+91 90000 11111", time: "0" },
    { channel: "email", text: "Thanks for confirming. I wrote up the notes from yesterday. The article I mentioned is at https://en.wikipedia.org/wiki/Project_management if you want to read it. Call me tomorrow if anything changes.", subject: "Re: project meeting", identity: "", time: "6" },
    { channel: "url", text: "https://en.wikipedia.org/wiki/Project_management", subject: "", identity: "", time: "10" } ] },
  { id: "weak", name: "Weak-signal parcel campaign", note: "Each message alone scores below the alert line. Same domain, 15 minutes.", events: [
    { channel: "sms", text: "Hello, there is a problem with your delivery address. Update it at parcel-redelivery.info/confirm today", subject: "", identity: "", time: "0" },
    { channel: "url", text: "http://parcel-redelivery.info/track?id=88213", subject: "", identity: "", time: "7" },
    { channel: "email", text: "Hello, we could not deliver your parcel today because the address on the label is incomplete. Please confirm your address at http://parcel-redelivery.info/confirm so we can try again. Thank you.", subject: "Delivery problem with your parcel", identity: "", time: "15" } ] },
];
PRESETS.push({ id: "apart", name: "Same parcel campaign, days apart", note: "The weak-signal parcel messages again, but three days apart. Outside the window they are not combined, so nothing alerts.",
  events: PRESETS[2].events.map((e, i) => ({ ...e, time: String([0, 4320, 8640][i]) })) });

const C = { maroon: "#7a1f2b", gold: "#c9a227", red: "#b3261e", green: "#1b7f3b", ink: "#1f2328", mute: "#6b7280", line: "#e5e7eb", bg: "#f7f6f3" };
const card = { background: "#fff", border: `1px solid ${C.line}`, borderRadius: 10, padding: 14 };
const input = { width: "100%", boxSizing: "border-box", padding: "7px 9px", border: `1px solid ${C.line}`, borderRadius: 6, font: "inherit", fontSize: 13 };
const pct = (x) => `${(x * 100).toFixed(x > 0.995 || x < 0.005 ? 2 : 1)}%`;

function Bar({ value, mark = 0.5 }) {
  return (
    <div style={{ position: "relative", height: 10, background: "#eee", borderRadius: 5 }}>
      <div style={{ width: `${Math.max(1, value * 100)}%`, height: "100%", borderRadius: 5, background: value >= mark ? C.red : C.green }} />
      <div style={{ position: "absolute", left: `${mark * 100}%`, top: -3, height: 16, width: 2, background: C.ink }} title="alert line" />
    </div>
  );
}

function Chips({ items, tone }) {
  return <span>{items.slice(0, 5).map(([t]) => <span key={t} style={{ display: "inline-block", margin: "2px 4px 2px 0", padding: "1px 7px", borderRadius: 10, fontSize: 12, background: tone === "bad" ? "#fde8e6" : "#e6f4ea", color: tone === "bad" ? C.red : C.green }}>{t}</span>)}</span>;
}

export default function Console() {
  const [base, setBase] = useState(API_DEFAULT);
  const [api, setApi] = useState("checking");
  const [fusion, setFusion] = useState("simulated bundles");
  const [win, setWin] = useState("60");
  const [events, setEvents] = useState(PRESETS[0].events);
  const [active, setActive] = useState("kyc");
  const [res, setRes] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const url = base.replace(/\/$/, "");

  useEffect(() => {
    setApi("checking");
    const t = setTimeout(() => fetch(`${url}/health`).then((r) => { setApi(r.ok ? "up" : "down"); return r.json(); }).then((j) => { setFusion(j.fusion_trained_on || "simulated bundles"); if (j.window_minutes) setWin(String(j.window_minutes)); }).catch(() => setApi("down")), 300);
    return () => clearTimeout(t);
  }, [url]);

  const load = (p) => { setActive(p.id); setEvents(p.events.map((e) => ({ ...e }))); setRes(null); setErr(""); };
  const edit = (i, k, v) => { setActive("custom"); setEvents(events.map((e, j) => (j === i ? { ...e, [k]: v } : e))); };
  const ready = events.length > 0 && events.every((e) => e.text.trim());

  async function analyze() {
    const w = Number(win);
    if (!(w > 0 && w <= 10080)) { setErr("The window must be a number of minutes above 0 and up to 10080 (one week)."); return; }
    setBusy(true); setErr(""); setRes(null);
    try {
      const r = await fetch(`${url}/correlate`, { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ events: events.map((e) => ({ channel: e.channel, text: e.text, subject: e.subject, identity: e.identity, time: e.time === "" ? null : String(e.time) })), window_minutes: w }) });
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
      setRes(await r.json());
    } catch (x) { setErr(x.message === "Failed to fetch" ? `Cannot reach ${url}. Start the backend with: uvicorn api:app --port 8000` : x.message); }
    setBusy(false);
  }

  const top = res ? Math.max(...res.events.map((e) => e.score)) : 0;
  const risky = res && res.bundle_risk >= res.alert_threshold;

  return (
    <div style={{ fontFamily: "Calibri, Segoe UI, sans-serif", background: C.bg, color: C.ink, minHeight: "100vh", paddingBottom: 30 }}>
      <div style={{ background: C.maroon, color: "#fff", padding: "14px 20px", borderBottom: `4px solid ${C.gold}` }}>
        <div style={{ fontFamily: "Times New Roman, serif", fontSize: 22 }}>Multi-Channel Phishing Correlation Console</div>
        <div style={{ fontSize: 13, opacity: 0.9 }}>Trained per-channel detectors, one correlation model on top. No hand-written scoring rules.</div>
      </div>

      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "14px 16px" }}>
        <div style={{ ...card, display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <b style={{ fontSize: 13 }}>Backend</b>
          <input style={{ ...input, width: 260 }} value={base} onChange={(e) => setBase(e.target.value)} />
          <span style={{ fontSize: 13, color: api === "up" ? C.green : api === "down" ? C.red : C.mute }}>{api === "up" ? "● connected" : api === "down" ? "● not reachable" : "● checking"}</span>
          <b style={{ fontSize: 13 }}>Window</b>
          <input style={{ ...input, width: 70 }} value={win} onChange={(e) => setWin(e.target.value)} title="Events further apart than this are not combined or linked" />
          <span style={{ fontSize: 13, color: C.mute }}>minutes</span>
          <span style={{ fontSize: 12, color: C.mute, marginLeft: "auto" }}>Voice and video: not trained</span>
        </div>

        <div style={{ margin: "12px 0 6px", display: "flex", gap: 8, flexWrap: "wrap" }}>
          {PRESETS.map((p) => (
            <button key={p.id} onClick={() => load(p)} style={{ padding: "7px 12px", borderRadius: 8, cursor: "pointer", border: `1px solid ${active === p.id ? C.maroon : C.line}`, background: active === p.id ? C.maroon : "#fff", color: active === p.id ? "#fff" : C.ink, font: "inherit", fontSize: 13 }}>{p.name}</button>
          ))}
          <button onClick={() => { setActive("custom"); setEvents([blank()]); setRes(null); setErr(""); }} style={{ padding: "7px 12px", borderRadius: 8, cursor: "pointer", border: `1px solid ${active === "custom" ? C.maroon : C.line}`, background: active === "custom" ? C.maroon : "#fff", color: active === "custom" ? "#fff" : C.ink, font: "inherit", fontSize: 13 }}>Custom</button>
        </div>
        <div style={{ fontSize: 13, color: C.mute, marginBottom: 10 }}>{PRESETS.find((p) => p.id === active)?.note || "Write your own events. Identity is optional (sender number, address or domain). Time is in minutes."} Example messages are illustrative, not from a real incident.</div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 12 }}>
          {events.map((e, i) => (
            <div key={i} style={card}>
              <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
                <select style={{ ...input, width: 90 }} value={e.channel} onChange={(x) => edit(i, "channel", x.target.value)}>{CHANNELS.map((c) => <option key={c}>{c}</option>)}</select>
                <input style={input} placeholder="identity (optional)" value={e.identity} onChange={(x) => edit(i, "identity", x.target.value)} />
                <input style={{ ...input, width: 70 }} title="minutes" value={e.time} onChange={(x) => edit(i, "time", x.target.value)} />
                <button onClick={() => { setActive("custom"); setEvents(events.filter((_, j) => j !== i)); }} style={{ border: "none", background: "none", cursor: "pointer", color: C.mute, fontSize: 16 }} title="remove">×</button>
              </div>
              {e.channel === "email" && <input style={{ ...input, marginBottom: 8 }} placeholder="subject" value={e.subject} onChange={(x) => edit(i, "subject", x.target.value)} />}
              <textarea style={{ ...input, minHeight: 84, resize: "vertical" }} placeholder={e.channel === "url" ? "paste a URL" : "paste the message"} value={e.text} onChange={(x) => edit(i, "text", x.target.value)} />
            </div>
          ))}
          {events.length < 6 && <button onClick={() => { setActive("custom"); setEvents([...events, blank()]); }} style={{ ...card, cursor: "pointer", color: C.mute, borderStyle: "dashed", minHeight: 80 }}>+ Add event</button>}
        </div>

        <div style={{ margin: "14px 0" }}>
          <button disabled={!ready || busy} onClick={analyze} style={{ padding: "10px 22px", borderRadius: 8, border: "none", background: !ready || busy ? "#c9c9c9" : C.maroon, color: "#fff", font: "inherit", fontSize: 15, cursor: !ready || busy ? "default" : "pointer" }}>{busy ? "Analyzing…" : "Analyze events"}</button>
          {err && <span style={{ marginLeft: 12, color: C.red, fontSize: 13 }}>{err}</span>}
        </div>

        {res && (
          <div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 12, marginBottom: 12 }}>
              <div style={card}>
                <div style={{ fontSize: 12, color: C.mute }}>SINGLE-CHANNEL VIEW</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: res.single_channel_alert ? C.red : C.green }}>{res.single_channel_alert ? "Alert raised" : "No alert"}</div>
                <div style={{ fontSize: 13, color: C.mute }}>Highest single score {pct(top)}. Each event is judged alone, alert line 50%.</div>
              </div>
              <div style={{ ...card, borderColor: risky ? C.red : C.green, borderWidth: 2 }}>
                <div style={{ fontSize: 12, color: C.mute }}>CORRELATED VIEW</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: risky ? C.red : C.green }}>{res.bundle_label} · {pct(res.bundle_risk)}</div>
                <Bar value={res.bundle_risk} />
                <div style={{ fontSize: 13, color: C.mute, marginTop: 6 }}>All events pooled, with no link or timing evidence, would score {pct(res.bundle_risk_without_correlation)}.</div>
                <div style={{ fontSize: 13, marginTop: 4 }}>{res.shared_identity_tokens.length ? <>Linked by <b>{res.shared_identity_tokens.join(", ")}</b></> : "No shared identity between the events in this window"}; window span {res.window_time_span_minutes} min.</div>
                {res.n_windows > 1 && <div style={{ fontSize: 13, color: C.mute, marginTop: 4 }}>The events are {res.time_span_minutes} min apart in total, so they fall into {res.n_windows} windows of {res.window_minutes} min. Only the highest-risk window counts, and events in different windows are not combined.</div>}
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 12 }}>
              {res.events.map((e, i) => {
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
                    {e.identity_tokens.length > 0 && <div style={{ fontSize: 12, color: C.mute, marginTop: 4 }}>identity: {e.identity_tokens.join(", ")}</div>}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div style={{ ...card, marginTop: 16, fontSize: 12, color: C.mute, lineHeight: 1.5 }}>
          <b>What is measured and what is assumed.</b> Event scores come from models trained on public email, SMS and URL data (held-out numbers are in results.md).{" "}
          {/simulated/.test(fusion)
            ? "The bundle score comes from a model trained on simulated bundles, because no public dataset links one attacker's email, SMS and URL events. Its use of link and timing evidence reflects those simulation assumptions, not field data. Events further apart than the window are not combined or linked, and an event alone in its window is judged by its own detector. The window is applied by the API on top of the trained model."
            : `The bundle score comes from a model refit on ${fusion}.`}
        </div>
      </div>
    </div>
  );
}
