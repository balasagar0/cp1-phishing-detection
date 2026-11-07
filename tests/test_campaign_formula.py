"""The patent's noisy-OR campaign score (src/campaign_formula.py), an evaluated alternative that is not wired into the API.
Run:  python tests/test_campaign_formula.py      or      pytest tests/test_campaign_formula.py"""
import math, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import pytest
import campaign_formula as CF


def test_noisy_or_basic_arithmetic():
    assert CF.noisy_or([], [], [], 0.0) == 0.0
    assert math.isclose(CF.noisy_or([0.5], [1.0], [0], 0.0), 0.5)
    assert math.isclose(CF.noisy_or([0.5, 0.5], [1.0, 1.0], [0, 0], 0.0), 0.75)                  # 1 - 0.5 * 0.5
    assert math.isclose(CF.noisy_or([0.5], [1.0], [10], 0.1), 0.5 * math.exp(-1.0))              # time decay
    assert CF.noisy_or([0.9, 0.9], [1.0, 1.0], [0, 0], 0.0, factor=2.0) == 1.0                    # capped at 1


def test_more_evidence_never_lowers_the_score():
    a = CF.noisy_or([0.4], [1.0], [0], 0.01); b = CF.noisy_or([0.4, 0.2], [1.0, 1.0], [0, 5], 0.01)
    assert b >= a


def test_the_formula_is_not_wired_into_the_api():
    src = (ROOT / "api.py").read_text(encoding="utf-8") + (ROOT / "src" / "fusion.py").read_text(encoding="utf-8") + (ROOT / "src" / "event_store.py").read_text(encoding="utf-8")
    assert "campaign_formula" not in src


@pytest.mark.skipif(not CF.PARAMETERS_FROM_SPEC, reason="needs the patent specification (docs/inputs/): section 16's worked example inputs, weights and factors")
def test_patent_worked_example_section_16():
    raise AssertionError("fill in from the specification: S about 0.35, then 0.60, then 0.77, and 0.84 after the sequence factor")


if __name__ == "__main__":
    ok = True
    for name, fn in sorted((n, f) for n, f in globals().items() if n.startswith("test_") and callable(f)):
        if name == "test_patent_worked_example_section_16" and not CF.PARAMETERS_FROM_SPEC: print("SKIP", name, "- needs the patent specification"); continue
        try: fn(); print("PASS", name)
        except Exception as e: ok = False; print("FAIL", name, "-", repr(e)[:400])
    print("ALL PASSED" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
