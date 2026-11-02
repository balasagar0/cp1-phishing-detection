"""Phase 3.1: the email candidate against v2 under ONE protocol (leave-one-corpus-out), with the adoption rule's checks (a) to (c).
  python src/eval_email_candidates.py          (about 20 minutes on one core)
Writes reports/candidates/email_candidates.json and .md, and models/candidates/email_model.joblib. The live model in models/ is not touched.
  B0  v2's recipe exactly: v2's text cleaner (read from tag v2-baseline), the 3 v2 corpora, C=16. Must reproduce v2's leave-one-corpus-out
      figures; its bootstrap gives the 95% interval of v2's honest metric.
  B1  v2's recipe with today's cleaner (D-11 fix): shows what the cleaner change alone does.
  C1  the candidate: today's cleaner + Nazario, SpamAssassin and Ling. C is chosen on a validation split, as train_email.py does.
Honest metric for rule (a): mean F1 over the held-out CEAS_08, Enron and FraudEmail, the same three corpora for every config.
The new corpora are also held out one at a time for C1, and scored by the live v2 model, which never saw them. A corpus with one class
gets only the measure that makes sense: recall for Nazario (all phishing).
Rule (b): the D-10 and D-17 workbook emails and the EML-01 to EML-03 groups (hand-written, never trained on). Rule (c): TC-01 to TC-08 keep their
alert outcome. Rule (d), every test passing, is checked by running the tests after adoption."""
import sys, json, subprocess, os, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score
import train_email as TE

V2_CORPORA = ["CEAS_08", "Enron", "FraudEmail"]; NEW = ["Nazario", "SpamAssassin", "LingSpam"]
OUTR, OUTM = REPORTS / "candidates", MODELS / "candidates"; OUTR.mkdir(parents=True, exist_ok=True); OUTM.mkdir(parents=True, exist_ok=True)
log = TE.log


