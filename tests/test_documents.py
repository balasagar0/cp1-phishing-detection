"""The documents written from cp1-final (Phase 5): numbers flow from code to documents, never back (rule 1).
Checks that reports/final_numbers.json comes from the tag, that every template renders and every rendered document is current, that no template
holds a typed metric, that no retired number appears in a document written in this work, and that every document with correlation numbers
says they are simulated (rule 4). Needs only the committed reports and templates.
Run:  pytest tests/test_documents.py"""
import json, re, subprocess, sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "scripts"))
import render_docs as RD
from make_final_numbers import RETIRED

FN = ROOT / "reports" / "final_numbers.json"
TEMPLATES = sorted((ROOT / "docs" / "templates").rglob("*.md"))
GENERATED = ["reports/FINAL_TEST_REPORT.md", "reports/figures/README.md", "docs/DIARY_ENTRIES.md"]
HAND_WRITTEN = ["README.md", "docs/USER_MANUAL.md", "docs/PRIVACY.md", "docs/CP2_BACKLOG.md", "PRIVACY_AND_ETHICS.md", "PROJECT_STATUS_AND_ROADMAP.md", "DATA_SOURCES.md"]
TYPED = [re.compile(r"\d+(?:\.\d+)?\s*%"), re.compile(r"(?<![\w.])0\.\d{2,}"), re.compile(r"\b\d+(?:\.\d+)?\s?ms\b"), re.compile(r"\bF1\s*[=:]?\s*\d")]
pytestmark = pytest.mark.skipif(not FN.exists(), reason="reports/final_numbers.json not written yet (scripts/make_final_numbers.py)")


def doc(): return json.loads(FN.read_text(encoding="utf-8"))
def rendered(t): return RD.OUT / t.relative_to(RD.TPL)


def test_final_numbers_come_from_the_tag():
    d = doc()
    assert d["build"]["tag"] == "cp1-final"
    sha = subprocess.run(["git", "rev-parse", "cp1-final^{commit}"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if sha: assert d["build"]["commit"] == sha


def test_every_template_renders_and_every_document_is_current():
    d = doc(); assert TEMPLATES
    for t in TEMPLATES:
        rel = t.relative_to(RD.TPL).as_posix(); text = RD.render(d, t.read_text(encoding="utf-8"), rel)
        assert rendered(t).exists(), f"{rel} has not been rendered: run scripts/render_docs.py"
        assert rendered(t).read_text(encoding="utf-8") == text, f"docs/{rel} is out of date: run scripts/render_docs.py"


def test_templates_hold_no_typed_metric():
    for t in TEMPLATES:
        text = RD.PH.sub(" ", t.read_text(encoding="utf-8"))
        text = re.sub(r"95%\s*(?:CI|confidence|bootstrap|interval)", " ", text)     # the confidence level is a label, not a result
        for rx in TYPED:
            m = rx.search(text)
            assert not m, f"{t.relative_to(ROOT).as_posix()}: '{m.group(0)}' looks typed; use a {{{{key}}}} from final_numbers.json"


def test_no_retired_number_in_the_documents_we_write():
    files = [rendered(t) for t in TEMPLATES] + [ROOT / f for f in GENERATED + HAND_WRITTEN]
    for f in files:
        if not f.exists(): continue
        text = f.read_text(encoding="utf-8")
        for name, rx in RETIRED:
            m = re.search(rx, text)
            assert not m, f"{f.relative_to(ROOT).as_posix()}: retired number {name} ('{m.group(0)}')"


def test_correlation_numbers_are_called_simulated():
    for t in TEMPLATES:
        raw = t.read_text(encoding="utf-8")
        if re.search(r"\{\{\s*(?:corr\.(?:single|parallel|whole|engine|nowindow|hard|auc|fit60)|sim\.|finalrun\.sim)|block:corr", raw):
            assert "simulated" in rendered(t).read_text(encoding="utf-8").lower(), f"{t.name} shows correlation numbers without saying simulated"
