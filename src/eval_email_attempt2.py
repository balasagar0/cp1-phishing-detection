"""Phase 3.1, email candidate ATTEMPT 2 (the brief allows two attempts per model). Run:  python src/eval_email_attempt2.py   (about 15 minutes)
Written, and its rule fixed, BEFORE it was run. Attempt 1 (src/eval_email_candidates.py) passed rule (a) but failed (b) and (c) in the false-alarm
direction: a legitimate receipt was flagged, a weak parcel email crossed the line, and leave-one-corpus-out false-positive rates rose.

C2 = the same data and training as C1 (today's cleaner + Nazario, SpamAssassin, Ling; C chosen on validation in attempt 1). ONLY the alert line moves:
  t = the lowest line at or above 0.5 at which C2, scoring the LEGITIMATE SpamAssassin and Ling-Spam emails with models that never saw that corpus,
      raises no more false alarms than the v2 recipe (v2's three corpora, today's cleaner) raises on the same emails.
The line is applied as an intercept shift (intercept - logit(t)), so a score of 0.5 from the shifted model means t from the unshifted one and the
API's single 0.5 line stays. t is chosen on those two corpora only: the honest metric (CEAS_08, Enron, FraudEmail held out), the workbook emails and
the demo cases are never used to set it; they are only checked afterwards, under the same adoption rule as attempt 1.
Writes reports/candidates/email_candidates_attempt2.md and .json, and models/candidates/email_model_attempt2.joblib (git-ignored)."""
import sys, json, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *
import joblib
from sklearn.metrics import f1_score
import train_email as TE
import eval_email_candidates as E1

CAL = ["SpamAssassin", "LingSpam"]             # where the line is chosen
log = TE.log


def boot_mean_f1_at(preds, t, B=300, seed=SEED):
    rng = np.random.default_rng(seed); vals = []
    for _ in range(B):
        fs = []
        for y, p in preds.values():
            i = rng.integers(0, len(y), len(y)); fs.append(f1_score(y[i], (p[i] >= t).astype(int), zero_division=0))
        vals.append(np.mean(fs))
    return [round(float(np.percentile(vals, 2.5)), 4), round(float(np.percentile(vals, 97.5)), 4)]


def main():
    a1 = json.loads((REPORTS / "candidates" / "email_candidates.json").read_text())
    C = a1["C1_candidate"]["chosen_C"]; v2_ci = a1["B0_v2_recipe"]["mean_f1_ci95"]
    log("loading corpora"); d2, _ = TE.load_email(extra=True); d1, _ = TE.load_email(extra=False)
    log("reference: the v2 recipe (3 corpora, today's cleaner) on the legitimate SpamAssassin and Ling-Spam emails")
    ref = E1.final_model(d1, 16)
    legit = d2[d2.source.isin(CAL) & (d2.label == 0)]
    ref_fpr = float((E1.score_with(ref, legit.text) >= .5).mean())
    log("C2 held-out scores (each corpus scored by a model trained without it)")
    held, preds = E1.held_out(d2, C, E1.V2_CORPORA + E1.NEW)
    cal_neg = np.concatenate([preds[s][1][preds[s][0] == 0] for s in CAL])
    t = next((float(x) for x in np.round(np.arange(0.5, 0.9951, 0.005), 3) if (cal_neg >= x).mean() <= ref_fpr), 0.995)
    cal_fpr = float((cal_neg >= t).mean())
    log(f"reference false-positive rate {ref_fpr:.4f}; C2 at 0.5 {float((cal_neg >= .5).mean()):.4f}; chosen line t={t} gives {cal_fpr:.4f}")
    shift = lambda p: 1 / (1 + np.exp(-(np.log(np.clip(p, 1e-12, 1 - 1e-12) / (1 - np.clip(p, 1e-12, 1 - 1e-12))) - math.log(t / (1 - t)))))   # the same intercept shift the model gets
    at_t = {s: E1.measure(preds[s][0], shift(preds[s][1])) for s in preds}
    mean_t = round(float(np.mean([at_t[s]["f1"] for s in E1.V2_CORPORA])), 4)
    ci_t = boot_mean_f1_at({s: preds[s] for s in E1.V2_CORPORA}, t)
    log("final C2 model on all data, intercept shifted by logit(t)")
    cand = E1.final_model(d2, C); cand["clf"].intercept_ = cand["clf"].intercept_ - math.log(t / (1 - t))
    cand["meta"].update({"variant": "robust+extra, alert line moved", "alert_line_t": t, "alert_line_rule": "no more false alarms than the v2 recipe on held-out legitimate SpamAssassin and Ling-Spam emails"})
    joblib.dump(cand, E1.OUTM / "email_model_attempt2.joblib", compress=3)
    live = joblib.load(MODELS / "email_model.joblib")
    res = {"attempt": 2, "rule_fixed_before_running": __doc__.split("C2 = ")[1].split("Writes")[0].strip(), "chosen_C": C, "alert_line_t": t,
           "calibration": {"corpora": CAL, "legitimate_emails": int(len(legit)), "v2_recipe_false_positive_rate": round(ref_fpr, 4),
                           "C2_false_positive_rate_at_0.5": round(float((cal_neg >= .5).mean()), 4), "C2_false_positive_rate_at_t": round(cal_fpr, 4)},
           "held_out_at_t": at_t, "mean_f1_at_t": mean_t, "mean_f1_at_t_ci95": ci_t, "v2_mean_f1_ci95": v2_ci,
           "samples_live": E1.sample_checks(live, "live v2 model"), "samples_candidate": E1.sample_checks(cand, "attempt 2")}
    res["demo_cases"] = E1.demo_outcomes(cand)
    sl, sc = res["samples_live"], res["samples_candidate"]
    keys = ["EML-01 standard phishing", "EML-02 standard legitimate", "EML-03 hard phishing", "EML-03 hard legitimate"]
    a = mean_t >= v2_ci[0]
    b = (len(sc["D-10 cases correct"]) + len(sc["D-17 cases correct"]) > len(sl["D-10 cases correct"]) + len(sl["D-17 cases correct"])) and all(sc[k] >= sl[k] for k in keys)
    c = all(v["live"] is None and v["candidate"] is None or (v["live"] and v["candidate"] and v["live"]["alert"] == v["candidate"]["alert"]) for v in res["demo_cases"].values())
    res["adoption"] = {"a_honest_metric_not_worse_than_v2_beyond_ci": a, "a_detail": f"attempt 2 mean held-out F1 {mean_t} vs v2 95% interval {v2_ci}",
                       "b_target_defect_cases_improve": b, "c_demo_cases_keep_alert_outcome": c, "d_every_test_passes": "checked after adoption by running the tests",
                       "decision": "attempt 2 passes (a) to (c)" if a and b and c else "keep v2's model; attempt 2 is a negative result (second failed attempt: the team decides next, per the brief)"}
    save_json(res, E1.OUTR / "email_candidates_attempt2.json"); write_md(res); log("decision:", res["adoption"])


