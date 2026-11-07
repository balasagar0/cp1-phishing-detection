"""The test plan's 7 exit criteria (Phase 4.4, R2-11), judged against the targets the plan wrote on 29 Sep and never moved after a result.
  python scripts/exit_criteria.py        (after tests/test_final_cases.py and scripts/fill_final_workbook.py)
The workbook's Summary sheet computes the same criteria with formulas when Excel opens it; this script computes them in Python from the same
inputs (reports/final_cases_results.json, the case list in tests/data/workbook_cases.json, reports/defect_status.json) so they can be quoted.
Targets are read from the team workbook when it is present (docs/inputs/), and must equal the constants below; otherwise the constants are used.
Criterion 4 is reported twice: the plan's held-out split (EML-10, SMS-08, URL-10) and the honest measure for each channel, against the same 0.90.
Writes reports/exit_criteria.md and .json."""
import json, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {"high_not_run": 0, "non_model_pass_rate": 0.95, "sample_groups_met": 12, "held_out_pass": 3, "sys14": "Pass", "speed_pass": 2, "open_critical_high": 0}
WB = ROOT / "docs" / "inputs" / "cp1_inputs" / "Test_Cases_and_Test_Data.xlsx"


def plan_targets():
    if not WB.exists(): return "constants (team workbook not present)"
    from openpyxl import load_workbook
    ws = load_workbook(WB)["Summary"]; got = {}
    for r in range(1, ws.max_row + 1):
        a, b = str(ws.cell(r, 1).value or ""), ws.cell(r, 2).value
        if a.startswith("Non-model test cases"): got["non_model_pass_rate"] = float(b)
        if a.startswith("All High-priority"): got["high_not_run"] = int(str(b).split()[0])
        if a.startswith("All 12 sample groups"): got["sample_groups_met"] = int(str(b).split()[0])
        if a.startswith("Held-out metrics pass"): got["held_out_pass"] = int(str(b).split()[0])
        if a.startswith("Speed tests pass"): got["speed_pass"] = int(str(b).split()[0])
        if a.startswith("No open Critical or High"): got["open_critical_high"] = int(b)
    assert all(TARGETS[k] == v for k, v in got.items()), ("workbook targets differ from the constants", got)
    return f"read from the team workbook's Summary sheet and equal to the constants ({len(got)} values checked)"


