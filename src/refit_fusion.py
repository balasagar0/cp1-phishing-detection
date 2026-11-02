"""Evaluate, and when there is enough data refit, the correlation model on REAL Review-2 bundles.
  python src/refit_fusion.py testcases/my_cases.xlsx                    # evaluation only
  python src/refit_fusion.py testcases/my_cases.xlsx --save             # also writes models/fusion_model_real.joblib (API picks it up)
Evaluation always comes first: the simulation-trained model is tested on your real bundles before anything is refit.
  --window N    time window in minutes (default: the model's, 60). Events further apart are not combined or linked; a bundle takes its highest-risk window.
  --no-window   no time limit (every event of a bundle is combined). With --save the chosen window is stored in the model and the API uses it."""
import sys, argparse, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *
from fusion import *
from testcases import *
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import roc_auc_score

MIN_TOTAL, MIN_PER_CLASS = 150, 40            # guard-rails chosen for the 5-parameter stacked model (about 8 bundles per parameter per class)
MIN_PER_CLASS_FULL = 150                      # 15 features x 10 bundles per feature, for --model lr

ap = argparse.ArgumentParser()
ap.add_argument("path"); ap.add_argument("--target", choices=["malicious", "coordinated"], default="malicious")
ap.add_argument("--model", choices=["stacked", "lr"], default="stacked"); ap.add_argument("--save", action="store_true")
ap.add_argument("--allow-examples", action="store_true", help="smoke tests only"); ap.add_argument("--models-dir", default=str(MODELS)); ap.add_argument("--reports-dir", default=str(REPORTS))
ap.add_argument("--window", type=float, default=None, help="time window in minutes (default: the model's, 60)"); ap.add_argument("--no-window", action="store_true", help="no time limit")
a = ap.parse_args()

df, issues = validate(read_table(a.path), a.allow_examples)
for lv, r, m in issues: print(f"[{lv}] row {r}: {m}" if r else f"[{lv}] {m}")
if any(lv == "error" for lv, _, _ in issues): sys.exit("Fix the errors above and run again.")
if df.empty: sys.exit("No usable rows (example rows are ignored).")
from predict import Detectors
bundles = build_bundles(df, Detectors())
F0 = Fusion(Path(a.models_dir) / "fusion_model.joblib"); base = F0.model
W = None if a.no_window else (a.window if a.window is not None else F0.window)      # the same rule the API applies
dec = [windowed_risk(base, b["events"], W) for b in bundles]                         # each bundle is scored on its highest-risk time window
X = np.stack([d["x"] for d in dec]); y = np.array([b[a.target] for b in bundles]); grp = np.array([b["group"] for b in bundles]); mx = np.array([max(e["score"] for e in b["events"]) for b in bundles])
print(f"{len(bundles)} bundles ({int(y.sum())} positive for '{a.target}', {int((1 - y).sum())} negative) from {df.source_type.nunique()} source type(s): {', '.join(sorted(df.source_type.unique()))}")
print(f"time window: {'none' if W is None else f'{W:g} minutes'}")


def boot(y_, pred, g, B=500, seed=SEED):
    rng = np.random.default_rng(seed); ug = np.unique(g); idx = {k: np.where(g == k)[0] for k in ug}; r = {"precision": [], "recall": [], "f1": []}
    for _ in range(B):
        i = np.concatenate([idx[k] for k in rng.choice(ug, len(ug))]); yy, pp = y_[i], pred[i]
        tp, fp, fn = ((pp == 1) & (yy == 1)).sum(), ((pp == 1) & (yy == 0)).sum(), ((pp == 0) & (yy == 1)).sum()
        pr, rc = tp / max(tp + fp, 1), tp / max(tp + fn, 1); r["precision"].append(pr); r["recall"].append(rc); r["f1"].append(2 * pr * rc / max(pr + rc, 1e-9))
    return {k: [round(float(np.percentile(v, 2.5)), 3), round(float(np.percentile(v, 97.5)), 3)] for k, v in r.items()}


def evaluate(name, p):
    m = binary_metrics(y, p); m["ci95"] = boot(y, (p >= .5).astype(int), grp); return name, m


