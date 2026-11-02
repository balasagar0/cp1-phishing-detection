"""Event store (R2-05): linking, the window edges, recipients never mixing, alerts, retention, restart, privacy, and equality with /correlate.
Run:  python tests/test_event_store.py      or      pytest tests/test_event_store.py
Uses a temporary database and a test HMAC key; nothing is written into the project folder."""
import os, sys, json, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT))
TMP = Path(tempfile.mkdtemp(prefix="cp1_store_"))
os.environ.setdefault("CP1_EVENT_DB", str(TMP / "api_events.db")); os.environ.setdefault("CP1_HMAC_KEY", "test-key-not-secret")
from demo_cases import CASES

_client = None
def client():
    global _client
    if _client is None:
        from fastapi.testclient import TestClient
        import api
        _client = TestClient(api.app)
    return _client


def new_store(name, **kw):
    import api
    from event_store import EventStore
    return EventStore(TMP / f"{name}.db", b"unit-test-key", api.F.model, api.F.window, **kw)


def ev(ch, score, ids, t):
    return {"channel": ch, "assessed": ch in ("email", "sms", "url"), "score": score if ch in ("email", "sms", "url") else None,
            "label": ("malicious" if score >= 0.5 else "benign") if ch in ("email", "sms", "url") else "not assessed", "ids": ids, "t": t, "model_version": "test"}


# ---------- the same answer as /correlate ----------
def test_highest_campaign_risk_equals_correlate_on_tc04_tc06_tc07():
    c = client()
    for cid in ("TC-04", "TC-06", "TC-07"):
        events = CASES[cid]["events"]
        corr = c.post("/correlate", json={"events": events}).json()
        r = c.post("/events", json={"recipient": f"eq-{cid}@example.test", "events": events}); assert r.status_code == 200, r.text[:300]
        j = r.json()
        assert round(j["highest_campaign_risk"], 3) == round(corr["bundle_risk"], 3), (cid, j["highest_campaign_risk"], corr["bundle_risk"])
        assert len(j["campaigns"]) == corr["n_windows"], (cid, j["campaigns"])
    tc07 = c.get("/campaigns", params={"recipient": "eq-TC-07@example.test"}).json()
    scores = sorted(round(e["score"], 3) for e in c.post("/correlate", json={"events": CASES["TC-07"]["events"]}).json()["events"])
    assert len(tc07) == 3 and all(x["n_events"] == 1 for x in tc07) and sorted(round(x["risk"], 3) for x in tc07) == scores, tc07   # three one-event campaigns


# ---------- linking and the window ----------
def test_events_sharing_a_domain_inside_the_window_link_into_one_campaign():
    S = new_store("link")
    S.add("r1", [ev("sms", .42, ["dom:parcel-redelivery.info"], 0), ev("url", .45, ["dom:parcel-redelivery.info"], 7), ev("email", .20, ["dom:parcel-redelivery.info"], 15)])
    cs = S.campaigns("r1"); assert len(cs) == 1 and cs[0]["n_events"] == 3 and len(cs[0]["shared_identity_tokens"]) == 1, cs
    assert cs[0]["shared_identity_tokens"][0].startswith("dom:#") and "parcel" not in json.dumps(cs), cs


def test_window_edges_59_and_61_minutes():
    S = new_store("edges")
    S.add("in", [ev("sms", .3, ["dom:a.top"], 0), ev("url", .3, ["dom:a.top"], 59)])
    S.add("out", [ev("sms", .3, ["dom:a.top"], 0), ev("url", .3, ["dom:a.top"], 61)])
    i, o = S.campaigns("in"), S.campaigns("out")
    assert len(i) == 1 and i[0]["n_events"] == 2, i
    assert len(o) == 2 and all(c["n_events"] == 1 and c["shared_identity_tokens"] == [] for c in o), o


def test_two_recipients_never_mix():
    S = new_store("mix")
    S.add("alice", [ev("sms", .42, ["dom:shared.top"], 0)]); S.add("bob", [ev("url", .45, ["dom:shared.top"], 3)]); S.add("alice", [ev("email", .2, ["dom:shared.top"], 5)])
    a, b = S.campaigns("alice"), S.campaigns("bob")
    assert len(a) == 1 and a[0]["n_events"] == 2 and len(b) == 1 and b[0]["n_events"] == 1, (a, b)
    assert not set(a[0]["event_ids"]) & set(b[0]["event_ids"]) and a[0]["recipient"] != b[0]["recipient"]


# ---------- alerts ----------
def test_one_alert_when_a_campaign_first_reaches_the_line_with_its_reason():
    c = client(); who = "alert-once@example.test"; weak = CASES["TC-06"]["events"]
    first = c.post("/events", json={"recipient": who, "events": weak[:1]}).json()
    assert first["new_alerts"] == [], first["new_alerts"]                          # one weak SMS stays below the line
    rest = c.post("/events", json={"recipient": who, "events": weak[1:]}).json()
    assert len(rest["new_alerts"]) == 1 and rest["highest_campaign_risk"] >= 0.5, rest
    a = rest["new_alerts"][0]
    assert a["shared_identity_tokens"] == ["dom:parcel-redelivery.info"] and len(a["event_ids"]) == 3 and "reached the alert line" in a["reason"], a
    again = c.post("/events", json={"recipient": who, "events": [dict(weak[0], time="16")]}).json()
    assert again["new_alerts"] == [], again["new_alerts"]                          # the same campaign does not alert twice
    al = c.get("/alerts", params={"recipient": who}).json(); assert len(al) == 1, al
    assert c.post(f"/alerts/{al[0]['id']}/ack").status_code == 200 and c.get("/alerts", params={"recipient": who}).json() == []
    assert c.post("/alerts/999999/ack").status_code == 404 and c.get("/campaigns/999999").status_code == 404


