"""Record of the Phase 4.1 final run (download_data.sh + run_all.sh on cp1-rc1) and why its models were not adopted.
  python scripts/final_run_record.py
Inputs: the live reports in reports/, the final run's reports in reports/final_run/ (copied there after the run), the live models in
models/, the final run's models in models/candidates/final_run/ (local only, gitignored), and both sets of simulation pools
(data/processed/ and data/processed/final_run/, gitignored). Scores the eight demo cases (hand-written, not a test set) with every mix of
detectors and correlation model, and checks them against the adoption rule (c): demo alert outcomes are kept.
Writes reports/final_run/tc_cross_check.json and reports/final_run/README.md. Every number is computed here; nothing is typed."""
import json, subprocess, sys, warnings, datetime
from pathlib import Path
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]; sys.path[:0] = [str(ROOT), str(ROOT / "src")]
FR, FRM, FRP = ROOT / "reports" / "final_run", ROOT / "models" / "candidates" / "final_run", ROOT / "data" / "processed" / "final_run"


def jl(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def loco(E): v = E["leave_one_corpus_out"]; return sum(x["f1"] for x in v.values()) / len(v)
def git(*a): return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def main():
    if not FRM.exists(): sys.exit(f"{FRM} is missing: the final run's models are needed to score the demo cases")
    import api
    from predict import Detectors
    from fusion import Fusion
    from demo_cases import CASES
    from fastapi.testclient import TestClient
    c = TestClient(api.app)
    D = {"live": Detectors(ROOT / "models"), "retrained": Detectors(FRM)}
    F = {"live": Fusion(ROOT / "models" / "fusion_model.joblib"), "retrained": Fusion(FRM / "fusion_model.joblib")}
    keep_D, keep_F = api.D, api.F
    cases = {}
    try:
        for cid in sorted(CASES):
            row = {}
            for dn in D:
                for fn in F:
                    api.D, api.F = D[dn], F[fn]
                    j = c.post("/correlate", json={"events": CASES[cid]["events"]}).json()
                    br = j.get("bundle_risk")
                    row[f"{dn} detectors + {fn} correlation"] = {"status": j.get("status"), "event_scores": [None if e.get("score") is None else round(e["score"], 3) for e in j.get("events", [])],
                                                                 "bundle_risk": None if br is None else round(br, 3), "alert": br is not None and br >= 0.5}
            cases[cid] = row
    finally:
        api.D, api.F = keep_D, keep_F
    L, R = "live detectors + live correlation", "retrained detectors + retrained correlation"
    flips = [cid for cid, r in cases.items() if r[L]["alert"] != r[R]["alert"]]
    WL, WR = jl(ROOT / "reports" / "window_metrics.json"), jl(FR / "window_metrics.json")
    EL, ER = jl(ROOT / "reports" / "email_metrics.json"), jl(FR / "email_metrics.json")
    pools = {ch: (FRP / f"pool_{ch}.csv").read_bytes() == (ROOT / "data" / "processed" / f"pool_{ch}.csv").read_bytes() for ch in ("email", "sms", "url")} if FRP.exists() else "not checked: data/processed/final_run/ is missing"
    build = (FR / "commit.txt").read_text(encoding="utf-8").strip()
    doc = {"date": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "build": build, "commit": git("rev-parse", f"{build}^{{commit}}"),
           "what": "download_data.sh and run_all.sh on the build above (Phase 4.1). Demo cases are hand-written, not a test set.",
           "email_loco_mean_f1": {"live": round(loco(EL), 4), "retrained": round(loco(ER), 4)},
           "simulated_f1_60min": {"live": WL["engine_default_window_at_0.5"]["f1"], "retrained": WR["engine_default_window_at_0.5"]["f1"]},
           "simulation_pools_identical": pools,
           "adoption_rule_c": {"rule": "the demo cases' alert outcomes are kept", "cases_whose_alert_changes": flips, "met": not flips},
           "decision": "not adopted: the account owner chose on 7 Nov 2026 to keep v2's models live, applying the same adoption rule as Phase 3",
           "cases": cases}
    for cid in ("TC-06", "TC-07"): doc[cid] = {k: v["bundle_risk"] for k, v in cases[cid].items()}
    (FR / "tc_cross_check.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")

    pct = lambda x: f"{100 * x:.1f}%"
    M = ["# Final run record (Phase 4.1)\n",
         f"Written by `scripts/final_run_record.py` on {doc['date']}. Every number below is computed by that script.\n",
         f"`download_data.sh` and `run_all.sh` ran on `{build}` (commit `{doc['commit'][:7]}`). This folder holds the reports that run wrote (`*.json`, `results.md`, `log_*.txt`, `run_all_log.txt`). "
         "The models it trained are kept on the build laptop in `models/candidates/final_run/` and are not committed; `model_manifest.json` here lists their hashes.\n",
         "## Decision\n", f"**Not adopted.** {doc['decision']}. Rule (c) says the demo cases' alert outcomes are kept; "
         f"{'it is met' if not flips else 'it fails on ' + ', '.join(flips)}. The shipped models are v2's, and `reports/` describes them.\n",
         "## What changed and why\n",
         "The only training change since v2 is the email text cleaner fix (D-11, D-15: drop scripts and styles, keep link targets). "
         + (f"The simulation pools for SMS and URL are {'identical' if pools.get('sms') and pools.get('url') else 'not identical'}; the email pool {'is identical' if pools.get('email') else 'differs'}. " if isinstance(pools, dict) else "")
         + f"Email honest F1 (mean of three leave-one-corpus-out runs): live {pct(doc['email_loco_mean_f1']['live'])}, retrained {pct(doc['email_loco_mean_f1']['retrained'])}. "
         f"Simulated 60-minute engine F1: live {pct(doc['simulated_f1_60min']['live'])}, retrained {pct(doc['simulated_f1_60min']['retrained'])}. "
         "Every figure is compared value by value in `reports/final_run_check.md`.\n",
         "## Demo cases (hand-written, not a test set)\n", "| Case | Live models: events, bundle, alert | Retrained models: events, bundle, alert | Alert outcome kept |", "|---|---|---|---|"]
    show = lambda r: f"{r['event_scores']}, {r['bundle_risk']}, {'alert' if r['alert'] else 'no alert'}" if r["status"] != "CANNOT_ASSESS" else f"{r['status']} (calls are not assessed)"
    M += [f"| {cid} | {show(r[L])} | {show(r[R])} | {'yes' if r[L]['alert'] == r[R]['alert'] else '**no**'} |" for cid, r in cases.items()]
    M += ["\n## Which model moves TC-06\n", "| Detectors | Correlation model | TC-06 bundle risk | TC-07 bundle risk |", "|---|---|---|---|"]
    for k in cases["TC-06"]:
        d, f = k.split(" + "); M.append(f"| {d.replace(' detectors', '')} | {f.replace(' correlation', '')} | {cases['TC-06'][k]['bundle_risk']} | {cases['TC-07'][k]['bundle_risk']} |")
    M.append("\nThe drop comes from the retrained correlation model; the detectors barely move. The simulated metrics hardly change, so the correlation model's verdict on a weak, "
             "borderline bundle is not stable under a retrain on almost the same simulated data. Real bundles (R2-10) are needed to settle it.")
    (FR / "README.md").write_text("\n".join(M) + "\n", encoding="utf-8")
    print("alert outcome changes:", flips or "none"); print({k: doc[k] for k in ("email_loco_mean_f1", "simulated_f1_60min", "simulation_pools_identical")}); print("TC-06:", doc["TC-06"])


if __name__ == "__main__":
    main()
