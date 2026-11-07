"""Rebuilds every Phase 5 document from the build cp1-final, in order (about 5 minutes; pytest runs once inside the first step).
  python scripts/make_documents.py [--reuse-tests]        (needs: pip install -r requirements-docs.txt)
  1. scripts/make_final_numbers.py   -> reports/FINAL_NUMBERS.md, reports/final_numbers.json, reports/test_run.json
  2. scripts/make_final_test_report.py -> reports/FINAL_TEST_REPORT.md
  3. scripts/make_figures.py         -> reports/figures/
  4. scripts/render_docs.py          -> docs/*.md and docs/report/ from docs/templates/
  5. scripts/make_diary_entries.py   -> docs/DIARY_ENTRIES.md
  6. pytest tests/test_documents.py  -> the documents are current and carry no typed or retired number
Stops at the first failed step."""
import subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def main():
    reuse = ["--reuse-tests"] if "--reuse-tests" in sys.argv else []
    steps = [["scripts/make_final_numbers.py", *reuse], ["scripts/make_final_test_report.py"], ["scripts/make_figures.py"], ["scripts/render_docs.py"],
             ["scripts/make_diary_entries.py"], ["-m", "pytest", "tests/test_documents.py", "-q", "-p", "no:cacheprovider"]]
    for s in steps:
        print(">>", " ".join(s), flush=True)
        r = subprocess.run([sys.executable, *s], cwd=ROOT)
        if r.returncode: print("FAILED:", " ".join(s)); return r.returncode
    print("all documents rebuilt from cp1-final"); return 0


if __name__ == "__main__":
    sys.exit(main())
