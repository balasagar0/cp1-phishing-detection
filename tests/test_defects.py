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


if __name__ == "__main__":
    ok = True
    for name, fn in sorted((n, f) for n, f in globals().items() if n.startswith("test_") and callable(f)):
        try: fn(); print("PASS", name)
        except Exception as e: ok = False; print("FAIL", name, "-", repr(e)[:400])
    print("ALL PASSED" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
