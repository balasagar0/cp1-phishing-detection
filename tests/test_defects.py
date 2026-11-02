"""Regression tests named after the defects in the test plan's Defect Log (D-01 to D-12) and the ones found on v2 (D-13 onwards).
Each fix has a test here; a defect closes only after its failing case passes. Needs only the shipped models.
Run:  python tests/test_defects.py      or      pytest tests/test_defects.py"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT))

_client = None
def client():
    global _client
    if _client is None:
        from fastapi.testclient import TestClient
        import api
        _client = TestClient(api.app)
    return _client


# ---------- email-sms: D-11, D-15 (R2-08) ----------
def test_D11_html_and_scripts_are_stripped():
    from common import clean_text
    assert clean_text("<html><body><p>Verify <b>now</b></p><script>track()</script></body></html>") == "Verify now"
    assert clean_text("<style>p{color:red}</style><p>Hello</p>") == "Hello"
    assert clean_text("<HEAD><TITLE>t</TITLE></HEAD><BODY>Body text</BODY>") == "Body text"


def test_D11_link_targets_are_kept_as_urls():
    from common import clean_text
    assert clean_text('<a href="http://evil.top/x">Click here</a> to verify') == "http://evil.top/x Click here to verify"
    assert clean_text("<a class='btn' href='https://bank.example/login' target=_blank>Log in</a>") == "https://bank.example/login Log in"


def test_D11_text_that_only_looks_like_a_tag_is_kept():
    from common import clean_text
    assert clean_text("a < b and c > d") == "a < b and c > d"


def test_D15_non_text_input_gives_an_empty_string():
    from common import clean_text
    assert [clean_text(None), clean_text(123), clean_text(float("nan")), clean_text(["x"])] == ["", "", "", ""]


# ---------- url: D-02 (R2-06), the URL shape check ----------
def test_D02_malformed_urls_are_recognised():
    from url_features import check_url
    for bad in ("htp:/bad url", "", "   ", "http://[::1", "<script>alert(1)</script>", "../../etc/passwd", "javascript:alert(1)", "mailto:a@b.com",
                "hxxp://evil[.]com", "http://999.1.1.1/a", "nodot", "http://example.123/x"):
        assert check_url(bad), bad


def test_D02_real_url_shapes_are_accepted():
    import json
    from url_features import check_url
    from demo_cases import CASES
    good = ["bit.ly/xyz", "localhost:8000/x", "http://0xC0000201/verify", "http://192.0.2.45/login", "http://www.google.com@203.0.113.9/login",
            "https://münchen.de/x", "http://[2001:db8::1]/a", "xn--pypal-4ve.example/signin", "a.b.co.in:8080/path?q=1#f"]
    good += [r["URL"] for r in json.loads((ROOT / "tests" / "data" / "workbook_cases.json").read_text(encoding="utf-8"))["url"]]
    good += [e["text"] for c in CASES.values() for e in c["events"] if e["channel"] == "url"]
    assert [u for u in good if check_url(u)] == []


# ---------- correlation: D-03, D-13 (R2-07); D-04, D-05, D-08 stay fixed ----------
KYC_EMAIL = dict(channel="email", text="Dear customer, your bank account has been suspended. Verify your password within 24 hours at http://sbi-kyc-update.top/verify-now.php or your account will be closed.",
                 subject="Urgent: account suspended", time="0")


def test_D03_nothing_assessable_is_cannot_assess_not_safe():
    for ch in ("call", "voice", "video"):
        r = client().post("/correlate", json={"events": [dict(channel=ch, text="Please verify your account now", time="0")]}); j = r.json()
        assert r.status_code == 200 and j["status"] == "CANNOT_ASSESS" and j["bundle_risk"] is None and j["single_channel_alert"] is None, (ch, j)
        assert j["bundle_label"] == "cannot assess" and j["not_assessed"][0]["channel"] == ch, j
    assert client().post("/correlate", json={"events": []}).status_code == 422 and client().post("/correlate", json={}).status_code == 422


def test_D13_a_call_or_video_does_not_block_or_change_the_bundle():
    alone = client().post("/correlate", json={"events": [KYC_EMAIL]}).json()
    for ch in ("call", "video"):
        r = client().post("/correlate", json={"events": [KYC_EMAIL, dict(channel=ch, text="Verify your account at sbi-kyc-update.top now", time="2")]}); j = r.json()
        assert r.status_code == 200 and j["status"] == "ASSESSED", (ch, r.status_code, r.text[:200])
        assert j["bundle_risk"] == alone["bundle_risk"] and j["features"] == alone["features"], (ch, j["bundle_risk"], alone["bundle_risk"])
        assert j["events"][1]["assessed"] is False and j["events"][1]["score"] is None and not j["events"][1]["in_window"], j["events"][1]
        assert j["shared_identity_tokens"] == [] and j["window_event_indices"] == [0], j        # the call names the same domain, but is not linked


def test_D13_window_indices_point_at_the_request_events():
    ev = [dict(channel="video", text="hello", time="0"), KYC_EMAIL | {"time": "1"}, dict(channel="url", text="http://sbi-kyc-update.top/verify-now.php", time="3")]
    j = client().post("/correlate", json={"events": ev}).json()
    assert j["window_event_indices"] == [1, 2] and [e["in_window"] for e in j["events"]] == [False, True, True], j


def test_D04_events_days_apart_are_not_combined():
    ev = [KYC_EMAIL | {"time": "0"}, dict(channel="url", text="http://sbi-kyc-update.top/verify-now.php", time="4320")]
    j = client().post("/correlate", json={"events": ev}).json()
    assert j["n_windows"] == 2 and j["shared_identity_tokens"] == [] and j["window_minutes"] == 60.0, j


def test_D05_any_public_suffix_links_events():
    from predict import extract_ids
    assert extract_ids("sms", "Verify at secure-bank-verify.online/login") == ["dom:secure-bank-verify.online"]
    assert extract_ids("sms", "see login.secure-bank.co.in") == ["dom:secure-bank.co.in"]


def test_D08_ordinary_words_are_not_identities():
    from predict import extract_ids
    assert extract_ids("email", "Urgent request: please verify the attached form today.") == [] and extract_ids("sms", "Urgent request. Verify today.") == []


# ---------- api-console: D-02 (R2-06), D-06 (R2-04), D-07 stays fixed, D-14 ----------
def test_D02_api_refuses_malformed_urls_and_unknown_channels():
    c = client()
    for body in ({"channel": "url", "text": "htp:/bad url"}, {"channel": "url", "text": "http://[::1"}, {"channel": "fax", "text": "hi"}, {"channel": "email", "text": ""}, {"channel": "sms"}):
        r = c.post("/score", json=body); assert r.status_code == 422, (body, r.status_code, r.text[:160])
    r = c.post("/score", json={"channel": "url", "text": "htp:/bad url"}); assert "not a valid URL" in r.json()["detail"], r.text
    r = c.post("/correlate", json={"events": [{"channel": "sms", "text": "hi"}, {"channel": "url", "text": "../../etc/passwd"}]})
    assert r.status_code == 422 and r.json()["detail"].startswith("event 1:"), r.text
    assert c.post("/score", json={"channel": "url", "text": "http://0xC0000201/verify/account"}).status_code == 200      # odd but real URL shapes still score


def test_D06_cors_names_explicit_origins_never_star():
    import api
    assert "*" not in api.ORIGINS and "http://localhost:5173" in api.ORIGINS
    c = client(); o = "http://localhost:5173"
    p = c.options("/correlate", headers={"Origin": o, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"})
    assert p.status_code == 200 and p.headers.get("access-control-allow-origin") == o, dict(p.headers)
    assert c.get("/health", headers={"Origin": "http://evil.example"}).headers.get("access-control-allow-origin") is None


def test_D07_bad_timestamps_give_422_not_500():
    r = client().post("/correlate", json={"events": [{"channel": "sms", "text": "hi", "time": "a"}, {"channel": "sms", "text": "ok", "time": "b"}]})
    assert r.status_code == 422 and "'time'" in r.json()["detail"], r.text


def test_D14_a_missing_model_degrades_one_channel_only():
    import shutil, tempfile
    from predict import Detectors
    tmp = Path(tempfile.mkdtemp(prefix="cp1_d14_"))
    try:
        for f in ("email_model.joblib", "url_string_model.joblib"): shutil.copy(ROOT / "models" / f, tmp / f)
        D = Detectors(tmp)
        assert D.unavailable.keys() == {"sms"} and D.available("email") and D.available("url") and not D.available("sms"), D.unavailable
        assert D.score("url", "http://sbi-kyc-update.top/verify-now.php")["score"] > 0.5
        try: D.score("sms", "hi"); raise AssertionError("sms should be unavailable")
        except RuntimeError as e: assert "not loaded" in str(e)
    finally: shutil.rmtree(tmp, ignore_errors=True)
    import api
    saved = (api.D.sms, dict(api.D.unavailable))
    try:
        api.D.unavailable["sms"] = "sms_model.joblib could not be loaded (test)"
        c = client()
        assert c.get("/health").json()["status"] == "degraded" and c.post("/score", json={"channel": "sms", "text": "hi"}).status_code == 503
        j = c.post("/correlate", json={"events": [{"channel": "sms", "text": "Verify now at secure-bank-verify.xyz/login", "time": "0"},
                                                   {"channel": "url", "text": "secure-bank-verify.xyz/login", "time": "1"}]}).json()
        assert j["status"] == "ASSESSED" and j["events"][0]["assessed"] is False and "not loaded" in j["events"][0]["reason"] and j["events"][1]["score"] is not None, j
    finally: api.D.sms, api.D.unavailable = saved[0], saved[1]


if __name__ == "__main__":
    ok = True
    for name, fn in sorted((n, f) for n, f in globals().items() if n.startswith("test_") and callable(f)):
        try: fn(); print("PASS", name)
        except Exception as e: ok = False; print("FAIL", name, "-", repr(e)[:400])
    print("ALL PASSED" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
