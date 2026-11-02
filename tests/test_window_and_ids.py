"""Tests for the time window, the single-event rule, the identity tokens and the input checks of /correlate.
Run:  python tests/test_window_and_ids.py     (or:  pytest tests/test_window_and_ids.py)
Needs the trained models in models/ (they ship with the project). No data download is needed."""
import sys, copy
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT))
from predict import extract_ids
from fusion import time_windows, bundle_features, FEATURE_NAMES, T_MAX

# ---------- example bundles (the same three as the console presets, plus a courier pair) ----------
KYC = [dict(channel="sms", text="Dear customer, your SBI account will be blocked today. Update your KYC now at http://sbi-kyc-update.top/verify-now.php or call 9876543210", identity="+91 98765 43210", time="0"),
       dict(channel="url", text="http://sbi-kyc-update.top/verify-now.php", time="4"),
       dict(channel="email", text="Dear customer, your bank account has been suspended. Verify your password within 24 hours at http://sbi-kyc-update.top/verify-now.php or your account will be closed.", subject="Urgent: account suspended", time="12")]
BENIGN = [dict(channel="sms", text="Hey, can we move our project meeting to 4 pm tomorrow? I will email you the notes and an article on planning.", identity="+91 90000 11111", time="0"),
          dict(channel="email", text="Thanks for confirming. I wrote up the notes from yesterday. The article I mentioned is at https://en.wikipedia.org/wiki/Project_management if you want to read it. Call me tomorrow if anything changes.", subject="Re: project meeting", time="6"),
          dict(channel="url", text="https://en.wikipedia.org/wiki/Project_management", time="10")]
WEAK = [dict(channel="sms", text="Hello, there is a problem with your delivery address. Update it at parcel-redelivery.info/confirm today", time="0"),
        dict(channel="url", text="http://parcel-redelivery.info/track?id=88213", time="7"),
        dict(channel="email", text="Hello, we could not deliver your parcel today because the address on the label is incomplete. Please confirm your address at http://parcel-redelivery.info/confirm so we can try again. Thank you.", subject="Delivery problem with your parcel", time="15")]
COURIER = [dict(channel="sms", text="Your package will arrive tomorrow between 10 and 2. Track it at https://www.fedex.com/fedextrack/?trknbr=123456789012", identity="FedEx", time="0"),
           dict(channel="email", text="Hi, your FedEx shipment 123456789012 is on its way and will arrive tomorrow. You can follow it at https://www.fedex.com/fedextrack/?trknbr=123456789012. Thanks for shipping with us.", subject="Your shipment is on the way", time="10")]


def retime(ev, times):
    out = copy.deepcopy(ev)
    for e, t in zip(out, times): e["time"] = str(t)
    return out


_client = None
def client():
    global _client
    if _client is None:
        from fastapi.testclient import TestClient
        import api
        _client = TestClient(api.app)
    return _client


def post(events, window=None):
    body = {"events": events}
    if window is not None: body["window_minutes"] = window
    r = client().post("/correlate", json=body)
    assert r.status_code == 200, (r.status_code, r.text[:200])
    return r.json()


# ---------- identity tokens ----------
def test_phone_numbers_are_recognised():
    for text, ident in [("call 9876543210", ""), ("Call +91 98765 43210 now", ""), ("WhatsApp 91 98765 43210", ""), ("(+91) 98765-43210", ""), ("dial 09876543210", ""), ("", "+91 98765 43210"), ("", "98765 43210")]:
        assert extract_ids("sms", text, ident) == ["tel:9876543210"], (text, ident, extract_ids("sms", text, ident))
    assert extract_ids("sms", "+1 (415) 555-2671", "") == ["tel:4155552671"]
    assert extract_ids("sms", "+44 20 7946 0958", "") == ["tel:2079460958"]


def test_numbers_that_are_not_phones():
    for text in ["Your FedEx shipment 123456789012 is on its way", "tracking number 1234567890", "AWB 1234567890", "Order AB1234567890", "Your OTP is 482913",
                 "Account 12345678901234", "Ref no 123456789012", "Meeting on 14 10 2026 10:02", "Logged 2026-10-14 10:02"]:
        assert extract_ids("sms", text, "") == [], (text, extract_ids("sms", text, ""))


def test_links_are_cut_out_before_phone_numbers_are_searched():
    assert extract_ids("sms", "Track it at https://www.fedex.com/fedextrack/?trknbr=123456789012", "") == ["dom:fedex.com"]
    assert extract_ids("url", "http://parcel-redelivery.info/track?id=1234567890", "") == ["dom:parcel-redelivery.info"]


def test_explicit_identity_field():
    assert extract_ids("sms", "", "FedEx") == ["id:fedex"]
    assert extract_ids("sms", "", "56767") == ["id:56767"]          # a short code is a sender id, not a phone number
    assert extract_ids("email", "", "alerts@secure-bank.xyz") == ["dom:secure-bank.xyz"]


def test_domains_use_the_whole_public_suffix_list():
    got = extract_ids("sms", "pay at http://pay-now.shop/x or write help@secure-bank.online or see login.secure-bank.co.in", "")
    assert got == ["dom:pay-now.shop", "dom:secure-bank.co.in", "dom:secure-bank.online"], got


def test_ordinary_words_are_not_identities():
    assert extract_ids("sms", "e.g. tomorrow. Ok. Version 2.5 is out, see file.txt", "") == []


# ---------- time windows ----------
def _groups(times, window):
    return time_windows([{"t": t} for t in times], window)