def test_calls_and_video_are_stored_and_shown_but_never_change_the_score():
    c = client(); who = "call-timeline@example.test"; weak = CASES["TC-06"]["events"]
    before = c.post("/events", json={"recipient": who, "events": weak}).json()["highest_campaign_risk"]
    j = c.post("/events", json={"recipient": who, "events": [{"channel": "call", "text": "Caller asked me to confirm my address for the parcel at parcel-redelivery.info", "time": "9"},
                                                             {"channel": "video", "text": "video message", "time": "10"}]}).json()
    assert j["status"] == "CANNOT_ASSESS" and j["highest_campaign_risk"] == before and j["new_alerts"] == [], j
    camp = c.get(f"/campaigns/{j['campaigns'][0]['id']}").json()
    calls = [e for e in camp["timeline"] if e["channel"] in ("call", "video")]
    assert len(calls) == 2 and all(e["assessed"] is False and e["score"] is None and not e["in_campaign"] for e in calls), camp["timeline"]


def test_nothing_assessable_stores_events_but_makes_no_campaign():
    j = client().post("/events", json={"recipient": "only-calls@example.test", "events": [{"channel": "call", "text": "hello", "time": "0"}]}).json()
    assert j["status"] == "CANNOT_ASSESS" and j["campaigns"] == [] and j["highest_campaign_risk"] is None and j["events"][0]["event_id"], j


def test_bad_input_is_refused():
    c = client()
    assert c.post("/events", json={"recipient": "", "events": [{"channel": "sms", "text": "hi"}]}).status_code == 422
    assert c.post("/events", json={"recipient": "x", "events": []}).status_code == 422
    assert c.post("/events", json={"recipient": "x", "events": [{"channel": "url", "text": "htp:/bad url"}]}).status_code == 422


# ---------- retention and restart ----------
def test_purge_deletes_old_events_and_their_campaigns():
    S = new_store("purge"); now = 1_800_000_000.0; old = now - 40 * 86400
    S.add("p", [ev("sms", .9, ["dom:old.top"], 0)], now=old); S.add("p", [ev("sms", .9, ["dom:new.top"], 5000)], now=now)
    assert len(S.campaigns("p")) == 2 and len(S.alerts("p")) == 2
    r = S.purge(30, now=now)
    assert r["events_deleted"] == 1 and len(S.campaigns("p")) == 1 and len(S.alerts("p")) == 1, (r, S.campaigns("p"))
    assert S.db.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 1
    assert client().post("/purge", json={"older_than_days": 3650}).status_code == 200


def test_data_survives_a_restart():
    S = new_store("restart"); S.add("r", [ev("sms", .42, ["dom:x.top"], 0), ev("url", .45, ["dom:x.top"], 7), ev("email", .2, ["dom:x.top"], 15)])
    before = (S.campaigns("r"), S.alerts("r")); S.close()
    T = new_store("restart"); assert (T.campaigns("r"), T.alerts("r")) == before and before[0], before


# ---------- privacy ----------
def test_recipient_tokens_and_text_are_not_stored_in_clear():
    S = new_store("privacy", store_content=False)
    S.add("victim@example.test", [{**ev("sms", .9, ["dom:secret-domain.top", "tel:9876543210"], 0), "text": "Your OTP-like secret message body", "subject": "subj"}])
    S.close(); raw = (TMP / "privacy.db").read_bytes()
    for clear in (b"victim@example.test", b"secret-domain", b"9876543210", b"secret message body"): assert clear not in raw, clear
    K = new_store("keep", store_content=True); K.add("v", [{**ev("sms", .9, [], 0), "text": "kept on purpose", "subject": "s"}])
    camp = K.campaign(K.campaigns("v")[0]["id"]); assert camp["timeline"][0]["text"] == "kept on purpose"


def test_key_file_is_created_once_and_reused():
    from event_store import load_key
    saved = os.environ.pop("CP1_HMAC_KEY", None)
    try:
        p = TMP / "k" / ".cp1_hmac_key"; p.parent.mkdir()
        k1 = load_key(p); k2 = load_key(p)
        assert k1 == k2 and len(k1) == 64 and p.exists()
    finally:
        if saved is not None: os.environ["CP1_HMAC_KEY"] = saved


if __name__ == "__main__":
    ok = True
    for name, fn in sorted((n, f) for n, f in globals().items() if n.startswith("test_") and callable(f)):
        try: fn(); print("PASS", name)
        except Exception as e: ok = False; print("FAIL", name, "-", repr(e)[:400])
    print("ALL PASSED" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
