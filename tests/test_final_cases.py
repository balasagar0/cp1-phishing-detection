"""The 112 cases of the 29 September test plan (v1.1), ported to v2. One test per case ID, PRE-01 to NFR-07, IDs kept.
The plan was written for an older codebase (/analyze routes, 0-100 scores, a rule bonus, SAFE/SUSPICIOUS/HIGH RISK bands), so every case is tagged:
  Ported   - the same check against v2.
  Replaced - the same intent with v2's expectation: HIGH RISK -> alert (risk >= 0.5), SAFE -> no alert, Rejected -> HTTP 4xx.
  N/A      - the feature does not exist in v2 (the rule bonus, the risk threshold of 20, the 30/60 verdict bands); the reason is given.
Expectations are never weakened so a case passes: when v2 behaves wrongly the case fails and points at a defect.
A failing case linked to an OPEN defect is reported as an expected failure (pytest xfail); any other failure fails the suite.

Run:  python tests/test_final_cases.py      (runs the smoke set first, then everything; writes reports/final_cases_results.json)
      pytest tests/test_final_cases.py
      CP1_API_URL=http://127.0.0.1:8000 ...  runs the API cases over real HTTP against a running uvicorn.
Samples, scenarios and cases come from tests/data/workbook_cases.json (copied from the team workbook by scripts/extract_workbook_cases.py).
They are HAND-WRITTEN, NOT A TEST SET: the sample groups are the plan's own checks, not an evaluation of the models."""
import json, os, sys, time, re, socket, statistics, subprocess, datetime, platform, threading, io, contextlib, logging, importlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT))
import pytest

DATA = json.loads((ROOT / "tests" / "data" / "workbook_cases.json").read_text(encoding="utf-8"))
SAMPLE = {ch: {r["ID"]: r for r in DATA[ch]} for ch in ("email", "sms", "url")}
SCEN = {s["Scenario"]: s for s in DATA["scenarios"]}
PLAN = {c["TC ID"]: c for c in DATA["test_cases"]}
ALERT = 0.5
OUT = ROOT / "reports" / "final_cases_results.json"

# Defects that are open on this build. A case linked to one of these may fail without failing the suite (it is reported as xfail).
# Update this set as defects close: a defect leaves it only after its failing case passes.
OPEN_DEFECTS = {"D-01", "D-09", "D-10", "D-12", "D-16", "D-17", "D-18"}

CASES, RESULTS, SAMPLE_RESULTS, SCENARIO_RESULTS = {}, {}, {}, {}


def case(cid, tag, why="", defect=None):
    """Registers the check for one plan case. `why` explains a Replaced or N/A tag."""
    assert cid in PLAN, cid
    def deco(fn):
        CASES[cid] = {"tag": tag, "why": why, "fn": fn, "defect": defect}
        return fn
    return deco


def ok(cond, actual): return ("Pass" if cond else "Fail", actual)
def na(reason): return ("N/A", reason)
def not_run(reason): return ("Not run", reason)


# ---------------------------------------------------------------- clients and helpers
_client = None
def C():
    global _client
    if _client is None:
        url = os.environ.get("CP1_API_URL")
        if url:
            import httpx
            _client = httpx.Client(base_url=url.rstrip("/"), timeout=120)
        else:
            from fastapi.testclient import TestClient
            import api
            _client = TestClient(api.app)
    return _client


def app_module():
    import api
    return api


def score(channel, text, subject=""):
    r = C().post("/score", json={"channel": channel, "text": text, "subject": subject})
    assert r.status_code == 200, (channel, r.status_code, r.text[:200])
    return r.json()


def sample_score(ch, sid):
    s = SAMPLE[ch][sid]
    if ch == "email": j = score("email", s["Body"], s["Subject"])
    elif ch == "sms": j = score("sms", s["Message"])
    else: j = score("url", s["URL"])
    pred = "Phishing" if j["score"] >= ALERT else "Legitimate"
    SAMPLE_RESULTS[sid] = {"channel": ch, "group": s["Group"], "expected": s["Expected label"], "predicted": pred, "score": j["score"],
                           "result": "Pass" if pred == s["Expected label"] else "Fail",
                           **({"smishing_probability": j.get("smishing_probability")} if ch == "sms" else {})}
    return j["score"], pred


def run_group(ch, group, label=None):
    ids = [r["ID"] for r in DATA[ch] if r["Group"] == group and (label is None or r["Expected label"] == label)]
    return [(sid, *sample_score(ch, sid)) for sid in ids]


def group_text(rows, label):
    good = [r for r in rows if r[2] == label]; bad = [r for r in rows if r[2] != label]
    acc = len(good) / len(rows)
    txt = f"{len(good)}/{len(rows)} predicted {label.lower()} ({100 * acc:.0f}%)"
    if bad: txt += "; wrong: " + ", ".join(f"{sid} {100 * s:.1f}" for sid, s, _ in bad)
    return acc, txt


def scenario_events(sid):
    """Turns a Scenarios-sheet case into /correlate events. Timestamps are given in seconds there; v2 takes minutes.
    Returns (events, fixed_scores or None). 'Video transcript' becomes a channel='video' event."""
    text = SCEN[sid]["Case sent to /analyze"]
    if text.startswith("(empty case"): return [], None
    ev, times, fixed = [], {}, None
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("Email:"):
            m = re.match(r'Email:\s*"([^"]*)"\s*(.*)', line); ev.append({"channel": "email", "subject": m.group(1), "text": m.group(2)})
        elif line.startswith("SMS:"): ev.append({"channel": "sms", "text": line[4:].strip()})
        elif line.startswith("URL:"): ev.append({"channel": "url", "text": line[4:].strip()})
        elif line.startswith("Video transcript:"): ev.append({"channel": "video", "text": line[len("Video transcript:"):].strip()})
        elif line.startswith("Timestamps (seconds):"): times = {k: float(v) for k, v in re.findall(r"(email|sms|url)\s+(\d+)", line)}
        elif line.startswith("Detector scores fixed at:"): fixed = {k: float(v) / 100 for k, v in re.findall(r"(email|sms|url)\s+([\d.]+)", line)}
    for i, e in enumerate(ev): e["time"] = str(times[e["channel"]] / 60.0) if e["channel"] in times else str(i)
    return ev, fixed


def correlate(events, **kw):
    return C().post("/correlate", json={"events": events, **kw})


def engine_fixed(items):
    """Runs v2's correlation engine on its own with fixed detector scores. items: (channel, score, text, minutes)."""
    from predict import extract_ids
    F = app_module().F
    ev = [{"channel": ch, "score": s, "ids": extract_ids(ch, txt), "t": float(t)} for ch, s, txt, t in items]
    r = F.risk(ev)
    from collections import Counter
    cnt = Counter(tok for i in r["window_events"] for tok in set(ev[i]["ids"]))
    r["shared"] = sorted(t for t, c in cnt.items() if c >= 2)
    r["max_single"] = max(e["score"] for e in ev)
    return r


def describe(j):
    sc = ", ".join(f"{e['channel']} {e['score']:.3f}" if e.get("score") is not None else f"{e['channel']} not assessed" for e in j["events"])
    risk = j.get("bundle_risk")
    return (f"events: {sc}; single-channel alert {j.get('single_channel_alert')}; bundle risk "
            f"{'none' if risk is None else f'{risk:.3f}'} ({j.get('bundle_label', j.get('status'))}); windows {j.get('n_windows')}; shared {j.get('shared_identity_tokens')}")


def scenario(sid):
    ev, fixed = scenario_events(sid)
    r = correlate(ev)
    j = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    SCENARIO_RESULTS[sid] = f"HTTP {r.status_code}: " + (describe(j) if r.status_code == 200 else str(j.get("detail", r.text[:200])))
    return r, j


# ================================================================= Preprocessing
@case("PRE-01", "Ported", defect="D-11")
def _():
    from common import clean_text
    out = clean_text("<html><body><p>Verify <b>now</b></p><script>track()</script></body></html>")
    return ok(out == "Verify now", f"clean_text returned: {out!r}")


@case("PRE-02", "N/A", "v2 does not replace URLs and e-mail addresses with placeholder tokens. The email model reads the words of the URL, and the "
      "correlation step extracts registered domains as identity tokens (tested by COR-02, COR-03 and tests/test_window_and_ids.py).")