# base (the correlation model) and the time window W were set above
pct = lambda v: f"{100 * v:.1f}%"
rows = [evaluate("Single-channel: alert if any event >= 0.5", mx), evaluate("Correlation model trained on simulated bundles (as deployed)", base.predict_proba(X)[:, 1])]
res = {"n_bundles": len(bundles), "target": a.target, "positives": int(y.sum()), "window_minutes": W, "evaluation_no_training": {n: m for n, m in rows}}
n_pos, n_neg = int(y.sum()), int((1 - y).sum()); need = MIN_PER_CLASS_FULL if a.model == "lr" else MIN_PER_CLASS
ok = len(bundles) >= MIN_TOTAL and min(n_pos, n_neg) >= need
refit_note = ""
if not ok:
    refit_note = f"Not refit: needs at least {MIN_TOTAL} bundles and {need} per class for --model {a.model}; you have {len(bundles)} ({n_pos} positive, {n_neg} negative)."
else:
    mk = lambda: (StackedFusion(base, make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000))) if a.model == "stacked" else make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000)))
    oof = np.zeros(len(y)); cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    for tr, te in cv.split(X, y, grp):
        if a.model == "stacked":
            m = mk(); m.lr.fit(m._z(X[tr]), y[tr]); oof[te] = m.predict_proba(X[te])[:, 1]
        else:
            m = mk().fit(X[tr], y[tr]); oof[te] = m.predict_proba(X[te])[:, 1]
    rows.append(evaluate(f"Refit on real bundles ({a.model}), 5-fold cross-validation grouped by campaign", oof)); res["cv_refit"] = rows[-1][1]
    res["auc"] = {"single_channel": round(float(roc_auc_score(y, mx)), 4), "deployed": round(float(roc_auc_score(y, base.predict_proba(X)[:, 1])), 4), "refit_cv": round(float(roc_auc_score(y, oof)), 4)}
    if a.save:
        final = mk()
        if a.model == "stacked": final.lr.fit(final._z(X), y)
        else: final.fit(X, y)
        joblib.dump({"model": final, "meta": {"trained_on": f"{len(bundles)} real test-case bundles (target: {a.target})", "model": a.model, "date": datetime.date.today().isoformat(), "feature_names": FEATURE_NAMES, "window_minutes": float(W) if W is not None else 1e6}}, Path(a.models_dir) / "fusion_model_real.joblib", compress=3)
        refit_note = f"Saved {a.models_dir}/fusion_model_real.joblib. Restart the API to use it."
    else: refit_note = "Cross-validated refit done; add --save to write the model."

# ---- pre-set hypothesis tests (decision rules are fixed in the test plan; paired bootstrap resamples whole campaigns) ----
pf = base.predict_proba(X)[:, 1]
pf0 = base.predict_proba(np.stack([bundle_features(b["events"], strip=True) for b in bundles]))[:, 1]     # same model, link + timing evidence hidden
coord = np.array([b["coordinated"] for b in bundles])
def _rates(yy, pp):
    pr = pp >= .5; return (pr & (yy == 0)).sum() / max((yy == 0).sum(), 1), (pr & (yy == 1)).sum() / max((yy == 1).sum(), 1)
def _paired(B=1000, seed=SEED):
    rng = np.random.default_rng(seed); ug = np.unique(grp); idx = {k: np.where(grp == k)[0] for k in ug}; d = {"fpr": [], "recall": [], "auc": []}
    for _ in range(B):
        i = np.concatenate([idx[k] for k in rng.choice(ug, len(ug))]); yy = y[i]
        if yy.min() == yy.max(): continue
        fs, rs = _rates(yy, mx[i]); ff, rf = _rates(yy, pf[i])
        d["fpr"].append(ff - fs); d["recall"].append(rf - rs); d["auc"].append(roc_auc_score(yy, pf[i]) - roc_auc_score(yy, pf0[i]))
    return {k: [round(float(np.mean(v)), 4), round(float(np.percentile(v, 2.5)), 4), round(float(np.percentile(v, 97.5)), 4)] for k, v in d.items()}
pb = _paired(); H = {}
H["H1"] = {"false_positive_rate_difference": pb["fpr"], "recall_difference": pb["recall"], "verdict": "supported" if pb["fpr"][2] < 0 and pb["recall"][1] > -0.05 else "not shown"}
H["H2"] = {"auc_difference_with_minus_without_link_timing": pb["auc"], "verdict": "supported" if pb["auc"][1] > 0 else "not shown"}
mk3 = (coord == 1) & (mx < .5); n3 = int(mk3.sum())
if n3 >= 10:
    k3 = int((pf[mk3] >= .5).sum()); zz = 1.96; ph = k3 / n3; dn = 1 + zz * zz / n3
    ctr = (ph + zz * zz / (2 * n3)) / dn; hw = zz * np.sqrt(ph * (1 - ph) / n3 + zz * zz / (4 * n3 * n3)) / dn
    H["H3"] = {"campaigns_missed_by_every_single_channel_filter": n3, "flagged_by_correlation_model": round(ph, 4), "wilson_ci95": [round(float(ctr - hw), 4), round(float(ctr + hw), 4)], "verdict": "reported"}