def main():
    res = json.loads((ROOT / "reports" / "final_cases_results.json").read_text(encoding="utf-8"))
    plan = {c["TC ID"]: c for c in json.loads((ROOT / "tests" / "data" / "workbook_cases.json").read_text(encoding="utf-8"))["test_cases"]}
    wbdef = {d["Defect ID"]: d for d in json.loads((ROOT / "tests" / "data" / "workbook_cases.json").read_text(encoding="utf-8"))["defects"]}
    reg = json.loads((ROOT / "docs" / "defect_registry.json").read_text(encoding="utf-8"))
    ds = json.loads((ROOT / "reports" / "defect_status.json").read_text(encoding="utf-8"))["defects"]
    C, S = res["cases"], res["samples"]; source = plan_targets(); out = []
    def crit(n, name, target, current, met, detail): out.append({"n": n, "criterion": name, "target": target, "current": current, "met": met, "detail": detail})

    high_nr = [k for k, c in C.items() if plan[k]["Priority"] == "High" and c["status"] == "Not run"]
    crit(1, "All High-priority test cases executed", "0 not run", f"{len(high_nr)} not run", len(high_nr) == TARGETS["high_not_run"], ", ".join(high_nr) or "every High case ran")
    nm = [c["status"] for k, c in C.items() if plan[k]["Category"] != "Model evaluation"]
    p, f = nm.count("Pass"), nm.count("Fail"); rate = p / (p + f) if p + f else None
    crit(2, "Non-model test cases: pass rate", f"{TARGETS['non_model_pass_rate']:.0%} or more", f"{rate:.1%} ({p} pass, {f} fail)" if rate is not None else "not run",
         rate is not None and rate >= TARGETS["non_model_pass_rate"], "N/A and Not run cases are left out, as the workbook's formula does")
    groups = {}
    for sid, s in S.items(): groups.setdefault((s["channel"], s["expected"], s["group"]), []).append(s["result"] == "Pass")
    tgt = lambda g: 0.9 if g == "Standard" else 0.7
    gm = {f"{ch} {lab} {g}": (sum(v) / len(v), tgt(g)) for (ch, lab, g), v in sorted(groups.items())}
    n_met = sum(a >= t for a, t in gm.values())
    crit(3, "All 12 sample groups meet their targets", "12 of 12", f"{n_met} of {len(gm)}", n_met == TARGETS["sample_groups_met"] and len(gm) == 12,
         "; ".join(f"{k} {a:.0%} (target {t:.0%})" for k, (a, t) in gm.items()) + ". Samples are hand-written, not a test set")
    ho = [k for k in ("EML-10", "SMS-08", "URL-10") if C[k]["status"] == "Pass"]
    E = json.loads((ROOT / "reports" / "email_metrics.json").read_text()); Sm = json.loads((ROOT / "reports" / "sms_metrics.json").read_text()); U = json.loads((ROOT / "reports" / "url_metrics.json").read_text())
    honest = {"email: mean leave-one-corpus-out F1": sum(v["f1"] for v in E["leave_one_corpus_out"].values()) / len(E["leave_one_corpus_out"]),
              "SMS: smishing-vs-rest F1": Sm["test_smishing_vs_rest"]["f1"], "URL: host-grouped F1": U["string_model"]["grouped_test"]["f1"]}
    crit("4a", "Held-out metrics pass (EML-10, SMS-08, URL-10): the plan's held-out split", "3 of 3", f"{len(ho)} of 3", len(ho) == TARGETS["held_out_pass"],
         "the plan reads each channel's held-out split against F1 0.90: email pooled random split, SMS spam-or-smishing, URL host-grouped")
    hm = sum(v >= 0.90 for v in honest.values())
    crit("4b", "The same 0.90 line on the honest measures", "3 of 3", f"{hm} of 3", hm == 3, "; ".join(f"{k} {v:.1%} ({'met' if v >= 0.9 else 'not met'})" for k, v in honest.items()))
    crit(5, "Correlation changes a verdict with real models (SYS-14)", "Pass", C["SYS-14"]["status"], C["SYS-14"]["status"] == TARGETS["sys14"],
         "S-01, S-02 and S-11 already alert on one channel; TC-06 (hand-written) is the case where correlation lifts a bundle, see reports/r2_09_evidence.md")
    sp = [k for k in ("NFR-01", "NFR-02") if C[k]["status"] == "Pass"]
    crit(6, "Speed tests pass (NFR-01, NFR-02)", "2 of 2", f"{len(sp)} of 2", len(sp) == TARGETS["speed_pass"], C["NFR-01"]["actual"][:160])
    sev = lambda d: (reg[d].get("severity") if reg.get(d, {}).get("new") else wbdef.get(d, {}).get("Severity"))
    oc = [d for d, s in ds.items() if s["status"] in ("Open", "Fixed", "Retest") and sev(d) in ("Critical", "High")]
    crit(7, "No open Critical or High defects", "0", str(len(oc)), len(oc) == TARGETS["open_critical_high"], ", ".join(f"{d} ({sev(d)})" for d in oc) or "none")
    doc = {"date": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "build": res["run"]["describe"], "commit": res["run"]["commit"], "targets": source,
           "criteria": out, "met": sum(1 for c in out if c["met"]), "of": len(out)}
    (ROOT / "reports" / "exit_criteria.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    L = ["# Exit criteria (R2-11)\n", f"Written by `scripts/exit_criteria.py` on {doc['date']} from the run on `{doc['build']}`. Targets: {source}. No target was moved after a result.\n",
         "| # | Criterion | Target | Current | Status | Detail |", "|---|---|---|---|---|---|"]
    L += [f"| {c['n']} | {c['criterion']} | {c['target']} | {c['current']} | **{'Met' if c['met'] else 'Not met'}** | {c['detail']} |" for c in out]
    L.append(f"\n{doc['met']} of {doc['of']} rows met. Criterion 4 is shown twice, as the brief asks: the plan's own held-out split (4a) and the honest measure (4b).")
    (ROOT / "reports" / "exit_criteria.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    for c in out: print(f"{'Met    ' if c['met'] else 'Not met'} {c['n']}: {c['criterion']} ({c['current']})")


if __name__ == "__main__":
    main()