def _(): return na(CASES["PRE-02"]["why"])


@case("PRE-03", "Ported", defect="D-15")
def _():
    from common import clean_text
    try: out = [clean_text(None), clean_text(123)]
    except Exception as e: return ok(False, f"exception: {e!r}")
    return ok(out == ["", ""], f"clean_text(None), clean_text(123) -> {out!r}")


@case("PRE-04", "Ported")
def _():
    from common import clean_text
    s = "Your account 🔒 will be blocked ⚠️ आज ही update करें"
    try: a, b = clean_text(s), clean_text(s)
    except Exception as e: return ok(False, f"exception: {e!r}")
    return ok(a == b and "account" in a, f"No exception; repeatable={a == b}; result={a!r}")


@case("PRE-05", "Replaced", "v2 has no 30-feature URL extractor. Its URL representation is the canonical URL's character 3-5-gram hashing (2^20 slots) "
      "plus 3 domain-popularity flags. Same intent: the vector for U-P01 is complete and identical on repeat, and the IP host carries no popularity flag.")
def _():
    import numpy as np
    from scipy import sparse
    from url_features import canon, host_of, rep_matrix
    D = app_module().D; u = SAMPLE["url"]["U-P01"]["URL"]
    def vec(x):
        c = canon(x); M = D.url["tfidf"].transform(D._hv.transform([c])); return sparse.hstack([M, rep_matrix([host_of(c)], D.url["rank_map"])]).tocsr()
    a, b = vec(u), vec(u)
    width = D._hv.n_features + 3; same = (a != b).nnz == 0; flags = a[0, -3:].toarray().ravel().tolist()
    return ok(a.shape[1] == width and same and flags == [0, 0, 0], f"width {a.shape[1]} (expected {width}), identical on repeat={same}, popularity flags for the IP host={flags}")


@case("PRE-06", "Replaced", "Same intent as PRE-05 for odd input: v2's URL representation is built for every input without an exception. "
      "(At the API, malformed URLs are refused instead: URL-08.)")
def _():
    from url_features import canon, host_of, rep_matrix
    from scipy import sparse
    D = app_module().D; bad = []
    for x in ["", "   ", "htp:/bad url", "a" * 5000, "http://[::1"]:
        try:
            c = canon(x); M = D.url["tfidf"].transform(D._hv.transform([c])); X = sparse.hstack([M, rep_matrix([host_of(c)], D.url["rank_map"])])
            if X.shape[1] != D._hv.n_features + 3: bad.append(f"{x[:20]!r}: width {X.shape[1]}")
        except Exception as e: bad.append(f"{x[:20]!r}: {e!r}")
    return ok(not bad, "No exception and full width for '', spaces, 'htp:/bad url', a 5,000-character string and 'http://[::1'" if not bad else "; ".join(bad))


@case("PRE-07", "Ported")
def _():
    a, b = score("url", "HTTPS://WWW.GOOGLE.COM/"), score("url", "https://www.google.com/")
    return ok(a["score"] == b["score"] and a["canonical_url"] == b["canonical_url"], f"canonical {a['canonical_url']!r} vs {b['canonical_url']!r}; scores {a['score']} vs {b['score']}")


# ================================================================= Email classifier
@case("EML-01", "Ported", defect="D-17")
def _():
    acc, txt = group_text(run_group("email", "Standard", "Phishing"), "Phishing"); return ok(acc >= 0.9, txt)


@case("EML-02", "Ported", defect="D-10")
def _():
    acc, txt = group_text(run_group("email", "Standard", "Legitimate"), "Legitimate"); return ok(acc >= 0.9, txt)


@case("EML-03", "Ported", defect="D-10, D-17")
def _():
    p = group_text(run_group("email", "Hard case", "Phishing"), "Phishing"); l = group_text(run_group("email", "Hard case", "Legitimate"), "Legitimate")
    return ok(p[0] >= 0.7 and l[0] >= 0.7, f"Hard case phishing: {p[1]}; hard case legitimate: {l[1]}")


@case("EML-04", "Replaced", "v2 returns a probability from 0 to 1 and a label (malicious or benign) plus the terms that moved the score; it has no separate "
      "'confidence' field. Same intent: the score is a valid probability, the label matches the 0.5 line and E-P01 scores higher than E-L01.")
def _():
    p = score("email", SAMPLE["email"]["E-P01"]["Body"], SAMPLE["email"]["E-P01"]["Subject"]); l = score("email", SAMPLE["email"]["E-L01"]["Body"], SAMPLE["email"]["E-L01"]["Subject"])
    good = all(0 <= x["score"] <= 1 and x["label"] == ("malicious" if x["score"] >= ALERT else "benign") for x in (p, l)) and p["score"] > l["score"]
    return ok(good, f"E-P01: {p['label']} {p['score']}; E-L01: {l['label']} {l['score']}")


@case("EML-05", "Ported")
def _():
    s = SAMPLE["email"]["E-P01"]; body, subj = s["Body"], s["Subject"]
    labels = [score("email", b, sj)["label"] for b, sj in ((body, subj), (body.upper(), subj.upper()), ("\n\n  " + "   ".join(body.split(" ")) + "\n\n", subj))]
    return ok(len(set(labels)) == 1, f"labels: original / upper case / extra spacing = {labels}")


@case("EML-06", "Ported")
def _():
    s = SAMPLE["email"]["E-P01"]; pad = " ".join([SAMPLE["email"]["E-L03"]["Body"]] * 3)
    j = score("email", s["Body"] + " " + pad, s["Subject"]); return ok(j["score"] >= ALERT, f"after padding: {j['label']} {j['score']}")


@case("EML-07", "Replaced", "v2 has no /analyze/email; the same request goes to POST /score with channel=email. Rejected = HTTP 4xx.", defect="D-02")
def _():
    r1 = C().post("/score", json={"channel": "email"}); r2 = C().post("/score", json={"channel": "email", "text": ""})
    return ok(400 <= r1.status_code < 500 and 400 <= r2.status_code < 500 and "score" not in r1.text and "score\":" not in r2.text,
              f"no text -> HTTP {r1.status_code}; empty text -> HTTP {r2.status_code}: {r2.text[:120]}")


