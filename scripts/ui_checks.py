"""Console checks UI-01 to UI-07 (Phase 2.4), automated with Playwright against the console served by the API.
  python scripts/ui_checks.py
Starts its own uvicorn on a spare port (temporary event database, test HMAC key), drives the installed Chrome and Microsoft Edge
(no browser download), and fails any request that leaves this machine. Writes reports/ui_checks.json (read by tests/test_final_cases.py)
and screenshots to reports/screenshots/ for the report, the manual and the poster. The samples are the workbook's hand-written ones."""
import json, os, socket, subprocess, sys, tempfile, time, datetime
from pathlib import Path
from urllib.parse import urlparse
import httpx
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
from machine_info import one_line
SHOTS = ROOT / "reports" / "screenshots"; SHOTS.mkdir(parents=True, exist_ok=True)
SAMPLE = json.loads((ROOT / "tests" / "data" / "workbook_cases.json").read_text(encoding="utf-8"))
EM = {r["ID"]: r for r in SAMPLE["email"]}
RESULTS, OUTSIDE = {}, []


def pct(x): return f"{x * 100:.{2 if x > 0.995 or x < 0.005 else 1}f}%"


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


class Server:
    def __init__(self):
        self.port = free_port(); self.url = f"http://127.0.0.1:{self.port}"; self.tmp = tempfile.mkdtemp(prefix="cp1_ui_"); self.p = None
    def start(self):
        env = {**os.environ, "CP1_EVENT_DB": str(Path(self.tmp) / "events.db"), "CP1_HMAC_KEY": "ui-check-key"}
        self.p = subprocess.Popen([sys.executable, "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", str(self.port), "--no-access-log"],
                                  cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(120):
            try:
                if httpx.get(self.url + "/health", timeout=2).status_code == 200: return self
            except httpx.HTTPError: time.sleep(0.5)
        raise RuntimeError("the API did not start")
    def stop(self):
        if self.p: self.p.terminate(); self.p.wait(timeout=30); self.p = None


def record(cid, ok, actual, shots=()):
    RESULTS[cid] = {"status": "Pass" if ok else "Fail", "actual": actual + (f" Screenshots: {', '.join(shots)}." if shots else "")}
    print(("PASS " if ok else "FAIL ") + cid, "-", actual[:160])


def watch(page, errors):
    page.on("console", lambda m: errors.append(f"console {m.type}: {m.text}") if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(f"page error: {e}"))
    page.on("request", lambda r: OUTSIDE.append(r.url) if urlparse(r.url).hostname not in ("127.0.0.1", "localhost") and not r.url.startswith(("data:", "blob:")) else None)


def shot(page, name, full=False):
    page.screenshot(path=str(SHOTS / name), full_page=full); return f"reports/screenshots/{name}"


def analyze(page):
    page.get_by_test_id("analyze").click(); page.get_by_test_id("results").wait_for(timeout=30000)


def preset(page, pid):
    page.get_by_test_id(f"preset-{pid}").click()


def row_scores(page):
    return [page.get_by_test_id(f"event-row-{i}").locator("td").nth(3).inner_text() for i in range(page.locator("[data-testid^=event-row-]").count())]


def custom_event(page, i, channel, text, subject=""):
    ed = page.get_by_test_id(f"event-editor-{i}")
    ed.locator("select").select_option(channel)
    if subject: ed.get_by_label("subject").fill(subject)
    ed.get_by_label("text").fill(text)


def main():
    S = Server().start(); api = httpx.Client(base_url=S.url, timeout=60)
    with sync_playwright() as pw:
        browsers = {}
        for name, channel in (("Chrome", "chrome"), ("Edge", "msedge")):
            try: browsers[name] = pw.chromium.launch(channel=channel, headless=True)
            except Exception as e: print(f"{name} not available: {e}")
        b = browsers.get("Chrome") or next(iter(browsers.values()))
        ctx = b.new_context(viewport={"width": 1366, "height": 900}); page = ctx.new_page(); errors = []; watch(page, errors)

        # UI-01: loads cleanly; email, SMS, URL inputs and a voice/video line
        page.goto(S.url + "/"); page.get_by_test_id("preset-TC-04").wait_for(); page.wait_for_timeout(800)
        opts = page.get_by_test_id("event-editor-0").locator("select option").all_inner_texts()
        vv = page.get_by_test_id("voice-video").inner_text(); health = page.get_by_test_id("health").inner_text()
        ok = not errors and {"email", "sms", "url"} <= set(opts) and "not assessed" in vv and "connected" in health
        record("UI-01", ok, f"Chrome at {S.url}/: browser console errors {errors or 'none'}; channel inputs {opts}; '{vv}'; health '{health}'", [shot(page, "ui01_console_loaded.png")])

        # UI-02: E-P01 then E-L01 through the console, compared with /score
        out, good = [], True
        for sid in ("E-P01", "E-L01"):
            page.get_by_test_id("preset-custom").click(); custom_event(page, 0, "email", EM[sid]["Body"], EM[sid]["Subject"]); analyze(page)
            shown = row_scores(page)[0]; alone = page.get_by_test_id("event-row-0").locator("td").nth(4).inner_text()
            ref = api.post("/score", json={"channel": "email", "text": EM[sid]["Body"], "subject": EM[sid]["Subject"]}).json()["score"]
            want = "yes" if EM[sid]["Expected label"] == "Phishing" else "no"
            good &= shown == pct(ref) and alone == want; out.append(f"{sid}: console {shown}, alerts alone '{alone}'; /score {pct(ref)}")
            if sid == "E-P01": s2 = shot(page, "ui02_single_email_EP01.png")
        record("UI-02", good, "; ".join(out), [s2, shot(page, "ui02_single_email_EL01.png")])

        # UI-03 and UI-04: preset scenario 1 (TC-04) and 2 (TC-06): both views shown; correlated at or above each single score
        for cid, pid, name in (("UI-03", "TC-04", "ui03_preset_TC04.png"), ("UI-04", "TC-06", "ui04_preset_TC06.png")):
            preset(page, pid); analyze(page)
            j = api.post("/correlate", json={"events": next(p for p in api.get("/presets").json() if p["id"] == pid)["events"]}).json()
            single = page.get_by_test_id("single-view").inner_text().split("\n")[1]; bundle = page.get_by_test_id("bundle-risk").inner_text()
            top = max(e["score"] for e in j["events"] if e["score"] is not None)
            ok = pct(j["bundle_risk"]) in bundle and j["bundle_risk"] >= top and row_scores(page) == [pct(e["score"]) for e in j["events"]]
            record(cid, ok, f"{pid}: single-channel view '{single}', correlated view '{bundle}', event scores {row_scores(page)}; correlated {pct(j['bundle_risk'])} >= best single {pct(top)}: {j['bundle_risk'] >= top}", [shot(page, name, True)])
        page.get_by_test_id("replay").click(); page.get_by_test_id("store-panel").wait_for(timeout=30000); page.wait_for_timeout(500)
        shot(page, "store_replay_TC06.png", True)

        # UI-05: custom input mode with an email, an SMS and a URL typed in (scenario S-02's messages)
        page.get_by_test_id("preset-custom").click()
        custom_event(page, 0, "email", "Dear customer, we detected unusual activity on your account. Verify your identity within 24 hours at secure-bank-verify.xyz/login and enter your net banking ID and password or your account will be locked.", "Urgent: your account will be suspended")
        page.get_by_text("+ Add event").click(); custom_event(page, 1, "sms", "URGENT! Your bank account is suspended. Verify now at secure-bank-verify.xyz/login to avoid permanent closure. Txt STOP to opt out")
        page.get_by_text("+ Add event").click(); custom_event(page, 2, "url", "secure-bank-verify.xyz/login")
        page.get_by_test_id("event-editor-1").get_by_label("time").fill("1"); page.get_by_test_id("event-editor-2").get_by_label("time").fill("2")
        analyze(page); bv = page.get_by_test_id("bundle-view").inner_text()
        record("UI-05", "dom:secure-bank-verify.xyz" in bv and "elevated risk" in bv, f"custom email + SMS + URL: correlated view shows '{bv.splitlines()[1]}' and '{[l for l in bv.splitlines() if 'Linked' in l][0]}'", [shot(page, "ui05_custom_input.png", True)])

        # UI-06: service down: clear error and a way to retry; the page does not freeze
        preset(page, "TC-01"); S.stop(); page.get_by_test_id("analyze").click(); page.get_by_test_id("error").wait_for(timeout=30000)
        msg = page.get_by_test_id("error").inner_text(); s6 = shot(page, "ui06_service_down.png")
        preset(page, "TC-05"); still = page.get_by_test_id("analyze").is_enabled()
        S.start(); api = httpx.Client(base_url=S.url, timeout=60); analyze(page); back = page.get_by_test_id("bundle-risk").inner_text()
        record("UI-06", "Cannot reach" in msg and "Retry" in msg and still and bool(back),
               f"API stopped: '{msg}'; page still responds (preset switched, Analyze enabled: {still}); after the API restarts, Analyze again shows '{back}'", [s6])

        # UI-07: 1366x768 and 1920x1080 in Chrome and Edge: no clipped content, same results
        res7, ok7, shots7 = {}, True, []
        for bname, br in browsers.items():
            for w, h in ((1366, 768), (1920, 1080)):
                c2 = br.new_context(viewport={"width": w, "height": h}); p2 = c2.new_page(); e2 = []; watch(p2, e2)
                p2.goto(S.url + "/"); p2.get_by_test_id("preset-TC-04").click(); analyze(p2)
                over = p2.evaluate("document.documentElement.scrollWidth - window.innerWidth")
                res7[(bname, w)] = (p2.get_by_test_id("bundle-risk").inner_text(), row_scores(p2))
                ok7 &= over <= 0 and not e2; shots7.append(shot(p2, f"ui07_{bname.lower()}_{w}x{h}.png")); c2.close()
        same = len({json.dumps(v) for v in res7.values()}) == 1
        record("UI-07", ok7 and same and len(browsers) == 2, f"browsers {list(browsers)}; sizes 1366x768 and 1920x1080; no horizontal overflow and no console errors: {ok7}; "
               f"identical results everywhere: {same} ({next(iter(res7.values()))[0]})", shots7)

        # extra screenshots for the report and poster (not cases)
        for pid in ("TC-07", "TC-03", "TC-05", "IN-04"):
            preset(page, pid); analyze(page); shot(page, f"demo_{pid}.png", True)
        for br in browsers.values(): br.close()
    S.stop()
    if OUTSIDE:
        for k in RESULTS: RESULTS[k]["status"] = "Fail"; RESULTS[k]["actual"] += f" Requests left this machine: {sorted(set(OUTSIDE))[:5]}."
    doc = {**RESULTS, "_run": {"date": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "machine": one_line(), "requests_outside_this_machine": sorted(set(OUTSIDE)),
                               "commit": subprocess.run(["git", "describe", "--tags", "--always", "--dirty"], cwd=ROOT, capture_output=True, text=True).stdout.strip()}}
    (ROOT / "reports" / "ui_checks.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print("requests outside this machine:", sorted(set(OUTSIDE)) or "none")
    return 0 if all(v["status"] == "Pass" for v in RESULTS.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
