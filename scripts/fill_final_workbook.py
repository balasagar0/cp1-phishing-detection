"""Fills the team's test-plan workbook with the latest run of tests/test_final_cases.py.
  python scripts/fill_final_workbook.py [--source docs/inputs/cp1_inputs/Test_Cases_and_Test_Data.xlsx] [--results reports/final_cases_results.json]
Copies the source to reports/Test_Cases_and_Test_Data_FINAL.xlsx (the source is never written) and fills: Actual result, Status, Defect ID,
Executed by and Date in Test Cases; the sample labels and scores; the scenario outcomes; the media rows; the run record; and the Defect Log.
Sheet names, headers and formulas are kept. Defect status comes from the run, never by hand: a defect is Closed only when every linked case
passes, Open when one fails, Retest when one has not run. Also writes reports/defect_status.json and reports/defect_log.md."""
import argparse, json, shutil, subprocess, sys, datetime
from pathlib import Path
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "scripts"))
from machine_info import info as machine, one_line

SRC = ROOT / "docs" / "inputs" / "cp1_inputs" / "Test_Cases_and_Test_Data.xlsx"
OUT = ROOT / "reports" / "Test_Cases_and_Test_Data_FINAL.xlsx"


def git(*a): return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def cols(ws):
    return {str(c.value).strip(): c.column for c in ws[1] if c.value is not None}


def rows_by_id(ws, col=1):
    return {str(ws.cell(r, col).value).strip(): r for r in range(2, ws.max_row + 1) if ws.cell(r, col).value not in (None, "")}


def find_label(ws, text):
    for r in range(1, ws.max_row + 1):
        if str(ws.cell(r, 1).value or "").strip() == text: return r
    raise KeyError(text)