def test_time_windows_grouping():
    assert _groups([0, 10, 100, 110], 60) == [[0, 1], [2, 3]]
    assert _groups([0, 10, 100, 110], None) == [[0, 1, 2, 3]]
    assert _groups([0, 10, 100, 110], 200) == [[0, 1, 2, 3]]
    assert _groups([0, 60], 60) == [[0, 1]]                  # the edge is inside the window
    assert _groups([0, 60.01], 60) == [[0], [1]]
    assert _groups([100, 0, 10], 60) == [[1, 2], [0]]        # input order does not matter
    assert _groups([0, 50, 100], 60) == [[0, 1], [1, 2]]     # windows may overlap
    assert _groups([5, 5, 5], 1) == [[0, 1, 2]] and _groups([7], 60) == [[0]] and _groups([], 60) == []


def test_span_feature_is_capped():
    ev = [{"channel": "sms", "score": .5, "ids": [], "t": 0.0}, {"channel": "url", "score": .5, "ids": [], "t": 1e6}]
    f = dict(zip(FEATURE_NAMES, bundle_features(ev)))
    assert abs(f["log_time_span_min"] - __import__("math").log1p(T_MAX)) < 1e-9, f["log_time_span_min"]


# ---------- /correlate ----------
def test_health_reports_the_window():
    h = client().get("/health").json()
    assert h["window_minutes"] == 60.0, h


def test_presets_inside_the_window_keep_their_results():
    k = post(KYC); assert k["bundle_risk"] >= 0.99 and k["n_windows"] == 1 and k["shared_identity_tokens"] == ["dom:sbi-kyc-update.top"], k
    b = post(BENIGN); assert b["bundle_risk"] < 0.05 and not b["single_channel_alert"], b
    w = post(WEAK)
    assert not w["single_channel_alert"] and abs(w["bundle_risk"] - 0.595) < 0.01 and w["bundle_risk"] >= 0.5, w     # no event alerts alone; the bundle does
    assert w["bundle_risk"] > w["bundle_risk_without_correlation"], w                                              # link and timing add to the pooled score
    assert w["window_event_indices"] == [0, 1, 2] and w["shared_identity_tokens"] == ["dom:parcel-redelivery.info"], w


def test_events_far_apart_are_not_correlated():
    w = post(retime(WEAK, [0, 4320, 8640]))
    top = max(e["score"] for e in w["events"])
    assert w["n_windows"] == 3 and w["shared_identity_tokens"] == [] and len(w["window_event_indices"]) == 1, w
    assert not w["single_channel_alert"] and w["bundle_risk"] < 0.5 and abs(w["bundle_risk"] - top) < 0.002, w       # no pooling: the bundle is its strongest event
    k = post(retime(KYC, [0, 4320, 8640]))
    assert k["n_windows"] == 3 and k["shared_identity_tokens"] == [] and k["bundle_risk"] >= 0.99, k                 # each event is malicious alone, so it still alerts


def test_window_minutes_parameter():
    spread = retime(WEAK, [0, 90, 180])
    narrow, wide = post(spread), post(spread, 240)
    assert narrow["window_minutes"] == 60.0 and narrow["n_windows"] == 3 and narrow["bundle_risk"] < 0.5, narrow
    assert wide["window_minutes"] == 240.0 and wide["n_windows"] == 1 and wide["shared_identity_tokens"] == ["dom:parcel-redelivery.info"], wide


def test_a_lone_event_is_its_detector_score():
    r = post(WEAK[1:2])
    assert r["n_windows"] == 1 and abs(r["bundle_risk"] - r["events"][0]["score"]) < 0.002, r


def test_courier_tracking_number_is_not_a_phone_number():
    r = post(COURIER)
    assert all(not t.startswith("tel:") for e in r["events"] for t in e["identity_tokens"]), r
    assert r["shared_identity_tokens"] == ["dom:fedex.com"], r


def test_iso_timestamps_are_read():
    r = post([dict(channel="sms", text="hi", time="2026-11-03T10:00:00+05:30"), dict(channel="sms", text="ok", time="2026-11-03T10:10:00+05:30")])
    assert r["time_span_minutes"] == 10.0, r


def test_bad_input_is_rejected():
    c = client()
    ok = dict(channel="sms", text="hi")
    for name, body, code in [("empty text", {"events": [dict(channel="sms", text="")]}, 422), ("time is a word", {"events": [dict(ok, time="tomorrow")]}, 422),
                             ("time is nan", {"events": [dict(ok, time="nan")]}, 422), ("window 0", {"events": [ok], "window_minutes": 0}, 422),
                             ("window negative", {"events": [ok], "window_minutes": -5}, 422), ("window above a week", {"events": [ok], "window_minutes": 99999}, 422),
                             ("no events", {"events": []}, 422), ("voice alone: CANNOT_ASSESS since R2-07 (was 501)", {"events": [dict(channel="voice", text="hi")]}, 200)]:
        r = c.post("/correlate", json=body); assert r.status_code == code, (name, r.status_code, r.text[:120])


def test_cors_preflight():
    r = client().options("/correlate", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
    # since R2-04 (D-06) CORS names the console's dev origin explicitly instead of '*'
    assert r.status_code == 200 and r.headers.get("access-control-allow-origin") == "http://localhost:5173", (r.status_code, dict(r.headers))


if __name__ == "__main__":
    ok = True
    for name, fn in sorted((n, f) for n, f in globals().items() if n.startswith("test_") and callable(f)):
        try: fn(); print("PASS", name)
        except Exception as e: ok = False; print("FAIL", name, "-", repr(e)[:400])
    print("ALL PASSED" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
