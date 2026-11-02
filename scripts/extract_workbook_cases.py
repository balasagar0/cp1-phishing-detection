"""Copies the hand-written samples, scenarios, test cases and defect log out of the team's test-plan workbook into
tests/data/workbook_cases.json, so tests/test_final_cases.py runs from a fresh clone (docs/inputs/ is gitignored).
  python scripts/extract_workbook_cases.py [path/to/Test_Cases_and_Test_Data.xlsx]
The workbook is read only. Its contents are evaluation material: HAND-WRITTEN, NOT A TEST SET, never used for training.
Only the inputs and expectations are copied; the old run's actual results stay in the workbook."""
import json, sys
from pathlib import Path
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "docs" / "inputs" / "cp1_inputs" / "Test_Cases_and_Test_Data.xlsx"
OUT = ROOT / "tests" / "data" / "workbook_cases.json"


def rows(ws):
    it = ws.iter_rows(values_only=True); head = [str(h).strip() if h is not None else "" for h in next(it)]
    for r in it:
        if r and r[0] not in (None, ""): yield dict(zip(head, ["" if v is None else v for v in r]))


def main(path):
    wb = load_workbook(path)        # formulas kept as text; nothing is written back
    keep = lambda d, ks: {k: (str(d[k]).strip() if not isinstance(d[k], (int, float)) else d[k]) for k in ks}
    doc = {"source": Path(path).name,
           "note": "Copied by scripts/extract_workbook_cases.py. Hand-written evaluation material: not a test set, never train on it.",
           "email": [keep(r, ["ID", "Group", "Category", "Subject", "Body", "Expected label"]) for r in rows(wb["Data-Email"])],
           "sms": [keep(r, ["ID", "Group", "Category", "Message", "Expected label"]) for r in rows(wb["Data-SMS"])],
           "url": [keep(r, ["ID", "Group", "Category", "URL", "Expected label"]) for r in rows(wb["Data-URL"])],
           "scenarios": [keep(r, ["Scenario", "Name", "Purpose", "Case sent to /analyze", "Channels", "Expected outcome"]) for r in rows(wb["Scenarios"]) if str(r["Scenario"]).startswith("S-")],
           "test_cases": [keep(r, ["TC ID", "Module", "Level", "Req ID", "Test scenario", "Preconditions / notes", "Input / steps", "Expected result", "Data ref", "Priority", "Category"]) for r in rows(wb["Test Cases"])],
           "defects": [keep(r, ["Defect ID", "Test case(s)", "Module", "Description", "Steps to reproduce", "Severity"]) for r in rows(wb["Defect Log"]) if str(r["Defect ID"]).startswith("D-")]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(doc['email'])} email, {len(doc['sms'])} SMS, {len(doc['url'])} URL samples, "
          f"{len(doc['scenarios'])} scenarios, {len(doc['test_cases'])} test cases, {len(doc['defects'])} defects")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT)