def v2_cleaner():
    src = subprocess.run(["git", "show", "v2-baseline:src/common.py"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    ns = {"__file__": str(ROOT / "src" / "common.py"), "__name__": "v2_common"}; exec(compile(src, "v2_common", "exec"), ns)
    return ns["clean_text"]


def held_out(df, C, sources):
    out, preds = {}, {}
    for s in sources:
        a, b = df[df.source != s], df[df.source == s]
        F = TE.Feat(a, min_sources=2); m = TE.fit_lr(F.Xtrain, a.label, C); p = m.predict_proba(F.transform(b.text))[:, 1]
        preds[s] = (b.label.values, p); out[s] = measure(b.label.values, p)
        log(f"  held-out {s}: {out[s]}")
    return out, preds


def measure(y, p):
    y = np.asarray(y); pred = (np.asarray(p) >= .5).astype(int)
    if len(set(y)) == 2:
        m = binary_metrics(y, p); return {k: m[k] for k in ("n", "positives", "precision", "recall", "f1", "false_positive_rate", "roc_auc")}
    if y[0] == 1: return {"n": int(len(y)), "positives": int(len(y)), "recall": round(float(pred.mean()), 4), "note": "one class (all phishing): recall only"}
    return {"n": int(len(y)), "positives": 0, "false_positive_rate": round(float(pred.mean()), 4), "note": "one class (all legitimate): false-positive rate only"}


def boot_mean_f1(preds, B=300, seed=SEED):
    rng = np.random.default_rng(seed); vals = []
    for _ in range(B):
        fs = []
        for y, p in preds.values():
            i = rng.integers(0, len(y), len(y)); fs.append(f1_score(y[i], (p[i] >= .5).astype(int), zero_division=0))
        vals.append(np.mean(fs))
    return [round(float(np.percentile(vals, 2.5)), 4), round(float(np.percentile(vals, 97.5)), 4)]


def choose_C(df):
    tr, rest = train_test_split(df, test_size=0.2, stratify=df.source + "_" + df.label.astype(str), random_state=SEED)
    va, _ = train_test_split(rest, test_size=0.5, stratify=rest.source + "_" + rest.label.astype(str), random_state=SEED)
    F = TE.Feat(tr, min_sources=2); Xva = F.transform(va.text)
    vs = {C: binary_metrics(va.label, TE.fit_lr(F.Xtrain, tr.label, C).predict_proba(Xva)[:, 1])["f1"] for C in (1, 4, 16)}
    return max(vs, key=vs.get), vs


def final_model(df, C):
    Fall = TE.Feat(df, min_sources=2)
    vf = TfidfVectorizer(vocabulary=list(Fall.terms), lowercase=True, strip_accents="unicode", ngram_range=(1, 2), sublinear_tf=True, token_pattern=TE.TOKEN, dtype=np.float32).fit(df.text)
    return {"vectorizer": vf, "clf": TE.fit_lr(vf.transform(df.text), df.label, C),
            "meta": {"channel": "email", "variant": "robust+extra", "mask_numbers": True, "C": C, "n_train": len(df), "sources": sorted(df.source.unique()), "candidate": True}}


def score_with(model, texts):
    return model["clf"].predict_proba(model["vectorizer"].transform(texts))[:, 1]


def sample_checks(model, tag):
    """Workbook emails (hand-written, evaluation only) through the same cleaner the API uses."""
    wb = json.loads((ROOT / "tests" / "data" / "workbook_cases.json").read_text(encoding="utf-8"))["email"]
    out = {}
    for r in wb:
        p = float(score_with(model, [clean_text(f"{r['Subject']} . {r['Body']}", mask_numbers=True)])[0])
        out[r["ID"]] = {"score": round(p, 4), "predicted": "Phishing" if p >= .5 else "Legitimate", "expected": r["Expected label"], "group": r["Group"]}
    grp = lambda g, l: [k for k, v in out.items() if v["group"] == g and v["expected"] == l]
    acc = lambda ids: round(sum(out[i]["predicted"] == out[i]["expected"] for i in ids) / len(ids), 4)
    return {"model": tag, "samples": out, "EML-01 standard phishing": acc(grp("Standard", "Phishing")), "EML-02 standard legitimate": acc(grp("Standard", "Legitimate")),
            "EML-03 hard phishing": acc(grp("Hard case", "Phishing")), "EML-03 hard legitimate": acc(grp("Hard case", "Legitimate")),
            "D-10 cases correct": [i for i in ("E-L08", "E-H06", "E-H04", "E-L06") if out[i]["predicted"] == out[i]["expected"]],
            "D-17 cases correct": [i for i in ("E-P03", "E-P06", "E-P07", "E-P09", "E-H01") if out[i]["predicted"] == out[i]["expected"]]}


def demo_outcomes(model):
    """TC-01 to TC-08 through /correlate with the candidate email model swapped in (in this process only)."""
    os.environ.setdefault("CP1_EVENT_DB", str(Path(tempfile.mkdtemp()) / "e.db")); os.environ.setdefault("CP1_HMAC_KEY", "candidate-check")
    from fastapi.testclient import TestClient
    import api
    from demo_cases import CASES
    c = TestClient(api.app); out = {}
    for tag, m in (("live", None), ("candidate", model)):
        saved = api.D.email
        if m is not None: api.D.email = m
        try:
            for cid, case in CASES.items():
                j = c.post("/correlate", json={"events": case["events"]}).json()
                out.setdefault(cid, {})[tag] = None if j.get("bundle_risk") is None else {"risk": j["bundle_risk"], "alert": j["bundle_risk"] >= .5,
                                                                                       "scores": [e["score"] for e in j["events"]]}
        finally: api.D.email = saved
    return out


def main():
    res = {}
    log("B0: v2's recipe exactly (v2 cleaner, 3 corpora, C=16)")
    d0, _ = TE.load_email(extra=False, cleaner=v2_cleaner())
    b0, p0 = held_out(d0, 16, V2_CORPORA); res["B0_v2_recipe"] = {"held_out": b0, "mean_f1": round(float(np.mean([b0[s]["f1"] for s in V2_CORPORA])), 4), "mean_f1_ci95": boot_mean_f1(p0)}
    v2 = json.loads((REPORTS / "email_metrics.json").read_text())["leave_one_corpus_out"]
    res["B0_v2_recipe"]["reproduces_v2_reports"] = all(abs(v2[s]["f1"] - b0[s]["f1"]) < 1e-4 for s in V2_CORPORA)
    log("B1: v2's recipe with today's cleaner (D-11)")
    d1, _ = TE.load_email(extra=False)
    b1, p1 = held_out(d1, 16, V2_CORPORA); res["B1_v2_recipe_new_cleaner"] = {"held_out": b1, "mean_f1": round(float(np.mean([b1[s]["f1"] for s in V2_CORPORA])), 4), "mean_f1_ci95": boot_mean_f1(p1)}
    log("C1: candidate (today's cleaner + Nazario, SpamAssassin, Ling)")
    d2, dd = TE.load_email(extra=True)
    counts = d2.groupby(["source", "label"]).size().unstack(fill_value=0)
    C, vs = choose_C(d2); log("chosen C", C, vs)
    c1, pc = held_out(d2, C, V2_CORPORA + NEW)
    res["C1_candidate"] = {"chosen_C": C, "validation_f1_by_C": vs, "held_out": c1, "mean_f1": round(float(np.mean([c1[s]["f1"] for s in V2_CORPORA])), 4),
                           "mean_f1_ci95": boot_mean_f1({s: pc[s] for s in V2_CORPORA}), "data": {"dedupe": dd, "counts": {s: {int(k): int(v) for k, v in r.items()} for s, r in counts.iterrows()}}}
    from email_corpora import SKIPPED
    res["C1_candidate"]["files_not_read"] = SKIPPED
    log("final candidate on all data"); cand = final_model(d2, C); joblib.dump(cand, OUTM / "email_model.joblib", compress=3)
    live = joblib.load(MODELS / "email_model.joblib")
    res["live_v2_model_on_new_corpora"] = {s: measure(d2[d2.source == s].label.values, score_with(live, d2[d2.source == s].text)) for s in NEW}
    res["samples_live"], res["samples_candidate"] = sample_checks(live, "live v2 model"), sample_checks(cand, "candidate")
    res["demo_cases"] = demo_outcomes(cand)
    lo = res["B0_v2_recipe"]["mean_f1_ci95"][0]
    a = res["C1_candidate"]["mean_f1"] >= lo
    sl, sc = res["samples_live"], res["samples_candidate"]
    keys = ["EML-01 standard phishing", "EML-02 standard legitimate", "EML-03 hard phishing", "EML-03 hard legitimate"]
    b = (len(sc["D-10 cases correct"]) + len(sc["D-17 cases correct"]) > len(sl["D-10 cases correct"]) + len(sl["D-17 cases correct"])) and all(sc[k] >= sl[k] for k in keys)
    c = all(v["live"] is None and v["candidate"] is None or (v["live"] and v["candidate"] and v["live"]["alert"] == v["candidate"]["alert"]) for v in res["demo_cases"].values())
    res["adoption"] = {"a_honest_metric_not_worse_than_v2_beyond_ci": a, "a_detail": f"candidate mean held-out F1 {res['C1_candidate']['mean_f1']} vs v2 95% interval {res['B0_v2_recipe']['mean_f1_ci95']}",
                       "b_target_defect_cases_improve": b, "c_demo_cases_keep_alert_outcome": c, "d_every_test_passes": "checked after adoption by running the tests",
                       "decision": "candidate passes (a) to (c)" if a and b and c else "keep v2's model; report the candidate as a negative result"}
    save_json(res, OUTR / "email_candidates.json"); write_md(res); log("decision:", res["adoption"])


def write_md(r):
    pct = lambda x: "–" if x is None else f"{100 * x:.1f}%"
    L = ["# Email candidate (Phase 3.1)\n", "Written by `src/eval_email_candidates.py`. Same protocol for every row: leave-one-corpus-out, alert line 0.5.\n",
         "## Held-out corpora (each trained without the corpus it is tested on)\n", "| Corpus held out | B0 v2 recipe | B1 v2 recipe + D-11 cleaner | C1 candidate (+3 corpora) | live v2 model (never saw it) |", "|---|---|---|---|---|"]
    def cell(m):
        if m is None: return "–"
        return f"F1 {pct(m['f1'])} (P {pct(m['precision'])}, R {pct(m['recall'])}, FPR {pct(m['false_positive_rate'])})" if "f1" in m else (f"recall {pct(m['recall'])} (n={m['n']:,})" if "recall" in m else f"FPR {pct(m['false_positive_rate'])}")
    for s in V2_CORPORA + NEW:
        L.append(f"| {s} | {cell(r['B0_v2_recipe']['held_out'].get(s))} | {cell(r['B1_v2_recipe_new_cleaner']['held_out'].get(s))} | {cell(r['C1_candidate']['held_out'].get(s))} | {cell(r['live_v2_model_on_new_corpora'].get(s))} |")
    L += ["", "| Honest metric: mean F1 over held-out CEAS_08, Enron, FraudEmail | 95% interval |", "|---|---|"]
    for k, n in (("B0_v2_recipe", "B0 v2 recipe"), ("B1_v2_recipe_new_cleaner", "B1 v2 recipe + D-11 cleaner"), ("C1_candidate", "C1 candidate")):
        L.append(f"| {n}: {pct(r[k]['mean_f1'])} | {pct(r[k]['mean_f1_ci95'][0])} to {pct(r[k]['mean_f1_ci95'][1])} |")
    L += [f"\nB0 reproduces v2's reported leave-one-corpus-out figures: {r['B0_v2_recipe']['reproduces_v2_reports']}.", "",
          "## Workbook emails (hand-written, not a test set; never trained on)\n", "| Check | live v2 model | candidate |", "|---|---|---|"]
    sl, sc = r["samples_live"], r["samples_candidate"]
    for k in ("EML-01 standard phishing", "EML-02 standard legitimate", "EML-03 hard phishing", "EML-03 hard legitimate"): L.append(f"| {k} | {pct(sl[k])} | {pct(sc[k])} |")
    L.append(f"| D-10 emails right (E-L08, E-H06, E-H04, E-L06) | {', '.join(sl['D-10 cases correct']) or 'none'} | {', '.join(sc['D-10 cases correct']) or 'none'} |")
    L.append(f"| D-17 emails right (E-P03, E-P06, E-P07, E-P09, E-H01) | {', '.join(sl['D-17 cases correct']) or 'none'} | {', '.join(sc['D-17 cases correct']) or 'none'} |")
    L += ["", "## Demo cases (hand-written): alert outcome with the live model and with the candidate\n", "| Case | live | candidate |", "|---|---|---|"]
    for cid, v in r["demo_cases"].items():
        f = lambda x: "CANNOT_ASSESS" if x is None else f"{x['risk']:.3f} ({'alert' if x['alert'] else 'no alert'})"
        L.append(f"| {cid} | {f(v['live'])} | {f(v['candidate'])} |")
    a = r["adoption"]
    L += ["", "## Adoption rule\n", f"- (a) honest metric not worse than v2's beyond its 95% interval: **{a['a_honest_metric_not_worse_than_v2_beyond_ci']}** ({a['a_detail']})",
          f"- (b) the target defects' cases improve (D-10, D-17): **{a['b_target_defect_cases_improve']}**", f"- (c) TC-01 to TC-08 keep their alert outcome: **{a['c_demo_cases_keep_alert_outcome']}**",
          f"- (d) every test passes: {a['d_every_test_passes']}", f"\n**Decision: {a['decision']}.**"]
    if r["C1_candidate"].get("files_not_read"): L.append(f"\nFiles that could not be read and were left out: {r['C1_candidate']['files_not_read']}")
    (OUTR / "email_candidates.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
