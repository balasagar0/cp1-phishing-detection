"""End-to-end check (Phase 4.2, R3-03): API -> correlation -> event store -> alert -> console, over real HTTP.
  python scripts/e2e_check.py
Starts uvicorn on a spare port (temporary event database, test HMAC key, no access log) and walks the whole flow with the demo cases
(hand-written, not a test set). The console's own screens are checked by scripts/ui_checks.py. Writes reports/e2e_check.json and .md."""
import json, os, re, socket, subprocess, sys, tempfile, time, datetime
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parents[1]


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def main():
    port = free_port(); url = f"http://127.0.0.1:{port}"; tmp = tempfile.mkdtemp(prefix="cp1_e2e_")
    env = {**os.environ, "CP1_EVENT_DB": str(Path(tmp) / "events.db"), "CP1_HMAC_KEY": "e2e-check-key"}
    p = subprocess.Popen([sys.executable, "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", str(port), "--no-access-log"], cwd=ROOT, env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    steps = []
    def step(name, ok, detail): steps.append({"step": name, "ok": bool(ok), "detail": detail}); print(("PASS " if ok else "FAIL ") + name, "-", detail[:150])
    try:
        c = httpx.Client(base_url=url, timeout=60)
        for _ in range(240):
            try:
                if c.get("/health").status_code == 200: break
            except httpx.HTTPError: time.sleep(0.25)
        h = c.get("/health").json(); step("API up, all detectors loaded", h["status"] == "ok", f"channels {h['channels']}, window {h['window_minutes']} min, correlation trained on {h['fusion_trained_on']}")
        page = c.get("/"); js = re.search(r'src="(/assets/[^"]+\.js)"', page.text)
        step("console served at /", page.status_code == 200 and js and c.get(js.group(1)).status_code == 200, f"HTTP {page.status_code}, script {js.group(1) if js else 'missing'}")
        pres = {x["id"]: x for x in c.get("/presets").json()}
        step("console presets from the API", {"TC-06", "TC-07", "IN-04"} <= set(pres), f"{len(pres)} presets")
        tc06 = c.post("/correlate", json={"events": pres["TC-06"]["events"]}).json()
        step("correlation: TC-06 alerts only as a bundle", (not tc06["single_channel_alert"]) and tc06["bundle_risk"] >= 0.5, f"bundle risk {tc06['bundle_risk']:.3f}, single-channel alert {tc06['single_channel_alert']}")
        who = "e2e-recipient@example.test"
        ev = c.post("/events", json={"recipient": who, "events": pres["TC-06"]["events"]}).json()
        step("event store: same risk as /correlate", round(ev["highest_campaign_risk"], 3) == round(tc06["bundle_risk"], 3), f"store {ev['highest_campaign_risk']:.3f}, correlate {tc06['bundle_risk']:.3f}")
        step("alert raised once, with its reason", len(ev["new_alerts"]) == 1 and "reached the alert line" in ev["new_alerts"][0]["reason"], f"{len(ev['new_alerts'])} new alert(s); linked by {ev['new_alerts'][0]['shared_identity_tokens'] if ev['new_alerts'] else []}")
        al = c.get("/alerts", params={"recipient": who}).json()
        camp = c.get(f"/campaigns/{al[0]['campaign_id']}").json() if al else {"timeline": []}
        step("alert listed, campaign timeline holds the events", len(al) == 1 and len(camp["timeline"]) == 3, f"{len(al)} open alert(s); timeline {len(camp['timeline'])} events")
        ack = c.post(f"/alerts/{al[0]['id']}/ack").status_code if al else 0
        step("alert acknowledged", ack == 200 and c.get("/alerts", params={"recipient": who}).json() == [], f"ack HTTP {ack}")
        who7 = "e2e-control@example.test"; e7 = c.post("/events", json={"recipient": who7, "events": pres["TC-07"]["events"]}).json()
        step("control TC-07: three one-event campaigns, no alert", len(e7["campaigns"]) == 3 and e7["new_alerts"] == [], f"{len(e7['campaigns'])} campaigns, {len(e7['new_alerts'])} alerts, highest {e7['highest_campaign_risk']:.3f}")
        e3 = c.post("/events", json={"recipient": "e2e-call@example.test", "events": pres["TC-03"]["events"]}).json()
        step("a call alone: CANNOT_ASSESS, stored, no campaign", e3["status"] == "CANNOT_ASSESS" and e3["campaigns"] == [], f"status {e3['status']}")
    finally:
        p.terminate(); p.wait(timeout=30)
    ok = all(s["ok"] for s in steps)
    commit = subprocess.run(["git", "describe", "--tags", "--always", "--dirty"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    doc = {"date": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "commit": commit, "ok": ok, "steps": steps}
    (ROOT / "reports" / "e2e_check.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    L = ["# End-to-end check (R3-03)\n", f"Written by `scripts/e2e_check.py` on {doc['date']} on `{commit}`, over real HTTP. Demo cases are hand-written, not a test set. Result: **{'PASS' if ok else 'FAIL'}**.\n",
         "| Step | Result | Detail |", "|---|---|---|"] + [f"| {s['step']} | {'pass' if s['ok'] else '**fail**'} | {s['detail']} |" for s in steps]
    L.append("\nThe console's screens (presets, side-by-side view, replay into the event store) are checked in Chrome and Edge by `scripts/ui_checks.py`.")
    (ROOT / "reports" / "e2e_check.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
