"""Trains the correlation model on simulated bundles (see fusion.py) and measures it against single-channel alerting."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *
from fusion import *
import joblib
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

PROC = ROOT / "data" / "processed"
raw = {c: pd.read_csv(PROC / f"pool_{c}.csv") for c in CH}
rng = np.random.default_rng(SEED)
parts = {"train": {}, "val": {}, "test": {}}          # split MESSAGES 50/20/30 so no message is shared between bundle sets
for c, df in raw.items():
    df = df.sample(frac=1, random_state=SEED); a, b = int(.5 * len(df)), int(.7 * len(df))
    for name, d in (("train", df.iloc[:a]), ("val", df.iloc[a:b]), ("test", df.iloc[b:])):
        parts[name][c] = {0: d.score[d.label == 0].values, 1: d.score[d.label == 1].values}
sets = {"train": simulate(parts["train"], 24000, rng), "val": simulate(parts["val"], 8000, rng), "test": simulate(parts["test"], 12000, rng)}
XY = {k: (np.stack([bundle_features(e) for e, _, _ in v]), np.array([y for _, y, _ in v]), np.array([t for _, _, t in v]),
          np.array([max(x["score"] for x in e) for e, _, _ in v])) for k, v in sets.items()}
mk = lambda: HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, max_depth=5, min_samples_leaf=40, l2_regularization=1.0, early_stopping=True, random_state=SEED)
keep = [i for i in range(len(FEATURE_NAMES)) if i not in CORR_COLS]
full = mk().fit(XY["train"][0], XY["train"][1]); nocorr = mk().fit(XY["train"][0][:, keep], XY["train"][1])
pv, pt = full.predict_proba(XY["val"][0])[:, 1], full.predict_proba(XY["test"][0])[:, 1]
pv_n, pt_n = nocorr.predict_proba(XY["val"][0][:, keep])[:, 1], nocorr.predict_proba(XY["test"][0][:, keep])[:, 1]
yv, yt, tt, mt = XY["val"][1], XY["test"][1], XY["test"][2], XY["test"][3]
base_fpr = float(((XY["val"][3] >= .5) & (yv == 0)).sum() / (yv == 0).sum())          # false-positive rate of "alert if any event >= 0.5"
thr = threshold_at_fpr(yv, pv, base_fpr); thr_n = threshold_at_fpr(yv, pv_n, base_fpr)    # fusion thresholds matched to that FPR (chosen on validation bundles)
res = {"assumptions": ASSUMPTIONS, "n_bundles": {k: len(v) for k, v in sets.items()}, "positive_share_test": round(float(yt.mean()), 3),
       "single_channel_alert_any_event_ge_0.5": binary_metrics(yt, mt, .5),
       "fusion_at_matched_fpr": binary_metrics(yt, pt, thr), "fusion_without_correlation_features_at_matched_fpr": binary_metrics(yt, pt_n, thr_n),
       "fusion_at_0.5": binary_metrics(yt, pt, .5), "matched_fpr_target": round(base_fpr, 4),
       "auc": {"single_channel_max_score": round(float(roc_auc_score(yt, mt)), 4), "fusion": round(float(roc_auc_score(yt, pt)), 4), "fusion_without_correlation_features": round(float(roc_auc_score(yt, pt_n)), 4)}}
hard = (tt == "attack_linked") & (mt < .5)
res["campaigns_missed_by_every_single_channel_filter"] = {"n": int(hard.sum()), "share_of_linked_attacks": round(float(hard.sum() / (tt == "attack_linked").sum()), 4),
    "caught_by_fusion": round(float((pt[hard] >= thr).mean()), 4) if hard.any() else None, "caught_by_fusion_without_correlation_features": round(float((pt_n[hard] >= thr_n).mean()), 4) if hard.any() else None}
res["flag_rate_by_bundle_type_fusion"] = {t: round(float((pt[tt == t] >= thr).mean()), 4) for t in sorted(set(tt))}
res["flag_rate_by_bundle_type_single_channel"] = {t: round(float((mt[tt == t] >= .5).mean()), 4) for t in sorted(set(tt))}
joblib.dump({"model": full, "meta": {"operating_threshold_matched_fpr": round(thr, 4), "feature_names": FEATURE_NAMES, "assumptions": ASSUMPTIONS, "trained_on": "simulated bundles"}}, MODELS / "fusion_model.joblib", compress=3)
save_json(res, REPORTS / "fusion_metrics.json")
for k in ("single_channel_alert_any_event_ge_0.5", "fusion_at_matched_fpr", "fusion_without_correlation_features_at_matched_fpr"):
    m = res[k]; print(k, {x: m[x] for x in ("precision", "recall", "f1", "false_positive_rate")})
print("auc", res["auc"]); print("hard campaigns", res["campaigns_missed_by_every_single_channel_filter"]); print("flag rate fusion", res["flag_rate_by_bundle_type_fusion"]); print("flag rate single", res["flag_rate_by_bundle_type_single_channel"])