@case("EML-08", "Ported")
def _():
    s = SAMPLE["email"]["E-P01"]; body = (s["Body"] + " ") * (200_000 // (len(s["Body"]) + 1) + 1); body = body[:200_000]
    t0 = time.perf_counter(); j = score("email", body, s["Subject"]); dt = time.perf_counter() - t0
    return ok(dt <= 5, f"{len(body):,} characters -> {j['label']} {j['score']} in {dt:.2f} s")


@case("EML-09", "Ported")
def _():
    m = json.loads((ROOT / "reports" / "email_metrics.json").read_text()); pooled = m["pooled_test"]["f1"]; lo = m["leave_one_corpus_out"]
    gaps = {k: pooled - v["f1"] for k, v in lo.items()}; worst = max(gaps.values())
    txt = (f"normal (pooled random) test F1 {100 * pooled:.1f}%; held-out corpus F1: " + ", ".join(f"{k} {100 * v['f1']:.1f}%" for k, v in lo.items())
           + f"; mean {100 * sum(v['f1'] for v in lo.values()) / len(lo):.1f}%. Largest gap {100 * worst:.1f} points (reports/email_metrics.json)")
    # The plan's expected result says: if the gap is above 10 points, record it as a limitation.
    return ("Pass", txt) if worst <= 0.10 else ("Known limitation", txt + ". Above 10 points: recorded as a limitation, as the plan says")


@case("EML-10", "Ported")
def _():
    m = json.loads((ROOT / "reports" / "email_metrics.json").read_text()); t = m["pooled_test"]; lo = m["leave_one_corpus_out"]
    honest = sum(v["f1"] for v in lo.values()) / len(lo)
    return ok(t["f1"] >= 0.90, f"reports/email_metrics.json pooled random test: F1 {t['f1']:.4f}, precision {t['precision']:.4f}, recall {t['recall']:.4f}, "
              f"confusion [[{t['tn']}, {t['fp']}], [{t['fn']}, {t['tp']}]]. Honest metric (mean leave-one-corpus-out F1): {honest:.4f}")


# ================================================================= SMS classifier  (the alert score is the API's SMS score: P(spam) + P(smishing) = 1 - P(ham))
SMS_NOTE = "SMS alert score = the score /score returns for SMS, which is 1 - P(ham), i.e. spam or smishing."


@case("SMS-01", "Ported", defect="D-09")
def _():
    acc, txt = group_text(run_group("sms", "Standard", "Phishing"), "Phishing"); return ok(acc >= 0.9, txt + ". " + SMS_NOTE)


@case("SMS-02", "Ported")
def _():
    acc, txt = group_text(run_group("sms", "Standard", "Legitimate"), "Legitimate"); return ok(acc >= 0.9, txt)


@case("SMS-03", "Ported", defect="D-09, D-16")
def _():
    p = group_text(run_group("sms", "Hard case", "Phishing"), "Phishing"); l = group_text(run_group("sms", "Hard case", "Legitimate"), "Legitimate")
    return ok(p[0] >= 0.7 and l[0] >= 0.7, f"Hard case phishing: {p[1]}; hard case legitimate: {l[1]}")


@case("SMS-04", "Ported")
def _():
    a, b = score("sms", SAMPLE["sms"]["S-L01"]["Message"]), score("sms", SAMPLE["sms"]["S-H06"]["Message"])
    return ok(a["score"] < ALERT and b["score"] < ALERT, f"S-L01: {a['label']} {a['score']}, S-H06: {b['label']} {b['score']}")


@case("SMS-05", "Ported")
def _():
    m = SAMPLE["sms"]["S-P04"]["Message"]; long = (" ".join([m] * 20))[:1284]
    a, b = score("sms", "Hi"), score("sms", long)
    return ok(a["score"] < ALERT and b["score"] >= ALERT, f"'Hi' -> {a['label']} {a['score']}; {len(long)}-character message -> {b['label']} {b['score']}")


@case("SMS-06", "Ported")
def _():
    m = SAMPLE["sms"]["S-P04"]["Message"]
    up, em, h4 = score("sms", m.upper()), score("sms", m + " 🎉🎁💰"), score("sms", SAMPLE["sms"]["S-H04"]["Message"])
    return ok(up["score"] >= ALERT and em["score"] >= ALERT, f"upper case: {up['label']} {up['score']}; with emoji: {em['label']} {em['score']}; S-H04 (Roman-script Hindi): {h4['label']} {h4['score']}")


@case("SMS-07", "Replaced", "v2 has no /analyze/sms; the same request goes to POST /score with channel=sms. Rejected = HTTP 4xx.", defect="D-02")
def _():
    r1 = C().post("/score", json={"channel": "sms"}); r2 = C().post("/score", json={"channel": "sms", "text": ""})
    return ok(400 <= r1.status_code < 500 and 400 <= r2.status_code < 500, f"no text -> HTTP {r1.status_code}; empty text -> HTTP {r2.status_code}")


@case("SMS-08", "Replaced", "v2's SMS model has three classes. The plan's 'spam class' (unwanted vs ham) is v2's spam-or-smishing vs ham on its 20% test split. "
      "The honest SMS metric, smishing vs rest, is reported beside it.")
def _():
    m = json.loads((ROOT / "reports" / "sms_metrics.json").read_text()); u, s = m["test_unwanted_vs_ham"], m["test_smishing_vs_rest"]
    return ok(u["f1"] >= 0.90, f"reports/sms_metrics.json spam-or-smishing vs ham: F1 {u['f1']:.4f}, precision {u['precision']:.4f}, recall {u['recall']:.4f}, "
              f"confusion [[{u['tn']}, {u['fp']}], [{u['fn']}, {u['tp']}]]. Honest metric (smishing vs rest): F1 {s['f1']:.4f}")


# ================================================================= URL classifier
@case("URL-01", "Ported")
def _():
    acc, txt = group_text(run_group("url", "Standard", "Phishing"), "Phishing"); return ok(acc >= 0.9, txt)


@case("URL-02", "Ported", defect="D-01")
def _():
    acc, txt = group_text(run_group("url", "Standard", "Legitimate"), "Legitimate"); return ok(acc >= 0.9, txt)


@case("URL-03", "Ported", defect="D-01")
def _():
    p = group_text(run_group("url", "Hard case", "Phishing"), "Phishing"); l = group_text(run_group("url", "Hard case", "Legitimate"), "Legitimate")
    return ok(p[0] >= 0.7 and l[0] >= 0.7, f"Hard case phishing: {p[1]}; hard case legitimate: {l[1]}")


@case("URL-04", "Ported")
def _():
    r = {sid: score("url", SAMPLE["url"][sid]["URL"]) for sid in ("U-P01", "U-P02", "U-P03")}
    return ok(all(j["score"] >= ALERT for j in r.values()), ", ".join(f"{k}: {j['label']} {j['score']}" for k, j in r.items()))


@case("URL-05", "Ported", defect="D-01")
def _():
    out, same = [], True
    for u in ("github.com", "en.wikipedia.org/wiki/Phishing", "www.kluniversity.in"):
        a, b = score("url", u), score("url", "https://" + u); same &= a["label"] == b["label"]
        out.append(f"{u} = {a['label']} {a['score']}; https://{u} = {b['label']} {b['score']}")
    return ok(same, "; ".join(out))


@case("URL-06", "Ported", defect="D-01")
def _():
    a, b = score("url", "https://www.google.com"), score("url", "https://www.google.com/")
    return ok(a["label"] == b["label"], f"without slash: {a['label']} {a['score']}; with slash: {b['label']} {b['score']}")


@case("URL-07", "Ported", defect="D-01")
def _():
    a, b = score("url", SAMPLE["url"]["U-H06"]["URL"]), score("url", SAMPLE["url"]["U-H08"]["URL"])
    return ok(a["score"] < ALERT and b["score"] < ALERT, f"U-H06: {a['label']} {a['score']}, U-H08: {b['label']} {b['score']}")


@case("URL-08", "Replaced", "v2 has no /analyze/url; the same request goes to POST /score with channel=url. Rejected = HTTP 4xx.", defect="D-02")
def _():
    r1 = C().post("/score", json={"channel": "url", "text": "htp:/bad url"}); r2 = C().post("/score", json={"channel": "url", "text": ""})
    def show(r): return f"HTTP {r.status_code}" + (f", {r.json()['label']} {r.json()['score']}" if r.status_code == 200 else f": {r.text[:100]}")
    return ok(400 <= r1.status_code < 500 and 400 <= r2.status_code < 500, f"'htp:/bad url' -> {show(r1)}; '' -> {show(r2)}")


@case("URL-09", "Ported")
def _():
    u = "http://example-long-url.test/" + "a1b2c3d4e5/" * 500; u = u[:5000]
    t0 = time.perf_counter(); j = score("url", u); dt = time.perf_counter() - t0
    return ok(dt <= 5, f"{len(u):,} characters -> {j['label']} {j['score']} in {dt:.3f} s")


@case("URL-10", "Ported")
def _():
    m = json.loads((ROOT / "reports" / "url_metrics.json").read_text()); g = m["string_model"]["grouped_test"]; b = m["feature_benchmark"]["hgb_all_features"]
    return ok(g["f1"] >= 0.90, f"reports/url_metrics.json deployed string model, host-grouped test: F1 {g['f1']:.4f}, precision {g['precision']:.4f}, recall {g['recall']:.4f}, "
              f"confusion [[{g['tn']}, {g['fp']}], [{g['fn']}, {g['tp']}]]. Offline feature benchmark (random split, not deployed): F1 {b['f1']:.4f}")


@case("URL-11", "Ported")
def _():
    real = socket.socket
    class Blocked(socket.socket):
        def connect(self, *a, **k): raise OSError("network disabled by URL-11")
        def connect_ex(self, *a, **k): raise OSError("network disabled by URL-11")
    D = app_module().D
    socket.socket = Blocked
    try: a, b = D.score("url", "github.com"), D.score("url", "192.0.2.45/login")
    except Exception as e: return ok(False, f"exception with sockets disabled: {e!r}")
    finally: socket.socket = real
    return ok(True, f"With sockets disabled: github.com -> {a['label']} {a['score']}; 192.0.2.45/login -> {b['label']} {b['score']}")


# ================================================================= Voice/Video module
VV_NA = ("No voice or video detector exists in v2 or in CP1 (VOICE_IN_CP1 = no; video is Capstone-2), and there is no media-file input. "
         "Calls and video are 'not assessed'. Not built.")


@case("VV-01", "Replaced", "v2 has no stub class. Same intent: the service says video and voice are not available. /health lists them as not trained and "
      "/score answers HTTP 501 for them.")
def _():
    h = C().get("/health").json(); r = C().post("/score", json={"channel": "video", "text": "hello"})
    good = {"voice", "video"} <= set(h.get("not_trained", [])) and r.status_code == 501
    return ok(good, f"/health not_trained={h.get('not_trained')}; /score channel=video -> HTTP {r.status_code}")


@case("VV-02", "Replaced", "Same intent as VV-01 with odd input: every call for the video channel gets a clean answer (501 not available, or 422 for a missing text), never a 500.")
def _():
    codes = []
    for body in ({"channel": "video"}, {"channel": "video", "text": "x"}, {"channel": "video", "text": "t" * 100_000}, {"channel": "video", "text": None}):
        codes.append(C().post("/score", json=body).status_code)
    return ok(all(c in (422, 501) for c in codes), f"HTTP codes for no text, a string, a 100,000-character transcript and null: {codes}")


@case("VV-03", "Replaced", "v2 has no /analyze. The S-07 case goes to POST /correlate with a channel='video' event. Expected: the email is scored and the video "
      "comes back 'not assessed'.", defect="D-13")
def _():
    ev = [e for e in scenario_events("S-07")[0] if e["channel"] in ("email", "video")]
    r = correlate(ev)
    if r.status_code != 200: return ok(False, f"HTTP {r.status_code}: {r.text[:160]}")
    j = r.json(); ch = {e["channel"]: e for e in j["events"]}
    good = ch["email"].get("score") is not None and ch["video"].get("assessed") is False
    return ok(good, describe(j))


@case("VV-04", "Replaced", "v2 has no evidence list. Same intent: a video event never adds risk. It is kept out of the correlation features, the shared tokens and the window.", defect="D-13")
def _():
    r = correlate([{"channel": "email", "text": SAMPLE["email"]["E-P01"]["Body"], "subject": SAMPLE["email"]["E-P01"]["Subject"], "time": "0"},
                   {"channel": "video", "text": "This is your bank manager. Verify your account now.", "time": "1"}])
    if r.status_code != 200: return ok(False, f"HTTP {r.status_code}: {r.text[:160]}")
    j = r.json(); f = j["features"]
    good = f["n_events"] == 1 and j["window_event_indices"] == [0] and not j["events"][1].get("in_window")
    return ok(good, describe(j) + f"; features n_events={f['n_events']}, window events {j['window_event_indices']}")


@case("VV-05", "Replaced", "v2 has no verdicts. 'Not SAFE (for example cannot assess)' becomes: the response says CANNOT_ASSESS (or rejects the request with "
      "HTTP 4xx) and gives no risk score.", defect="D-03")
def _():
    r, j = scenario("S-08")
    good = (r.status_code == 200 and j.get("status") == "CANNOT_ASSESS" and j.get("bundle_risk") is None) or 400 <= r.status_code < 500
    return ok(good, SCENARIO_RESULTS["S-08"])


for _cid in ("VV-06", "VV-07", "VV-08", "VV-09", "VV-10"):
    case(_cid, "N/A", VV_NA)(lambda: na(VV_NA))


# ================================================================= Correlation engine (fixed scores: the engine is tested on its own)
FIX = "Uses fixed detector scores through v2's correlation engine (Fusion.risk), as the plan does."


@case("COR-01", "Replaced", "v2 has no evidence strings or bonus. Same intent: the shared link is found as a shared identity token and the link features are on. " + FIX)
def _():
    r = engine_fixed([("email", .70, "Verify now at bit.ly/xyz", 0), ("sms", .65, "Verify now: bit.ly/xyz", 1), ("url", .95, "bit.ly/xyz", 2)])
    f = r["features"]
    return ok("dom:bit.ly" in r["shared"] and f["shares_identity"] == 1 and f["frac_events_linked"] == 1, f"shared tokens {r['shared']}; shares_identity {f['shares_identity']}; risk {r['risk']:.3f}")


@case("COR-02", "Replaced", "Same intent as COR-01: the flagged URL inside the email gives the email the URL's domain token, shared with the URL event. " + FIX)
def _():
    from predict import extract_ids
    e, u = extract_ids("email", "Your account is locked. Unlock it at http://secure-bank-verify.xyz/login"), extract_ids("url", "http://secure-bank-verify.xyz/login")
    r = engine_fixed([("email", .70, "Your account is locked. Unlock it at http://secure-bank-verify.xyz/login", 0), ("sms", .10, "See you at 5", 1), ("url", .95, "http://secure-bank-verify.xyz/login", 2)])
    return ok(set(u) <= set(e) and "dom:secure-bank-verify.xyz" in r["shared"], f"email tokens {e}; url tokens {u}; shared {r['shared']}")


@case("COR-03", "Replaced", "Same intent as COR-02 for the SMS. " + FIX)
def _():
    from predict import extract_ids
    s = extract_ids("sms", "Unlock now: secure-bank-verify.xyz/login")
    r = engine_fixed([("email", .10, "Lunch at noon?", 0), ("sms", .65, "Unlock now: secure-bank-verify.xyz/login", 1), ("url", .95, "secure-bank-verify.xyz/login", 2)])
    return ok("dom:secure-bank-verify.xyz" in s and "dom:secure-bank-verify.xyz" in r["shared"], f"sms tokens {s}; shared {r['shared']}")


@case("COR-04", "Replaced", "v2 reports a shared link as a fact whatever the scores, and the learned model decides its weight; there is no bonus. Same intent: "
      "three legitimate channels sharing a link and a brand raise no alert (bundle risk below 0.5). " + FIX)
def _():
    r = engine_fixed([("email", .10, "Your SecureBank statement is at securebank.com/statements", 0), ("sms", .12, "SecureBank: statement ready at securebank.com/statements", 1),
                      ("url", .05, "securebank.com/statements", 2)])
    return ok(r["risk"] < ALERT, f"scores 0.10 / 0.12 / 0.05; shared {r['shared']}; bundle risk {r['risk']:.3f}")


@case("COR-05", "N/A", "v2 has no rule that link evidence needs a risky URL channel. Shared links are identity tokens and the learned model weighs them with the scores.")
def _(): return na(CASES["COR-05"]["why"])


@case("COR-06", "N/A", "v2 has no rule that identity evidence needs both email and SMS to be risky. Brand names are not identity tokens in v2 (only domains, phone numbers and the identity field).")
def _(): return na(CASES["COR-06"]["why"])


@case("COR-07", "Ported", "")
def _():
    from predict import extract_ids
    a = extract_ids("email", "Urgent request: please verify the attached form today."); b = extract_ids("sms", "Urgent request. Verify today.")
    r = engine_fixed([("email", .8, "Urgent request: please verify the attached form today.", 0), ("sms", .8, "Urgent request. Verify today.", 1)])
    return ok(r["shared"] == [], f"email tokens {a}; sms tokens {b}; shared {r['shared']}")


@case("COR-08", "N/A", "v2 has no bonus and so no MAX_BONUS cap. The bundle risk is a probability from the learned model, between 0 and 1 by construction.")
def _(): return na(CASES["COR-08"]["why"])


@case("COR-09", "Replaced", "Same intent as VV-04 at the API: a video event never contributes to the bundle risk.", defect="D-13")
def _():
    a = correlate([{"channel": "email", "text": SAMPLE["email"]["E-P01"]["Body"], "subject": SAMPLE["email"]["E-P01"]["Subject"], "time": "0"}])
    b = correlate([{"channel": "email", "text": SAMPLE["email"]["E-P01"]["Body"], "subject": SAMPLE["email"]["E-P01"]["Subject"], "time": "0"},
                   {"channel": "video", "text": "Verify your account now", "time": "1"}])
    if b.status_code != 200: return ok(False, f"email alone -> HTTP {a.status_code}; email + video -> HTTP {b.status_code}: {b.text[:120]}")
    return ok(a.json()["bundle_risk"] == b.json()["bundle_risk"], f"bundle risk email alone {a.json()['bundle_risk']}; with a video event {b.json()['bundle_risk']}")


@case("COR-10", "Replaced", "v2 has one alert line (0.5), so S-03's fixed scores 0.55 / 0.52 / 0.58 each alert on their own and the SUSPICIOUS band does not exist. "
      "Same intent where it can be kept: the bundle alerts and its risk is at least the best single score. The lift from below the line is SYS-14 / TC-06. " + FIX)
def _():
    r = engine_fixed([("email", .55, "Click bit.ly/xyz to verify your account", 0), ("sms", .52, "Verify your account now: bit.ly/xyz", 1), ("url", .58, "bit.ly/xyz", 2)])
    return ok(r["risk"] >= ALERT and r["risk"] >= r["max_single"], f"best single 0.58 (alerts alone); bundle risk {r['risk']:.3f}; shared {r['shared']}")


@case("COR-11", "N/A", "v2 has no time-evidence rule that needs email, SMS and URL timestamps. The time span of a window is a model feature for any two or more events.")
def _(): return na(CASES["COR-11"]["why"])


@case("COR-12", "Replaced", "v2 has no evidence strings. Same intent: events 3 and 6 days apart fall in separate 60-minute windows, are not linked, and the bundle risk is the strongest single event. " + FIX)
def _():
    r = engine_fixed([("email", .8, "Verify at secure-bank-verify.xyz/login", 0), ("sms", .8, "Verify at secure-bank-verify.xyz/login", 4320), ("url", .8, "secure-bank-verify.xyz/login", 8640)])
    return ok(r["n_windows"] == 3 and r["shared"] == [] and abs(r["risk"] - r["max_single"]) < 0.002, f"windows {r['n_windows']}; shared {r['shared']}; risk {r['risk']:.3f} (strongest single {r['max_single']})")


@case("COR-13", "Replaced", "v2 has no evidence text. Same intent: the window's time span is the real span (90 s = 1.5 minutes).")
def _():
    ev, _ = scenario_events("S-10"); r = correlate(ev); j = r.json()
    return ok(r.status_code == 200 and j["window_time_span_minutes"] == 1.5, f"window time span {j.get('window_time_span_minutes')} minutes; windows {j.get('n_windows')}")


@case("COR-14", "Replaced", "Same intent: the shared link on a .online host is found as a shared identity token (full public suffix list). " + FIX)
def _():
    r = engine_fixed([("email", .9, "Verify your account now at secure-bank-verify.online/login", 0), ("sms", .9, "Verify now at secure-bank-verify.online/login", 1), ("url", .9, "secure-bank-verify.online/login", 2)])
    return ok("dom:secure-bank-verify.online" in r["shared"], f"shared {r['shared']}")


@case("COR-15", "Ported")
def _():
    ev, _ = scenario_events("S-01"); a, b = correlate(ev).json(), correlate(ev).json()
    return ok(a == b, f"identical={a == b}; bundle risk {a.get('bundle_risk')}")


@case("COR-16", "N/A", "v2 has no risk threshold of 20 and no separate phishing label for evidence. Its one line is 0.5.")
def _(): return na(CASES["COR-16"]["why"])


@case("COR-17", "Replaced", "v2 has no bonus. Same intent: missing content does not crash the service; it is rejected with HTTP 4xx (no 500).")
def _():
    codes = [correlate([{"channel": c, "text": None} for c in ("email", "sms", "url", "video")]).status_code, C().post("/correlate", json={}).status_code]
    return ok(all(400 <= c < 500 for c in codes), f"null texts -> HTTP {codes[0]}; empty body -> HTTP {codes[1]}")


# ================================================================= Scoring and verdict
@case("SCO-01", "Replaced", "v2 has no SAFE / SUSPICIOUS / HIGH RISK bands (0-30-60-100). Its one line is 0.5. Same intent: the boundary is placed exactly; "
      "0.5 alerts, just below does not, for a channel score and for the bundle label.")
def _():
    D = app_module().D
    labs = [D._pack("email", p, {})["label"] for p in (0.0, 0.4999, 0.5, 1.0)]
    r = engine_fixed([("url", 0.5, "x.example", 0)]); r2 = engine_fixed([("url", 0.4999, "x.example", 0)])
    return ok(labs == ["benign", "benign", "malicious", "malicious"] and r["risk"] >= ALERT and r2["risk"] < ALERT,
              f"channel labels at 0, 0.4999, 0.5, 1 -> {labs}; one-event bundle at 0.5 -> risk {r['risk']}, at 0.4999 -> risk {r2['risk']}")


@case("SCO-02", "Replaced", "v2's bundle risk is a learned model, not min(100, best + bonus), so the formula part is N/A. The second part is kept: the bundle risk "
      "is never below the best channel score, for S-01, S-02 and S-05.")
def _():
    out, good = [], True
    for sid in ("S-01", "S-02", "S-05"):
        r, j = scenario(sid); best = max(e["score"] for e in j["events"] if e.get("score") is not None)
        good &= j["bundle_risk"] >= best; out.append(f"{sid}: best {best:.3f}, bundle {j['bundle_risk']:.3f}")
    return ok(good, "; ".join(out))


@case("SCO-03", "N/A", "v2 returns no correlation_delta field (no bonus). It returns bundle_risk and, for comparison, bundle_risk_without_correlation.")
def _(): return na(CASES["SCO-03"]["why"])


@case("SCO-04", "Replaced", "v2 scores are probabilities from 0 to 1 (the plan's 0-100 scale divided by 100).")
def _():
    s = [sample_score(ch, sid)[0] for ch in ("email", "sms", "url") for sid in SAMPLE[ch]]
    return ok(all(0 <= x <= 1 for x in s), f"{len(s)} samples, min {min(s):.4f}, max {max(s):.4f}")


@case("SCO-05", "Replaced", "v2 has no /analyze. Same intent through /correlate: a URL-only case returns one URL event and no other channel.")
def _():
    j = correlate([{"channel": "url", "text": "https://www.amazon.in/"}]).json(); f = j["features"]
    return ok([e["channel"] for e in j["events"]] == ["url"] and f["has_email"] == 0 and f["has_sms"] == 0, f"channels analysed: {[e['channel'] for e in j['events']]}")


@case("SCO-06", "Replaced", "v2 has no analyze({}). The empty case goes to POST /correlate. Expected: rejected with HTTP 4xx or CANNOT_ASSESS, never a low risk.", defect="D-03")
def _():
    r1, r2 = C().post("/correlate", json={}), C().post("/correlate", json={"events": []})
    good = all(400 <= r.status_code < 500 or (r.status_code == 200 and r.json().get("status") == "CANNOT_ASSESS") for r in (r1, r2))
    return ok(good, f"POST {{}} -> HTTP {r1.status_code}; POST {{\"events\": []}} -> HTTP {r2.status_code}: {r2.text[:100]}")


@case("SCO-07", "Ported")
def _():
    ev, _ = scenario_events("S-01")
    runs = [json.dumps([correlate(ev).json(), score("email", SAMPLE["email"]["E-P01"]["Body"], SAMPLE["email"]["E-P01"]["Subject"]),
                        score("sms", SAMPLE["sms"]["S-P04"]["Message"]), score("url", SAMPLE["url"]["U-P01"]["URL"])], sort_keys=True) for _ in range(5)]
    return ok(len(set(runs)) == 1, f"5 runs, distinct results: {len(set(runs))}")


@case("SCO-08", "Replaced", "Same intent through /correlate: with S-06, the bundle risk is at least the email score.", defect="D-18")
def _():
    r, j = scenario("S-06"); em = [e["score"] for e in j["events"] if e["channel"] == "email"][0]
    return ok(j["bundle_risk"] >= em, describe(j))


# ================================================================= Service (API)
@case("API-01", "Replaced", "v2's /health lists the trained channels and the untrained ones instead of a readiness map.")
def _():
    r = C().get("/health"); j = r.json()
    return ok(r.status_code == 200 and set(j.get("channels", [])) >= {"email", "sms", "url"} and "video" in j.get("not_trained", []), f"HTTP {r.status_code}: {j}")


@case("API-02", "Replaced", "v2 has no /analyze/email; POST /score with channel=email. v2 returns score (0-1), label (malicious/benign) and the terms that moved the score instead of confidence and top_signals.")
def _():
    s = SAMPLE["email"]["E-P01"]; r = C().post("/score", json={"channel": "email", "text": s["Body"], "subject": s["Subject"]}); j = r.json()
    good = r.status_code == 200 and {"score", "label", "top_terms_toward_malicious"} <= set(j) and j["label"] == "malicious"
    return ok(good, f"HTTP {r.status_code}: label {j.get('label')}, score {j.get('score')}, top terms {[t for t, _ in j.get('top_terms_toward_malicious', [])][:5]}")


@case("API-03", "Replaced", "POST /score with channel=sms instead of /analyze/sms.")
def _():
    j = score("sms", SAMPLE["sms"]["S-P04"]["Message"]); return ok(j["label"] == "malicious", f"HTTP 200: label {j['label']}, score {j['score']}")


@case("API-04", "Replaced", "POST /score with channel=url instead of /analyze/url.")
def _():
    j = score("url", SAMPLE["url"]["U-P01"]["URL"]); return ok(j["label"] == "malicious", f"HTTP 200: label {j['label']}, score {j['score']}")


@case("API-05", "Replaced", "POST /correlate instead of /analyze. It returns per-event scores, bundle_risk, bundle_label, shared identity tokens and the window instead of combined_score, verdict and correlation_delta.")
def _():
    r, j = scenario("S-01")
    good = r.status_code == 200 and {"events", "bundle_risk", "bundle_label", "shared_identity_tokens", "window_minutes"} <= set(j)
    return ok(good, f"HTTP {r.status_code}: " + (describe(j) if r.status_code == 200 else r.text[:150]))


@case("API-06", "Ported")
def _():
    r = C().post("/score", content='{"subject": ', headers={"Content-Type": "application/json"}); h = C().get("/health")
    return ok(r.status_code in (400, 422) and h.status_code == 200, f"HTTP {r.status_code}; service still answers /health with {h.status_code}")


@case("API-07", "Ported")
def _():
    a = C().post("/score", json={"channel": "sms", "text": 12345}); b = C().post("/score", json={"channel": "email", "text": "hello there", "subject": ["a", "b"]})
    return ok(a.status_code == 422 and b.status_code == 422, f"sms text=12345 -> HTTP {a.status_code}; email subject=list -> HTTP {b.status_code}")


@case("API-08", "Replaced", "v2 takes one 'time' per event (minutes or ISO). The S-01 case goes to /correlate with times 'a', 'b', 'c'.")
def _():
    ev, _ = scenario_events("S-01")
    for e, t in zip(ev, "abc"): e["time"] = t
    r = correlate(ev); return ok(400 <= r.status_code < 500, f"HTTP {r.status_code}: {r.text[:140]}")


@case("API-09", "Replaced", "v2 has no per-channel readiness map. Same intent: with the SMS model file missing, the service still starts, SMS is 'not assessed', and email and URL are still scored.", defect="D-14")
def _():
    import shutil, tempfile
    tmp = Path(tempfile.mkdtemp(prefix="cp1_api09_"))        # a copy of the app whose models/ folder has no SMS model
    shutil.copy(ROOT / "api.py", tmp); shutil.copytree(ROOT / "src", tmp / "src", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "models", tmp / "models", ignore=shutil.ignore_patterns("sms_model.joblib", "candidates"))
    if (ROOT / "console" / "dist").exists(): shutil.copytree(ROOT / "console" / "dist", tmp / "console" / "dist")
    code = ("import sys, json; sys.path.insert(0, 'src'); sys.path.insert(0, '.')\n"
            "from fastapi.testclient import TestClient\n"
            "try:\n import api\nexcept Exception as e:\n print(json.dumps({'start': 'failed', 'error': repr(e)[:200]})); raise SystemExit(0)\n"
            "c = TestClient(api.app); h = c.get('/health').json()\n"
            "ev = [{'channel': 'email', 'text': 'Your account is suspended. Verify at secure-bank-verify.xyz/login', 'time': '0'}, {'channel': 'sms', 'text': 'Verify now at secure-bank-verify.xyz/login', 'time': '1'}, {'channel': 'url', 'text': 'secure-bank-verify.xyz/login', 'time': '2'}]\n"
            "r = c.post('/correlate', json={'events': ev}); print(json.dumps({'start': 'ok', 'health': h, 'status': r.status_code, 'body': r.json()}))\n")
    p = subprocess.run([sys.executable, "-c", code], cwd=tmp, capture_output=True, text=True, timeout=300)
    shutil.rmtree(tmp, ignore_errors=True)
    try: j = json.loads(p.stdout.strip().splitlines()[-1])
    except Exception: return ok(False, f"could not run: {p.stderr[-200:]}")
    if j["start"] != "ok": return ok(False, f"the API did not start with the SMS model missing: {j['error']}")
    b = j["body"]; ch = {e["channel"]: e for e in b.get("events", [])}
    good = j["status"] == 200 and ch.get("sms", {}).get("assessed") is False and ch.get("email", {}).get("score") is not None and ch.get("url", {}).get("score") is not None
    return ok(good, f"/health: {j['health'].get('not_available', j['health'].get('not_trained'))}; /correlate HTTP {j['status']}: " + (describe(b) if j["status"] == 200 else str(b)[:150]))


@case("API-10", "Ported")
def _():
    reqs = [("email", SAMPLE["email"][k]["Body"], SAMPLE["email"][k]["Subject"]) for k in ("E-P01", "E-L01", "E-P04")] + \
           [("sms", SAMPLE["sms"][k]["Message"], "") for k in ("S-P04", "S-L01", "S-P01")] + [("url", SAMPLE["url"][k]["URL"], "") for k in ("U-P01", "U-L01", "U-H06")]
    reqs = (reqs * 3)[:20]
    serial = [score(*q) for q in reqs]
    with ThreadPoolExecutor(8) as ex: par = list(ex.map(lambda q: C().post("/score", json={"channel": q[0], "text": q[1], "subject": q[2]}), reqs))
    match = sum(1 for a, b in zip(serial, par) if b.status_code == 200 and b.json() == a)
    return ok(match == 20, f"{match} of 20 parallel responses matched their own serial result")


@case("API-11", "Replaced", "Same intent: hostile strings are data, every answer is JSON and nothing runs. Email and SMS answer 200. For URL, a string that is not a URL may be "
      "refused with 422 instead, because URL-08 requires invalid URLs to be rejected; a 500 or a non-JSON answer fails.")
def _():
    codes, alljson = [], True
    for s in ("<script>alert(1)</script>", "'; DROP TABLE users;--", "../../etc/passwd"):
        for ch in ("email", "sms", "url"):
            r = C().post("/score", json={"channel": ch, "text": s}); codes.append((ch, r.status_code))
            try: r.json()
            except Exception: alljson = False
    good = alljson and all(c == 200 or (ch == "url" and c == 422) for ch, c in codes)
    return ok(good, f"9 requests, HTTP codes {sorted(set(codes))}; all JSON={alljson}; none executed")


@case("API-12", "Replaced", "Stricter than the plan, as CP1_FINISH_TASK.md R2-04 asks: CORS with explicit origins, never '*'. The console's dev origin (localhost:5173) "
      "gets the header and the preflight succeeds; an unknown origin gets no header.", defect="D-06")
def _():
    o = "http://localhost:5173"
    g = C().get("/health", headers={"Origin": o}); p = C().options("/correlate", headers={"Origin": o, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"})
    acao = g.headers.get("access-control-allow-origin"); pa = p.headers.get("access-control-allow-origin")
    bad = C().get("/health", headers={"Origin": "http://evil.example"}).headers.get("access-control-allow-origin")
    # CP1_FINISH_TASK.md R2-04: explicit origins, never '*'. The console's dev origin is allowed; any other origin is not.
    good = acao == o and pa == o and p.status_code == 200 and bad is None
    return ok(good, f"Allow-Origin for {o}: GET {acao}, preflight {pa} (HTTP {p.status_code}); for http://evil.example: {bad}")


@case("API-13", "Ported")
def _():
    body = ("Dear customer, please verify your account. " * 50000)[:2_000_000]
    t0 = time.perf_counter(); r = C().post("/score", json={"channel": "email", "text": body}); dt = time.perf_counter() - t0
    return ok(dt <= 5 and r.status_code in (200, 413), f"{len(body) / 1e6:.1f} MB body -> HTTP {r.status_code} in {dt:.2f} s")


# ================================================================= Console (UI): run by scripts/ui_checks.py (Playwright), which writes reports/ui_checks.json
def ui(cid):
    p = ROOT / "reports" / "ui_checks.json"
    if not p.exists(): return not_run("The console checks run with Playwright in scripts/ui_checks.py (Phase 2.4); reports/ui_checks.json does not exist yet.")
    j = json.loads(p.read_text()).get(cid)
    if not j: return not_run(f"{cid} is not in reports/ui_checks.json")
    return (j["status"], j["actual"])


for _cid, _why in (("UI-01", "Same check on v2's console, served by FastAPI. Panels: email, SMS and URL inputs and a voice/video line that reads 'not assessed'."),
                   ("UI-02", "Same check: E-P01 and E-L01 through the console, compared with /score."),
                   ("UI-03", "Preset scenario 1 = TC-04 (KYC campaign). 'Correlated at or above each single score' is kept."),
                   ("UI-04", "Preset scenario 2 = TC-06 (weak parcel campaign). 'Correlated at or above each single score' is kept."),
                   ("UI-05", "Same check: an email, an SMS and a URL entered by hand; the bundle risk and the shared tokens (v2's evidence) are shown."),
                   ("UI-06", "Same check with the API stopped."),
                   ("UI-07", "Same check at 1366x768 and 1920x1080 in Chromium and Edge (Edge only if it is installed).")):
    case(_cid, "Replaced" if _cid in ("UI-01", "UI-03", "UI-04", "UI-05") else "Ported", _why)((lambda c: (lambda: ui(c)))(_cid))


# ================================================================= End-to-end cases (Scenarios S-01 to S-13)
def scen_check(sid, want_alert, want_shared=None, extra=None):
    r, j = scenario(sid)
    if r.status_code != 200: return ok(False, SCENARIO_RESULTS[sid])
    good = (j["bundle_risk"] >= ALERT) is want_alert
    if want_shared is not None: good &= (want_shared in j["shared_identity_tokens"]) if want_shared else (j["shared_identity_tokens"] == [])
    if extra: good &= extra(j)
    return ok(good, SCENARIO_RESULTS[sid])


E2E = "HIGH RISK -> alert (bundle risk >= 0.5), SAFE -> no alert. v2's evidence for a shared link is a shared identity token."


@case("SYS-01", "Replaced", E2E)
def _(): return scen_check("S-01", True, "dom:bit.ly")


@case("SYS-02", "Replaced", E2E)
def _(): return scen_check("S-02", True, "dom:secure-bank-verify.xyz")


@case("SYS-03", "Replaced", "S-03 uses fixed scores 0.55 / 0.52 / 0.58, which /correlate cannot take, so it runs through the engine (as COR-10). With v2's single line at 0.5 "
      "the best channel already alerts. Kept: the bundle alerts and is at least the best single score. The lift from below the line is SYS-14 / TC-06.")
def _():
    ev, fx = scenario_events("S-03")
    r = engine_fixed([(e["channel"], fx[e["channel"]], e["text"], float(e["time"])) for e in ev])
    SCENARIO_RESULTS["S-03"] = f"fixed scores email 0.55, sms 0.52, url 0.58 through the engine: best single 0.58 (alerts alone); bundle risk {r['risk']:.3f}; shared {r['shared']}"
    return ok(r["risk"] >= ALERT and r["risk"] >= r["max_single"], SCENARIO_RESULTS["S-03"])


@case("SYS-04", "Replaced", E2E)
def _(): return scen_check("S-04", False, "")


@case("SYS-05", "Replaced", E2E)
def _(): return scen_check("S-05", True, "")


@case("SYS-06", "Replaced", E2E)
def _(): return scen_check("S-06", True, "")


@case("SYS-07", "Replaced", E2E + " The video event must come back 'not assessed' and stay out of the shared tokens and features.", defect="D-13")
def _():
    return scen_check("S-07", True, None, lambda j: all(e.get("assessed") is False for e in j["events"] if e["channel"] == "video") and j["features"]["n_events"] == 2)


@case("SYS-08", "Replaced", "'Anything except SAFE (for example cannot assess)' becomes: CANNOT_ASSESS with no risk score, or HTTP 4xx.", defect="D-03")
def _():
    r, j = scenario("S-08")
    return ok((r.status_code == 200 and j.get("status") == "CANNOT_ASSESS" and j.get("bundle_risk") is None) or 400 <= r.status_code < 500, SCENARIO_RESULTS["S-08"])


@case("SYS-09", "Replaced", E2E + " 'No time-proximity evidence' = three separate windows and no shared token inside the scored window.")
def _(): return scen_check("S-09", True, "", lambda j: j["n_windows"] == 3)


@case("SYS-10", "Replaced", E2E + " 'Time-proximity evidence' = one window holding all three events.")
def _(): return scen_check("S-10", True, "dom:secure-bank-verify.xyz", lambda j: j["n_windows"] == 1 and len(j["window_event_indices"]) == 3)


@case("SYS-11", "Replaced", E2E)
def _(): return scen_check("S-11", True, "dom:secure-bank-verify.online")


@case("SYS-12", "Replaced", "'Rejected (HTTP 4xx). Not reported as SAFE' is kept as written.", defect="D-03")
def _():
    r = C().post("/correlate", json={"events": []}); r2 = C().post("/correlate", json={})
    SCENARIO_RESULTS["S-12"] = f"POST {{\"events\": []}} -> HTTP {r.status_code}; POST {{}} -> HTTP {r2.status_code}"
    return ok(400 <= r.status_code < 500 and 400 <= r2.status_code < 500, SCENARIO_RESULTS["S-12"])


@case("SYS-13", "Replaced", E2E, defect="D-01")
def _(): return scen_check("S-13", False, "")


@case("SYS-14", "Ported", "Kept as written: S-01, S-02 and S-11 with the real models. TC-06 (hand-written) is the case where correlation lifts a bundle over the line; see R2-09.", defect="D-12")
def _():
    out, lifted = [], 0
    for sid in ("S-01", "S-02", "S-11"):
        r, j = scenario(sid); single = j["single_channel_alert"]; final = j["bundle_risk"] >= ALERT
        lifted += (final and not single); out.append(f"{sid}: best single {'alert' if single else 'no alert'}, bundle {'alert' if final else 'no alert'} ({j['bundle_risk']:.3f})")
    return ok(lifted >= 1, "; ".join(out) + (". The detectors already alert on all three, so correlation cannot raise the verdict." if not lifted else ""))


# ================================================================= Non-functional
def lat(n, fn):
    ts = []
    for _ in range(n):
        t0 = time.perf_counter(); fn(); ts.append((time.perf_counter() - t0) * 1000)
    ts.sort(); return statistics.median(ts), ts[int(round(0.95 * (len(ts) - 1)))]


def via(): return "over HTTP to " + os.environ["CP1_API_URL"] if os.environ.get("CP1_API_URL") else "in-process (FastAPI TestClient)"


def bench():
    p = ROOT / "reports" / "benchmark.json"
    return json.loads(p.read_text()) if p.exists() else None


@case("NFR-01", "Ported", "Measured here in-process or over HTTP; scripts/benchmark.py (Phase 4.2) measures 100 requests per channel over real HTTP and its result is used when present.")
def _():
    b = bench()
    if b and b.get("per_channel"):
        pc = b["per_channel"]; good = all(v["median_ms"] <= 2000 for v in pc.values())
        return ok(good, "scripts/benchmark.py over real HTTP, " + f"{b['n_per_channel']} requests each ({b['machine']}): " + "; ".join(f"{k} {v['median_ms']:.0f} ms / {v['p95_ms']:.0f} ms" for k, v in pc.items()))
    s = {"email": lambda: score("email", SAMPLE["email"]["E-P01"]["Body"], SAMPLE["email"]["E-P01"]["Subject"]), "sms": lambda: score("sms", SAMPLE["sms"]["S-P04"]["Message"]),
         "url": lambda: score("url", SAMPLE["url"]["U-P01"]["URL"])}
    m = {k: lat(50, f) for k, f in s.items()}
    return ok(all(v[0] <= 2000 for v in m.values()), f"Median / 95th percentile over 50 requests each ({via()}): " + "; ".join(f"{k} {v[0]:.0f} ms / {v[1]:.0f} ms" for k, v in m.items()))


@case("NFR-02", "Replaced", "S-01 goes to /correlate instead of /analyze.")
def _():
    b = bench()
    if b and b.get("full_case"):
        fc = b["full_case"]; return ok(fc["max_ms"] <= 5000, f"scripts/benchmark.py over real HTTP, {fc['n']} full cases: median {fc['median_ms']:.0f} ms, 95th percentile {fc['p95_ms']:.0f} ms, max {fc['max_ms']:.0f} ms")
    ev, _ = scenario_events("S-01"); ts = []
    for _ in range(5):
        t0 = time.perf_counter(); correlate(ev); ts.append((time.perf_counter() - t0) * 1000)
    return ok(max(ts) <= 5000, f"S-01 through POST /correlate, 5 runs ({via()}): " + ", ".join(f"{t:.0f} ms" for t in ts))


@case("NFR-03", "Ported")
def _():
    reqs = [("email", SAMPLE["email"]["E-P01"]["Body"]), ("sms", SAMPLE["sms"]["S-P04"]["Message"]), ("url", SAMPLE["url"]["U-P01"]["URL"])] * 34
    ts, errs = [], 0
    for ch, t in reqs[:100]:
        t0 = time.perf_counter(); r = C().post("/score", json={"channel": ch, "text": t}); ts.append((time.perf_counter() - t0) * 1000); errs += r.status_code != 200
    a, b = statistics.median(ts[:20]), statistics.median(ts[-20:])
    return ok(errs == 0 and b <= 1.5 * a + 5, f"errors: {errs}; median of first 20 = {a:.0f} ms, last 20 = {b:.0f} ms")


@case("NFR-04", "Ported", "Uses scripts/secret_scan.py over the files git tracks or would add.")
def _():
    p = subprocess.run([sys.executable, str(ROOT / "scripts" / "secret_scan.py")], cwd=ROOT, capture_output=True, text=True)
    return ok(p.returncode == 0, p.stdout.strip().splitlines()[-1] if p.stdout.strip() else p.stderr[-200:])


@case("NFR-05", "Ported", "Run by scripts/nfr05_fresh_clone.py (Phase 4.4), which writes reports/nfr05_fresh_clone.json.")
def _():
    p = ROOT / "reports" / "nfr05_fresh_clone.json"
    if not p.exists(): return not_run("Runs in Phase 4.4 on the frozen build (scripts/nfr05_fresh_clone.py).")
    j = json.loads(p.read_text()); return (j["status"], j["actual"])


@case("NFR-06", "Replaced", "The serving code now includes the event store, which may store message text only when CP1_STORE_CONTENT=1. Same intent: a message sent through the API "
      "never appears in a log line, and nothing is written to disk unless the event store is used.")
def _():
    marker = "nfr06-marker-" + str(int(time.time() * 1000)); before = _snapshot()
    buf_out, buf_err, logs = io.StringIO(), io.StringIO(), io.StringIO()
    h = logging.StreamHandler(logs); root = logging.getLogger(); root.addHandler(h); old = root.level; root.setLevel(logging.DEBUG)
    try:
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            score("email", f"Please verify {marker} now"); score("sms", f"verify {marker}"); correlate([{"channel": "sms", "text": f"verify {marker}"}])
    finally: root.removeHandler(h); root.setLevel(old)
    seen = [n for n, b in (("stdout", buf_out), ("stderr", buf_err), ("logging", logs)) if marker in b.getvalue()]
    changed = [p for p in _changed_files(before) if p.suffix not in (".pyc",)]
    with_marker = [p.relative_to(ROOT).as_posix() for p in changed if p.is_file() and marker.encode() in p.read_bytes()]
    src = [p for p in ("api.py", "src/predict.py", "src/fusion.py", "src/url_features.py") if (ROOT / p).exists()]       # common.py: serving uses clean_text only; save_json is a training helper
    writes = [p for p in src if re.search(r"\blogging\.(info|debug|warning|error)\(|\bprint\(|\.write_text\(|open\([^)]*['\"]w", (ROOT / p).read_text(encoding="utf-8").split('if __name__ == "__main__":')[0])]
    return ok(not seen and not with_marker and not writes,
              f"marker found in output: {seen or 'nowhere'}; files changed during the requests: {[p.relative_to(ROOT).as_posix() for p in changed] or 'none'}"
              f" (holding the marker: {with_marker or 'none'}); serving files with log or write calls: {writes or 'none'}")


def _snapshot():
    skip = {".venv", ".git", "_baseline_v2", "node_modules", "__pycache__", ".pytest_cache", "data"}
    return {p: p.stat().st_mtime_ns for p in ROOT.rglob("*") if p.is_file() and not (set(p.relative_to(ROOT).parts) & skip)}


def _changed_files(before):
    after = _snapshot(); return [p for p, m in after.items() if before.get(p) != m and p.name != OUT.name]


@case("NFR-07", "Ported", "Compares this run with reports/regression_baseline.json (the results on the build before the last change, Phase 4).")
def _():
    p = ROOT / "reports" / "regression_baseline.json"
    if not p.exists(): return not_run("Runs in Phase 4 after the final code change: needs reports/regression_baseline.json from the earlier run.")
    base = json.loads(p.read_text())["cases"]
    worse = [k for k, v in base.items() if v["status"] == "Pass" and RESULTS.get(k, {}).get("status") not in (None, "Pass")]
    return ok(not worse, f"compared with {json.loads(p.read_text())['run']['describe']}: cases that passed before and do not now: {worse or 'none'}")


# ================================================================= runner
SMOKE = ["API-01", "API-02", "SCO-01", "SYS-01"]
ORDER = SMOKE + [k for k in PLAN if k not in SMOKE and k != "NFR-07"] + ["NFR-07"]


def run_one(cid):
    c = CASES[cid]
    try: status, actual = c["fn"]()
    except Exception as e: status, actual = "Fail", f"error while running: {e!r}"[:400]
    RESULTS[cid] = {"tag": c["tag"], "why": c["why"], "status": status, "actual": actual, "defect": c["defect"]}
    return RESULTS[cid]


def git(*a):
    try: return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except Exception: return ""


def write_results():
    run = {"date": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "describe": git("describe", "--tags", "--always", "--dirty"),
           "commit": git("rev-parse", "HEAD"), "git_user": git("config", "user.name"), "via": via(), "python": platform.python_version(), "platform": platform.platform()}
    OUT.write_text(json.dumps({"run": run, "cases": RESULTS, "samples": SAMPLE_RESULTS, "scenarios": SCENARIO_RESULTS}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def _defects(d): return [x.strip() for x in (d or "").split(",") if x.strip()]


def check_result(cid):
    r = RESULTS[cid]
    if r["status"] in ("Pass", "N/A", "Not run", "Known limitation"): return
    if set(_defects(r["defect"])) & OPEN_DEFECTS: pytest.xfail(f"{cid} fails; {r['defect']} is open: {r['actual'][:200]}")
    pytest.fail(f"{cid} ({r['tag']}): {r['actual']}")


@pytest.fixture(scope="module", autouse=True)
def _write_at_end():
    yield
    write_results()


@pytest.mark.parametrize("cid", ORDER)
def test_case(cid):
    run_one(cid)
    check_result(cid)


def test_every_plan_case_is_ported():
    assert sorted(CASES) == sorted(PLAN), set(PLAN) ^ set(CASES)
    assert all(c["tag"] in ("Ported", "Replaced", "N/A") for c in CASES.values())
    assert all(c["why"] for c in CASES.values() if c["tag"] in ("Replaced", "N/A"))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")       # the Windows console is cp1252; samples hold emoji and Devanagari
    print("Smoke set first:", ", ".join(SMOKE))
    for cid in SMOKE:
        r = run_one(cid); print(f"{r['status']:<17} {cid}  {r['actual'][:150]}")
    if any(RESULTS[c]["status"] != "Pass" for c in SMOKE): print("Smoke set failed: stopping."); write_results(); sys.exit(1)
    for cid in ORDER[len(SMOKE):]:
        r = run_one(cid); print(f"{r['status']:<17} {cid}  [{r['tag']}] {r['actual'][:150]}")
    write_results()
    from collections import Counter
    cnt = Counter(r["status"] for r in RESULTS.values())
    unexpected = [k for k, r in RESULTS.items() if r["status"] == "Fail" and not set(_defects(r["defect"])) & OPEN_DEFECTS]
    print(dict(cnt), "| unexpected failures:", unexpected or "none", "| wrote", OUT.relative_to(ROOT))
    sys.exit(1 if unexpected else 0)