else:
    H["H3"] = {"campaigns_missed_by_every_single_channel_filter": n3, "verdict": "not shown (fewer than 10 such campaigns)"}
res["hypotheses"] = H
res["assumption_check"] = assumption_check(bundles); res["time_window"] = suggest_window(bundles)
L = ["# Review-2 real-bundle evaluation\n", f"File: `{a.path}`. {len(bundles)} bundles; target `{a.target}`: {n_pos} positive, {n_neg} negative. Sources: {', '.join(sorted(df.source_type.unique()))}.\n",
     "Confidence intervals resample whole campaigns, not single bundles.\n", f"Time window: {'none (every event of a bundle is combined)' if W is None else f'{W:g} minutes (events further apart are not combined or linked; a bundle takes the risk of its highest-risk window)'}.\n", "| Model | Precision | Recall | F1 | False-positive rate | ROC-AUC |\n|---|---|---|---|---|---|"]
for n, m in rows: L.append(f"| {n} | {pct(m['precision'])} ({m['ci95']['precision'][0]:.2f}-{m['ci95']['precision'][1]:.2f}) | {pct(m['recall'])} ({m['ci95']['recall'][0]:.2f}-{m['ci95']['recall'][1]:.2f}) | {pct(m['f1'])} | {pct(m['false_positive_rate'])} | {m.get('roc_auc', float('nan')):.3f} |")
L += ["", refit_note, "", "## Simulation assumptions vs your data\n", "| Quantity | Your data | Simulation |\n|---|---|---|"] + [f"| {q} | {d} | {s} |" for q, d, s in res["assumption_check"]]
L += ["", "## Hypothesis tests (rules fixed in the test plan)\n", "| Hypothesis | Estimate (95% interval, whole campaigns resampled) | Verdict |\n|---|---|---|"]
f_, r_, a_ = H["H1"]["false_positive_rate_difference"], H["H1"]["recall_difference"], H["H2"]["auc_difference_with_minus_without_link_timing"]
L.append(f"| H1: lower false-positive rate at the 0.5 line, recall not more than 5 points lower | false-positive rate {100*f_[0]:+.1f} points ({100*f_[1]:+.1f} to {100*f_[2]:+.1f}); recall {100*r_[0]:+.1f} points ({100*r_[1]:+.1f} to {100*r_[2]:+.1f}) | {H['H1']['verdict']} |")
L.append(f"| H2: link and timing evidence adds ROC-AUC | {a_[0]:+.3f} ({a_[1]:+.3f} to {a_[2]:+.3f}) | {H['H2']['verdict']} |")
h3 = H["H3"]; L.append(f"| H3: campaigns missed by every single-channel filter are flagged | " + (f"{100*h3['flagged_by_correlation_model']:.0f}% of {h3['campaigns_missed_by_every_single_channel_filter']} (Wilson {100*h3['wilson_ci95'][0]:.0f}-{100*h3['wilson_ci95'][1]:.0f}%)" if "wilson_ci95" in h3 else f"{h3['campaigns_missed_by_every_single_channel_filter']} such campaigns") + f" | {h3['verdict']} |")
w = res["time_window"]; L += ["", "## Time-clustering window", "", (f"Suggested window: **{w['window_minutes']:.0f} minutes** (n={w['n']} coordinated bundles; median span {w['median']:.0f} min; 90th percentile {w['p90']:.0f} min, 95% CI {w['p90_ci95'][0]:.0f}-{w['p90_ci95'][1]:.0f}). {w['note']}." if w["window_minutes"] else f"No suggestion yet: {w['note']} (have {w['n']}).")]
if set(df.source_type) <= {"public_dataset", "example"}: L += ["", "**Warning:** no lab_simulation or collected_real rows; timings and links in this file are not real behaviour."]
Path(a.reports_dir).mkdir(exist_ok=True, parents=True); (Path(a.reports_dir) / "real_bundles_report.md").write_text("\n".join(L)); save_json(res, Path(a.reports_dir) / "real_bundles_metrics.json")
print("\n".join(L))
