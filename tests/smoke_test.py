"""Smoke tests for the Review-2 pipeline. Run:  python tests/smoke_test.py   (needs run_all.sh outputs and the synthetic generator)."""
import sys, subprocess, shutil, tempfile, json, csv
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import pandas as pd
from testcases import read_table, validate, COLS
T = Path(tempfile.mkdtemp()); ok = True
def check(name, cond, detail=""):
    global ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))

# 1. workbook: example rows ignored by default, parsed with --allow-examples; progress formulas count correctly
wb = ROOT / "testcases" / "review2_testcase_workbook.xlsx"
df, iss = validate(read_table(wb)); check("workbook: example rows ignored by default", df.empty and any("example" in m for _, _, m in iss))
df, iss = validate(read_table(wb), True); check("workbook: examples parse without errors", len(df) == 5 and not any(l == "error" for l, _, _ in iss), iss)
check("workbook: call rows get a 'not scored' warning", any("call event" in m for _, _, m in iss))
check("loader: defanged URLs are restored", df.content.str.contains("http://kyc-update-bank.top/verify").any())
from openpyxl import load_workbook
w = load_workbook(wb); ev = w["Events"]
for r, row in enumerate([["T1", "T1-1", "sms", "2026-11-03T10:00:00+05:30", "", "", "x", "malicious", "C1", "lab_simulation"], ["T1", "T1-2", "url", "2026-11-03T10:03:00+05:30", "", "", "a.top/x", "malicious", "C1", "lab_simulation"],
                         ["T2", "T2-1", "email", "2026-11-03T12:00:00+05:30", "", "s", "hello", "benign", "", "lab_simulation"]], 7):
    for c, v in enumerate(row, 1): ev.cell(r, c, v)
w.save(T / "wb.xlsx"); RECALC = Path("/mnt/skills/public/xlsx/scripts/recalc.py")     # the formulas need a spreadsheet program to calculate; this helper exists only in some environments
if RECALC.exists():
    subprocess.run([sys.executable, str(RECALC), str(T / "wb.xlsx"), "60"], capture_output=True, text=True)
    p = load_workbook(T / "wb.xlsx", data_only=True)["Progress"]
    check("progress sheet counts real rows only", (p["B3"].value, p["B4"].value, p["B8"].value, p["B9"].value, p["C7"].value) == (2, 3, 1, 1, 1), [p[k].value for k in ("B3", "B4", "B8", "B9", "C7")])
else: print("SKIP progress sheet check (needs a spreadsheet program to recalculate the formulas; open the workbook in Excel to see them work)")

# 2. validator catches planted mistakes
bad = [["B1", "E1", "fax", "2026-11-03T10:00:00+05:30", "", "", "hi", "malicious", "C1", "lab_simulation", "", "", ""], ["B1", "E1", "sms", "not a date", "", "", "", "benign", "", "lab_simulation", "", "", ""],
       ["B2", "E3", "sms", "2026-11-03T10:00:00+05:30", "", "", "hi", "malicious", "", "collected_real", "", "", "2"]]
with open(T / "bad.csv", "w", newline="") as f: cw = csv.writer(f); cw.writerow(COLS); cw.writerows(bad)
_, iss = validate(read_table(T / "bad.csv")); msgs = " | ".join(m for l, _, m in iss if l == "error")
for needle in ("is not one of", "'content' is empty", "cannot be read as a date-time", "needs a campaign_id", "need 'basis'", "duplicate event_id", "between 0 and 1"):
    check(f"validator flags: {needle}", needle in msgs)

# 3. end-to-end on synthetic bundles (all rows are source_type=example, so --allow-examples is needed)
for n in (40, 260): subprocess.run([sys.executable, str(ROOT / "tests" / "make_synthetic_testcases.py"), str(n), str(T / f"s{n}.csv")], check=True, capture_output=True)
M = T / "models"; M.mkdir(); shutil.copy(ROOT / "models" / "fusion_model.joblib", M)
run = lambda *a: subprocess.run([sys.executable, str(ROOT / "src" / "refit_fusion.py"), *a, "--allow-examples", "--models-dir", str(M), "--reports-dir", str(T / "rep")], capture_output=True, text=True)
r = run(str(T / "s40.csv")); check("small file: evaluates but refuses to refit", "Not refit" in r.stdout and "Single-channel" in r.stdout, r.stdout[-300:] + r.stderr[-300:])
r = run(str(T / "s260.csv"), "--model", "lr"); check("--model lr refuses with too few bundles per class", "Not refit" in r.stdout, r.stdout[-300:] + r.stderr[-300:])
r = run(str(T / "s260.csv"), "--save"); check("260 bundles: cross-validated refit and save", "Saved" in r.stdout and (M / "fusion_model_real.joblib").exists() and "No suggestion yet" in r.stdout, r.stdout[-400:] + r.stderr[-400:])
check("hypothesis tests H1-H3 are reported", all(h in r.stdout for h in ("H1:", "H2:", "H3:")), r.stdout[-500:])
check("evaluation states the time window", "time window: 60 minutes" in r.stdout, r.stdout[:300])
r2 = run(str(T / "s260.csv"), "--no-window"); check("--no-window is accepted and reported", "time window: none" in r2.stdout, r2.stdout[:300] + r2.stderr[-300:])
r3 = run(str(T / "s260.csv"), "--window", "10"); check("--window N is accepted and reported", "time window: 10 minutes" in r3.stdout, r3.stdout[:300] + r3.stderr[-300:])
print(r.stdout[r.stdout.find("## Hypothesis"):][:900])

# 3b. time-window suggestion works once timing is flagged as real (re-labelled in memory only)
from testcases import build_bundles, suggest_window
from predict import Detectors
bs = build_bundles(validate(read_table(T / "s260.csv"), True)[0], Detectors())
for b in bs: b["sources"] = ["lab_simulation"]
w_ = suggest_window(bs); check("window suggestion: rounded up to 5 minutes, CI brackets the estimate", w_["window_minutes"] % 5 == 0 and w_["p90_ci95"][0] <= w_["p90"] <= w_["p90_ci95"][1] and w_["window_minutes"] >= w_["p90"], w_)
check("window suggestion refuses with too few coordinated bundles", suggest_window(bs[:30])["window_minutes"] is None)

# 4. the saved model loads, scores a bundle, and the API serves it
from fusion import Fusion
F = Fusion(M / "fusion_model_real.joblib"); out = F.risk([{"channel": "sms", "score": .9, "ids": ["dom:a.top"], "t": 0.0}, {"channel": "url", "score": .8, "ids": ["dom:a.top"], "t": 5.0}])
check("saved model scores a bundle", 0 <= out["risk"] <= 1 and F.trained_on.startswith("260 real"), F.trained_on)
check("saved model keeps the evaluation window", F.window == 60.0, F.window)
A = T / "app"; shutil.copytree(ROOT / "src", A / "src"); shutil.copy(ROOT / "api.py", A); shutil.copytree(ROOT / "models", A / "models"); shutil.copy(M / "fusion_model_real.joblib", A / "models")
code = "import sys; sys.path.insert(0,'.'); from fastapi.testclient import TestClient; import api; print(TestClient(api.app).get('/health').json()['fusion_trained_on'])"
r = subprocess.run([sys.executable, "-c", code], cwd=A, capture_output=True, text=True); check("API picks up the refit model", "real test-case bundles" in r.stdout, r.stdout + r.stderr[-300:])
run(str(T / "s260.csv"), "--save", "--window", "30"); check("a refit stores the chosen window and the model uses it", Fusion(M / "fusion_model_real.joblib").window == 30.0)
print("ALL PASSED" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
