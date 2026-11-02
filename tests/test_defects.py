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


if __name__ == "__main__":
    ok = True
    for name, fn in sorted((n, f) for n, f in globals().items() if n.startswith("test_") and callable(f)):
        try: fn(); print("PASS", name)
        except Exception as e: ok = False; print("FAIL", name, "-", repr(e)[:400])
    print("ALL PASSED" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