def write_md(r):
    pct = lambda x: "–" if x is None else f"{100 * x:.1f}%"
    cal = r["calibration"]
    L = ["# Email candidate, attempt 2 (Phase 3.1)\n", "Written by `src/eval_email_attempt2.py`. Its rule was fixed in the script before it ran:\n", "> " + r["rule_fixed_before_running"].replace("\n", " ") + "\n",
         "## The alert line\n", f"- Calibration set: {cal['legitimate_emails']:,} legitimate emails from {', '.join(cal['corpora'])}, each scored by a model that never saw its corpus.",
         f"- False alarms there: v2 recipe {pct(cal['v2_recipe_false_positive_rate'])}; attempt 2 at 0.5 {pct(cal['C2_false_positive_rate_at_0.5'])}; attempt 2 at the chosen line {pct(cal['C2_false_positive_rate_at_t'])}.",
         f"- Chosen line t = **{r['alert_line_t']}** (applied as an intercept shift, so the API keeps its 0.5 line).", "",
         "## Held-out corpora at the chosen line\n", "| Corpus held out | Attempt 2 |", "|---|---|"]
    for s, m in r["held_out_at_t"].items():
        L.append(f"| {s} | " + (f"F1 {pct(m['f1'])} (P {pct(m['precision'])}, R {pct(m['recall'])}, FPR {pct(m['false_positive_rate'])})" if "f1" in m else f"recall {pct(m.get('recall'))} (n={m['n']:,})") + " |")
    L += ["", f"Honest metric (mean F1 over held-out CEAS_08, Enron, FraudEmail): attempt 2 **{pct(r['mean_f1_at_t'])}** (95% interval {pct(r['mean_f1_at_t_ci95'][0])} to {pct(r['mean_f1_at_t_ci95'][1])}); "
          f"v2's 95% interval {pct(r['v2_mean_f1_ci95'][0])} to {pct(r['v2_mean_f1_ci95'][1])}.", "", "## Workbook emails (hand-written, not a test set; never trained on, never used to set the line)\n",
          "| Check | live v2 model | attempt 2 |", "|---|---|---|"]
    sl, sc = r["samples_live"], r["samples_candidate"]
    for k in ("EML-01 standard phishing", "EML-02 standard legitimate", "EML-03 hard phishing", "EML-03 hard legitimate"): L.append(f"| {k} | {pct(sl[k])} | {pct(sc[k])} |")
    L.append(f"| D-10 emails right (E-L08, E-H06, E-H04, E-L06) | {', '.join(sl['D-10 cases correct']) or 'none'} | {', '.join(sc['D-10 cases correct']) or 'none'} |")
    L.append(f"| D-17 emails right (E-P03, E-P06, E-P07, E-P09, E-H01) | {', '.join(sl['D-17 cases correct']) or 'none'} | {', '.join(sc['D-17 cases correct']) or 'none'} |")
    L += ["", "## Demo cases (hand-written): alert outcome\n", "| Case | live | attempt 2 |", "|---|---|---|"]
    for cid, v in r["demo_cases"].items():
        f = lambda x: "CANNOT_ASSESS" if x is None else f"{x['risk']:.3f} ({'alert' if x['alert'] else 'no alert'})"
        L.append(f"| {cid} | {f(v['live'])} | {f(v['candidate'])} |")
    a = r["adoption"]
    L += ["", "## Adoption rule\n", f"- (a) honest metric not worse than v2's beyond its 95% interval: **{a['a_honest_metric_not_worse_than_v2_beyond_ci']}** ({a['a_detail']})",
          f"- (b) the target defects' cases improve (D-10, D-17): **{a['b_target_defect_cases_improve']}**", f"- (c) TC-01 to TC-08 keep their alert outcome: **{a['c_demo_cases_keep_alert_outcome']}**",
          f"- (d) every test passes: {a['d_every_test_passes']}", f"\n**Decision: {a['decision']}.**"]
    (E1.OUTR / "email_candidates_attempt2.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
