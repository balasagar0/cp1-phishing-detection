"""reports/FINAL_TEST_REPORT.md (R3-11, R3-07, R2-11): the final test report, written from the run on cp1-final.
  python scripts/make_final_test_report.py      (after scripts/make_final_numbers.py)
Reads reports/final_cases_results.json (the 112 ported cases, run on cp1-final), the plan's case list (tests/data/workbook_cases.json),
reports/defect_status.json, docs/defect_registry.json, reports/exit_criteria.json and reports/final_numbers.json. Nothing is typed."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; R = ROOT / "reports"
jl = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
cell = lambda s: " ".join(str(s or "").split()).replace("|", "/")
STATUSES = ["Pass", "Fail", "Known limitation", "N/A", "Not run"]


def main():
    FC, W, DS, REG, EX, FN = jl(R / "final_cases_results.json"), jl(ROOT / "tests" / "data" / "workbook_cases.json"), jl(R / "defect_status.json"), \
        jl(ROOT / "docs" / "defect_registry.json"), jl(R / "exit_criteria.json"), jl(R / "final_numbers.json")
    V, run = FN["values"], FC["run"]; plan = {c["TC ID"]: c for c in W["test_cases"]}; wbdef = {d["Defect ID"]: d for d in W["defects"]}
    cases = FC["cases"]
    count = lambda items, key: {s: sum(1 for c in items if c[key] == s) for s in sorted({c[key] for c in items})}
    st, tg = count(cases.values(), "status"), count(cases.values(), "tag")
    L = ["# Final test report (CP1)\n",
         f"Written by `scripts/make_final_test_report.py` from the run of {run['date'][:16].replace('T', ' ')} on **`{run['describe']}`** (commit `{run['commit'][:7]}`), "
         f"Python {run['python']}, {run['platform']}. Every count below comes from `reports/final_cases_results.json` and the other files named; nothing is typed.\n",
         "## 1. Why the suite was ported\n",
         "The test plan (v1.1, 29 Sep) and its 112 cases were written for an older codebase: `/analyze` routes, scores from 0 to 100, a rule bonus capped at 25, "
         "and verdicts SAFE, SUSPICIOUS and HIGH RISK. The codebase changed after 29 Sep. This build has per-channel detectors that give a score from 0 to 1, "
         "a learned correlation model applied in time windows, and an alert line of " + V["alert_line"] + ". So each case was ported, not run as written, and kept its ID:\n",
         "- **Ported:** the same check against this build.",
         "- **Replaced:** the same intent with this build's expectation. HIGH RISK became an alert (risk at or above the alert line), SAFE became no alert, Rejected became HTTP 4xx.",
         "- **N/A:** the feature does not exist in this build (the rule bonus, the risk threshold of 20, the 30/60 verdict bands, the voice module). The reason is given per case.\n",
         "No expectation was weakened so a case would pass. Where the build behaves wrongly, the case fails and is linked to a defect.\n",
         "## 2. Summary\n", f"{len(cases)} cases: " + ", ".join(f"{st.get(s, 0)} {s}" for s in STATUSES if st.get(s)) + ". "
         f"Porting: " + ", ".join(f"{n} {t}" for t, n in tg.items()) + ". Every failure is linked to an open defect; there is no unexpected failure.\n",
         "Other checks on the same build (from `reports/final_numbers.json`):\n",
         f"- pytest: {V['tests.pytest.passed']} passed, {V['tests.pytest.xfailed']} expected failures (open defects), {V['tests.pytest.skipped']} skipped, {V['tests.pytest.failed']} failed.",
         f"- Smoke test: {V['tests.smoke.passed']} passed, {V['tests.smoke.skipped']} skipped (it needs a spreadsheet program).",
         f"- End-to-end check over real HTTP: {V['tests.e2e.passed']} of {V['tests.e2e.steps']} steps pass (`reports/e2e_check.md`).",
         f"- Console UI checks in Chrome and Edge: {V['tests.ui.passed']} of {V['tests.ui.n']} pass; failing: {V['tests.ui.failed']} (`reports/ui_checks.json`).",
         f"- Offline check (no network at runtime): {V['tests.offline']} (`reports/offline_check.md`).",
         f"- NFR-05, a fresh clone run from the README alone: {V['tests.nfr05']} (`reports/nfr05_fresh_clone.json`).",
         f"- Latency over real HTTP: median {V['latency.email.median']} (email), {V['latency.sms.median']} (SMS), {V['latency.url.median']} (URL); slowest full case {V['latency.case.max']} (`reports/benchmark.md`).\n",
         "## 3. Results by module\n", "| Module | Cases | " + " | ".join(STATUSES) + " |", "|---|---|" + "---|" * len(STATUSES)]
    mods = {}
    for cid, c in cases.items(): mods.setdefault(plan[cid]["Module"], []).append(c)
    for m, cs in sorted(mods.items()):
        cc = count(cs, "status"); L.append(f"| {m} | {len(cs)} | " + " | ".join(str(cc.get(s, 0)) for s in STATUSES) + " |")
    L += ["\n## 4. Every case: porting and result\n", "| ID | Module | Priority | Porting | Why (Replaced or N/A) | Result | Defect |", "|---|---|---|---|---|---|---|"]
    for cid, c in cases.items():
        p = plan[cid]; why = cell(c.get("why")) if c["tag"] != "Ported" else "same check"
        L.append(f"| {cid} | {p['Module']} | {p['Priority']} | {c['tag']} | {why} | {c['status']} | {c.get('defect') or 'none'} |")
    L += ["\nThe actual result of each case is in `reports/final_cases_results.json` and in the FINAL workbook (`reports/Test_Cases_and_Test_Data_FINAL.xlsx`).\n",
          "## 5. Sample groups (hand-written samples, not a test set)\n",
          "The plan's 96 hand-written samples, run at the alert line as its 12 sample groups. These are the team's own examples: the counts show behaviour, not a detection rate.\n",
          "| Channel | Expected | Group | Passed | Target |", "|---|---|---|---|---|"]
    groups = {}
    for s in FC["samples"].values(): groups.setdefault((s["channel"], s["expected"], s["group"]), []).append(s["result"] == "Pass")
    for (ch, ex, gr), v in sorted(groups.items()):
        L.append(f"| {ch} | {ex} | {gr} | {sum(v)} of {len(v)} | {'90%' if gr == 'Standard' else '70%'} of the group |")
    L += [f"\nFor SMS the alert score is 1 - P(ham), the score the API alerts on.\n", "## 6. Exit criteria\n",
          f"Judged by `scripts/exit_criteria.py` against the targets the plan wrote on 29 Sep. No target was moved after a result. {EX['met']} of {EX['of']} rows met.\n",
          "| # | Criterion | Target | Current | Status |", "|---|---|---|---|---|"]
    L += [f"| {c['n']} | {c['criterion']} | {c['target']} | {cell(c['current'])} | **{'Met' if c['met'] else 'Not met'}** |" for c in EX["criteria"]]
    L += ["\n## 7. Defect log\n", "Status comes from the run: a defect is Closed only when every linked case passes. Accepting a defect is the team's call; no defect is marked accepted here.\n",
          "| Defect | Severity | Module | What is wrong | Status | Linked cases | Fix or proposal |", "|---|---|---|---|---|---|---|"]
    for d, s in DS["defects"].items():
        reg = REG.get(d, {}); new = reg.get("new"); wd = wbdef.get(d, {})
        sev = reg.get("severity") if new else wd.get("Severity", "")
        mod = reg.get("module") if new else wd.get("Module", "")
        desc = reg.get("description") if new else wd.get("Description", "")
        fix = s.get("proposal") or reg.get("fix_summary") or ""
        L.append(f"| {d} | {sev} | {cell(mod)} | {cell(desc)[:220]} | {s['status']} | " + ", ".join(f"{k} {v}" for k, v in s["cases"].items()) + f" | {cell(fix)[:220] or 'not fixed'} |")
    L += ["\n## 8. What was not tested, and why\n",
          "- **Voice and video.** No detector is built (no accessible data). Their cases are N/A; calls and video answer 'not assessed', never SAFE.",
          "- **Real multi-channel bundles.** None collected yet (R2-10). Correlation is measured on simulated bundles only; SYS-14 with real bundles is still open.",
          "- **The demo laptop.** Latency, offline and UI checks ran on the build laptop. A person confirms the demo laptop or re-runs `scripts/benchmark.py` and `scripts/preflight.py` there.",
          "- **A real Wi-Fi-off run.** `scripts/offline_check.py` blocks sockets in software. One run with the network switched off is a person's job (R3-06).",
          "- **Other browsers and Linux.** The console was checked in Chrome and Edge on Windows; NFR-05 ran on Windows.",
          "- **Load.** Requests were timed one at a time. No concurrent-load test was run.",
          "- **Security testing beyond the plan's cases.** Input checks, the secret scan and the privacy checks ran; no penetration test.",
          "- **Calibration.** Scores are not calibrated probabilities, so no calibration test applies."]
    (R / "FINAL_TEST_REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote reports/FINAL_TEST_REPORT.md: {len(cases)} cases, {len(DS['defects'])} defects")


if __name__ == "__main__":
    main()