def defect_status(reg, results, run_date):
    out = {}
    for did, d in ((k, v) for k, v in reg.items() if k.startswith("D-")):
        st = {c: results["cases"].get(c, {}).get("status", "Not run") for c in d["cases"]}
        fails = [c for c, s in st.items() if s in ("Fail", "Known limitation")]; pending = [c for c, s in st.items() if s == "Not run"]
        status = "Open" if fails else "Retest" if pending else "Closed"
        commits = []
        for pat in d.get("fix_commits", []): commits += git("log", "--no-merges", "--format=%h", "-E", f"--grep={pat}").split()
        retest = "; ".join(f"{c} {s}" for c, s in st.items())
        out[did] = {"status": status, "cases": st, "retest": f"{results['run']['describe']} on {run_date}: {retest}", "commits": commits,
                    "date_closed": run_date if status == "Closed" else "", "proposal": d.get("proposal", "") if status != "Closed" else ""}
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--source", default=str(SRC)); ap.add_argument("--results", default=str(ROOT / "reports" / "final_cases_results.json"))
    ap.add_argument("--out", default=str(OUT)); a = ap.parse_args()
    res = json.loads(Path(a.results).read_text(encoding="utf-8")); reg = json.loads((ROOT / "docs" / "defect_registry.json").read_text(encoding="utf-8"))
    run = res["run"]; run_date = run["date"][:10]; by = f"automated run, started by {run['git_user']}"
    shutil.copy(a.source, a.out); wb = load_workbook(a.out)

    # ---- Test Cases
    ws = wb["Test Cases"]; c = cols(ws); ids = rows_by_id(ws)
    for cid, r in ids.items():
        x = res["cases"].get(cid)
        if not x: continue
        actual = f"[{x['tag']}] {x['actual']}" if x["tag"] == "Ported" or x["status"] == "N/A" else f"[{x['tag']}] {x['actual']} Port note: {x['why']}"
        ws.cell(r, c["Actual result"], actual); ws.cell(r, c["Status"], x["status"])
        ws.cell(r, c["Defect ID"], x["defect"] or None); ws.cell(r, c["Executed by"], by); ws.cell(r, c["Date"], run_date)
    for dv in ws.data_validations.dataValidation:          # the plan's status list gains N/A (a case whose feature v2 does not have)
        if dv.formula1 and "Known limitation" in dv.formula1 and "N/A" not in dv.formula1: dv.formula1 = dv.formula1[:-1] + ',N/A"'

    # ---- sample sheets: label at the 0.5 line, score = v2 probability x 100
    for sheet, lab, sc in (("Data-Email", "Actual label", "Score"), ("Data-SMS", "Actual label", "Score"), ("Data-URL", "Actual label", "Score")):
        ws = wb[sheet]; c = cols(ws)
        for sid, r in rows_by_id(ws).items():
            s = res["samples"].get(sid)
            if s: ws.cell(r, c[lab], s["predicted"]); ws.cell(r, c[sc], round(100 * s["score"], 1))

    # ---- scenarios and media
    ws = wb["Scenarios"]; c = cols(ws)
    for sid, r in rows_by_id(ws).items():
        if sid in res["scenarios"]: ws.cell(r, c["Actual outcome"], res["scenarios"][sid])
    ws = wb["Media Files"]; c = cols(ws)
    for fid, r in rows_by_id(ws).items():
        ws.cell(r, c["Actual outcome"], "Not built in CP1: no voice or video detector (VOICE_IN_CP1 = no; video is Capstone-2) and no media-file input. See VV-06 to VV-10.")
        ws.cell(r, c["Status"], "N/A")
    for dv in ws.data_validations.dataValidation:
        if dv.formula1 and "Known limitation" in dv.formula1 and "N/A" not in dv.formula1: dv.formula1 = dv.formula1[:-1] + ',N/A"'

    # ---- Defect Log
    ds = defect_status(reg, res, run_date)
    ws = wb["Defect Log"]; c = cols(ws); have = rows_by_id(ws); nxt = ws.max_row + 1
    while nxt > 2 and not ws.cell(nxt - 1, 1).value: nxt -= 1
    for did in sorted(ds, key=lambda k: int(k[2:])):
        d, s = reg[did], ds[did]
        r = have.get(did)
        if r is None:
            r = nxt; nxt += 1
            for k, v in (("Defect ID", did), ("Date found", d["date_found"]), ("Test case(s)", ", ".join(d["cases"])), ("Module", d["module"]),
                         ("Description", d["description"]), ("Steps to reproduce", d["steps"]), ("Severity", d["severity"]), ("Found by", by)):
                ws.cell(r, c[k], v)
        fixed_by = d["fixed_by"] + (f"; commit {', '.join(s['commits'])} (Claude Code session started by {run['git_user']})" if s["commits"] else "")
        ws.cell(r, c["Status"], s["status"]); ws.cell(r, c["Fixed by"], fixed_by)
        ws.cell(r, c["Fix summary"], d["fix_summary"] + (f" {s['proposal']}" if s["proposal"] else ""))
        ws.cell(r, c["Retest result"], s["retest"]); ws.cell(r, c["Date closed"], s["date_closed"] or None)

    # ---- Read Me: run record and the description of the system tested (the old text described the 29 Sep codebase)
    m = machine(); ws = wb["Read Me"]
    import sklearn, fastapi
    ui = (ROOT / "reports" / "ui_checks.json").exists()
    put = lambda label, text: ws.cell(find_label(ws, label), 2, text)
    ws.cell(4, 1, f"Companion document: Test Plan (Word). This FINAL copy holds the automated run of {run['date'][:16].replace('T', ' ')} on {run['describe']}, with the 112 cases ported to the v2 build "
                  "(tests/test_final_cases.py). The 29 September results stay in the original workbook.")
    put("Step 1", "Run: python tests/test_final_cases.py (or pytest tests/test_final_cases.py). It runs the smoke set first and writes reports/final_cases_results.json.")
    put("Step 2", "Run: python scripts/fill_final_workbook.py. It copies the team workbook to reports/Test_Cases_and_Test_Data_FINAL.xlsx and fills the yellow columns, samples, scenarios, run record and Defect Log.")
    put("Step 3", "Console cases come from scripts/ui_checks.py (Playwright), NFR-05 from scripts/nfr05_fresh_clone.py, NFR-07 from the comparison with the earlier run. A person confirms the demo-laptop run below.")
    put("Step 4", "Defect status is worked out from the run: a defect closes only when every linked case passes. Accepting a defect is the team's call; proposals are written as 'Proposed: accept because ...'.")
    put("Automated run", f"{run['date'][:10]}: {one_line(m)}; scikit-learn {sklearn.__version__}, FastAPI {fastapi.__version__}. API called {run['via']}. Scores are v2 probabilities x 100.")
    put("Git commit or tag tested", f"{run['describe']} ({run['commit']})")
    put("Run on the demo laptop (date, CPU, RAM, OS)", f"This run: {run['date'][:10]}, {m['cpu']}, {m['ram_gb']} GB RAM, {m['os']} (host {m['machine']}). Viraj confirms whether this is the demo laptop (R3-06).")
    put("Case", "POST /correlate with a list of events: channel (email, sms, url, call, voice or video), text, optional subject, identity and time (minutes or ISO). POST /score scores one message.")
    put("Score and label", "Each email, SMS or URL gets a probability from 0 to 1 that it is not benign; label malicious at 0.5 or more. SMS uses 1 - P(ham) (spam or smishing). This workbook shows scores x 100.")
    put("Correlation evidence", "Identity tokens (registered domains, phone numbers, the identity field) shared by events in one 60-minute window, and the window's time span, go into a gradient-boosting model trained on SIMULATED bundles. No rule bonus.")
    put("Combined score", "bundle_risk is the highest-risk window. A window with one event is that event's score; two or more go to the model. It is not a calibrated probability.")
    put("Verdict", "One alert line: bundle risk 0.5 or more alerts ('elevated risk'). There are no SAFE / SUSPICIOUS / HIGH RISK bands. A bundle with nothing assessable answers CANNOT_ASSESS.")
    put("Voice/video", "Not built. /score answers HTTP 501; /correlate lists such events as 'not assessed' and keeps them out of the risk.")
    put("Console", "React console in console/, served by the API, cases run with Playwright." if ui else "React console in console/. The console cases run in Phase 2.4 (scripts/ui_checks.py) and are Not run here.")
    put("Labels in data sheets", "Phishing or Legitimate, from the v2 score at the 0.5 line. For SMS, Phishing means spam or smishing (1 - P(ham) at 0.5 or more).")
    put("Status values", "Pass, Fail, Blocked (cannot run yet), Known limitation (a documented weakness, not a new bug), Not run, N/A (the plan's feature does not exist in v2; the reason is in Actual result).")
    for label, cid in (("EML-09", "EML-09"), ("NFR-05, NFR-07", None), ("Console (UI-01 to UI-07)", "UI-01"), ("Voice/video files (VV-06 to VV-10)", "VV-06")):
        try: r = find_label(ws, label)
        except KeyError: continue
        if cid: ws.cell(r, 2, f"{res['cases'][cid]['status']}: {res['cases'][cid]['actual'][:200]}")
        else: ws.cell(r, 2, f"NFR-05 {res['cases']['NFR-05']['status']}; NFR-07 {res['cases']['NFR-07']['status']}.")
    try: ws.cell(find_label(ws, "EML-10, SMS-08, URL-10"), 2, "Read from reports/*_metrics.json, written by run_all.sh. Reproduced from scratch in Phase 0 (reports/baseline_check.md).")
    except KeyError: pass
    n_new = sum(1 for d in reg.values() if isinstance(d, dict) and d.get("new"))
    try: ws.cell(find_label(ws, "Defect Log"), 2, f"{12 + n_new} defects: 12 from the 29 Sep run and {n_new} found on v2 (D-13 onwards). Status is worked out from the latest run.")
    except KeyError: pass

    wb.calculation.fullCalcOnLoad = True           # Summary formulas recalculate when the file is opened
    wb.save(a.out)
    office = shutil.which("soffice") or shutil.which("libreoffice")
    recalc = "LibreOffice not found: Excel recalculates the Summary sheet on opening (fullCalcOnLoad is set)."
    if office:
        p = subprocess.run([office, "--headless", "--convert-to", "xlsx", "--outdir", str(Path(a.out).parent / "_recalc"), a.out], capture_output=True, text=True, timeout=180)
        recalc = f"LibreOffice recalculation: exit {p.returncode}"

    # ---- defect status files
    (ROOT / "reports" / "defect_status.json").write_text(json.dumps({"run": run, "defects": ds}, indent=1) + "\n", encoding="utf-8")
    L = [f"# Defect log\n", f"Written by `scripts/fill_final_workbook.py` from the run of {run['date'][:16].replace('T', ' ')} on `{run['describe']}`. Status comes from the run: Closed only when every linked case passes. "
         "Accepting a defect is the team's call.\n", "| Defect | Severity | Module | Status | Linked cases on this run | Fixed by | Fix summary |", "|---|---|---|---|---|---|---|"]
    wbsrc = load_workbook(a.source, read_only=True)["Defect Log"]
    old = {str(r[0]): r for r in wbsrc.iter_rows(min_row=2, values_only=True) if r[0]}
    for did in sorted(ds, key=lambda k: int(k[2:])):
        d, s = reg[did], ds[did]
        sev, mod = (d["severity"], d["module"]) if d.get("new") else (old[did][6], old[did][3])
        fixed = d["fixed_by"] + (f" ({', '.join(s['commits'])})" if s["commits"] else "")
        L.append(f"| {did} | {sev} | {mod} | **{s['status']}** | {', '.join(f'{k} {v}' for k, v in s['cases'].items())} | {fixed} | {d['fix_summary']}{(' ' + s['proposal']) if s['proposal'] else ''} |")
    (ROOT / "reports" / "defect_log.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    from collections import Counter
    print(f"wrote {Path(a.out).relative_to(ROOT)}; defects {dict(Counter(s['status'] for s in ds.values()))}; {recalc}")


if __name__ == "__main__":
    main()
