"""The console is served by the API (one command, one address) and gets its presets from it (R2-04, R3-13).
Run:  python tests/test_console_api.py      or      pytest tests/test_console_api.py"""
import os, sys, re, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT))
os.environ.setdefault("CP1_EVENT_DB", str(Path(tempfile.mkdtemp(prefix="cp1_console_")) / "events.db")); os.environ.setdefault("CP1_HMAC_KEY", "test-key-not-secret")

_client = None
def client():
    global _client
    if _client is None:
        from fastapi.testclient import TestClient
        import api
        _client = TestClient(api.app)
    return _client


def test_built_console_is_served_at_the_root():
    r = client().get("/")
    assert r.status_code == 200 and '<div id="root">' in r.text and "/assets/" in r.text, r.text[:200]
    js = re.search(r'src="(/assets/[^"]+\.js)"', r.text).group(1)
    a = client().get(js); assert a.status_code == 200 and "javascript" in a.headers["content-type"], a.headers


def test_one_file_console_is_served_at_lite():
    r = client().get("/lite"); assert r.status_code == 200 and "location.origin" in r.text


def test_api_routes_still_win_over_the_console():
    c = client()
    assert c.get("/health").json()["status"] in ("ok", "degraded") and c.post("/score", json={"channel": "sms", "text": "hi"}).status_code == 200


def test_docs_pages_are_off_because_they_load_a_cdn():
    c = client(); assert c.get("/docs").status_code == 404 and c.get("/redoc").status_code == 404 and c.get("/openapi.json").status_code == 200


def test_presets_are_the_demo_cases_and_the_indian_stories_all_hand_written():
    p = client().get("/presets").json()
    assert [x["id"] for x in p] == [f"TC-0{i}" for i in range(1, 9)] + ["IN-01", "IN-02", "IN-03", "IN-04"], [x["id"] for x in p]
    assert all(x["label"] == "hand-written, not a test set" and x["events"] for x in p)


if __name__ == "__main__":
    ok = True
    for name, fn in sorted((n, f) for n, f in globals().items() if n.startswith("test_") and callable(f)):
        try: fn(); print("PASS", name)
        except Exception as e: ok = False; print("FAIL", name, "-", repr(e)[:400])
    print("ALL PASSED" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
