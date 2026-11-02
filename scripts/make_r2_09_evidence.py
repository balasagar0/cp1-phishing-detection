"""Evidence for R2-09 (D-12, SYS-14): does correlation change a verdict with real scores?  python scripts/make_r2_09_evidence.py
One table, every row labelled by kind: fixed scores (old build and v2's engine), hand-written cases with real detector scores, and the simulated
weak campaigns from the reports. Writes reports/r2_09_evidence.md and .json. Every value is read from a file or computed here; nothing is typed."""
import json, os, re, sys, tempfile, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("CP1_EVENT_DB", str(Path(tempfile.mkdtemp(prefix="cp1_r209_")) / "events.db")); os.environ.setdefault("CP1_HMAC_KEY", "evidence-key")
from fastapi.testclient import TestClient
import api
from predict import extract_ids
from demo_cases import CASES

SRC = ROOT / "docs" / "inputs" / "cp1_inputs" / "Test_Cases_and_Test_Data.xlsx"


def old_s03():
    """The 29 Sep run's SYS-03 result, read from the team workbook (the old build used fixed scores 55 / 52 / 58 and a rule bonus)."""
    if not SRC.exists(): return None
    from openpyxl import load_workbook
    for r in load_workbook(SRC, read_only=True)["Test Cases"].iter_rows(min_row=2, values_only=True):
        if r[0] == "SYS-03": return str(r[11])
    return None


def main():
    c = TestClient(api.app); rows = []
    o = old_s03()
    if o:
        m = re.search(r"Best single ([\d.]+) \((\w+)\), bonus \+(\d+), combined ([\d.]+) -> ([A-Z ]+)\.", o)
        rows.append({"evidence": "S-03 on the old build (29 Sep run)", "kind": "fixed scores (55 / 52 / 58 on a 0-100 scale), rule bonus", "events": "email 55, sms 52, url 58",
                     "alone": f"best single {m.group(1)} = {m.group(2)}" if m else o[:80], "bundle": f"{m.group(4)} = {m.group(5).strip()} (bonus +{m.group(3)})" if m else "",
                     "lift": "yes, from SUSPICIOUS to HIGH RISK, on fixed scores", "source": "team workbook, SYS-03 'Actual result' (29 Sep)"})
    ev = [{"channel": ch, "score": s, "ids": extract_ids(ch, t), "t": float(i)} for i, (ch, s, t) in enumerate((("email", .55, "Click bit.ly/xyz to verify your account"), ("sms", .52, "Verify your account now: bit.ly/xyz"), ("url", .58, "bit.ly/xyz")))]
    f = api.F.risk(ev)
    rows.append({"evidence": "S-03 fixed scores through v2's engine", "kind": "fixed scores (0.55 / 0.52 / 0.58)", "events": "email 0.550, sms 0.520, url 0.580",
                 "alone": "yes (each is at or above 0.5)", "bundle": f"{f['risk']:.3f}", "lift": "no: with one line at 0.5 these scores already alert alone", "source": "fusion.Fusion.risk, computed here"})
    for cid, what in (("TC-06", "weak parcel campaign, 15 minutes"), ("TC-07", "TC-06's messages 3 days apart (control)"), ("TC-05", "colleague shares an article (linked but harmless)"),
                      ("TC-04", "KYC campaign on one domain")):
        j = c.post("/correlate", json={"events": CASES[cid]["events"]}).json()
        alone = j["single_channel_alert"]; final = j["bundle_risk"] >= 0.5
        rows.append({"evidence": f"{cid}: {what}", "kind": "hand-written, not a test set (real detector scores)",
                     "events": ", ".join(f"{e['channel']} {e['score']:.3f}" for e in j["events"]), "alone": "yes" if alone else "no",
                     "bundle": f"{j['bundle_risk']:.3f} ({'alert' if final else 'no alert'}; {j['n_windows']} window{'s' if j['n_windows'] > 1 else ''}, shared {', '.join(j['shared_identity_tokens']) or 'none'})",
                     "lift": "yes: no event alerts alone, the bundle does" if final and not alone else ("no: already alerts alone" if alone else "no: stays below the line"), "source": "POST /correlate, run here"})
    W = json.loads((ROOT / "reports" / "window_metrics.json").read_text()); Fm = json.loads((ROOT / "reports" / "fusion_metrics.json").read_text())
    h = W["campaigns_missed_by_every_single_channel_filter"]; share = Fm["campaigns_missed_by_every_single_channel_filter"]["share_of_linked_attacks"]
    rows.append({"evidence": "Simulated linked attacks where every event is below 0.5", "kind": "SIMULATED bundles (12,000 test bundles; real held-out messages, constructed links)",
                 "events": f"{h['n']} campaigns ({100 * share:.1f}% of simulated linked attacks)", "alone": "no (by definition)",
                 "bundle": f"flagged by the 60-minute engine: {100 * h['caught_engine_default_window_at_0.5']:.1f}% ({round(h['n'] * h['caught_engine_default_window_at_0.5'])} of {h['n']}); by the whole-bundle model: {100 * h['caught_whole_bundle_model_at_0.5']:.1f}%",
                 "lift": "yes, for a minority of a small group, on simulated bundles", "source": "reports/window_metrics.json, reports/fusion_metrics.json"})
    for sid in ("S-01", "S-02", "S-11"):
        pass                                           # SYS-14's own scenarios: already alerting alone; reported in reports/final_cases_results.json
    res = json.loads((ROOT / "reports" / "final_cases_results.json").read_text(encoding="utf-8")) if (ROOT / "reports" / "final_cases_results.json").exists() else None
    sys14 = res["cases"]["SYS-14"]["actual"] if res else "run tests/test_final_cases.py"
    doc = {"date": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "rows": rows, "sys14": sys14}
    (ROOT / "reports" / "r2_09_evidence.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    L = ["# R2-09: does correlation change a verdict with real scores?\n", f"Written by `scripts/make_r2_09_evidence.py` on {doc['date']}. Every row says what kind of evidence it is.\n",
         "| Evidence | Kind | Event scores | Alerts alone? | Bundle | Correlation lifts the verdict? | Source |", "|---|---|---|---|---|---|---|"]
    L += [f"| {r['evidence']} | {r['kind']} | {r['events']} | {r['alone']} | {r['bundle']} | {r['lift']} | {r['source']} |" for r in rows]
    L += ["", f"**SYS-14 as the plan wrote it** (S-01, S-02, S-11 with the real models): {sys14}", "",
          "**Reading.** The only case with real detector scores where correlation lifts a verdict is TC-06, which is hand-written; its control TC-07 (same messages, days apart) does not lift, and the "
          "harmless linked case TC-05 stays low. On simulated bundles, correlation flags a minority of the small group of campaigns that every single-channel filter misses. "
          "Neither is a field result: real bundles (R2-10) are needed before claiming more."]
    (ROOT / "reports" / "r2_09_evidence.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
