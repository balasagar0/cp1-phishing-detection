"""R3-09 comparison on the SAME SIMULATED test bundles that train_fusion.py and eval_window.py report on (same seed, message split and draw order).
  python src/eval_comparison.py        (needs data/processed/pool_*.csv and models/fusion_model.joblib, both from run_all.sh)
Rows, all at the alert line 0.5, with 95% bootstrap intervals over bundles:
  1. single-channel: alert if any event >= 0.5
  2. parallel multi-channel: the fusion recipe trained WITHOUT link and timing features, on the whole bundle (retrained here exactly as
     train_fusion.py trains it: same data, same settings, same seed)
  3. the correlation model on the whole bundle (pools events up to 72 hours apart)
  4. the deployed engine: 60-minute windows, a lone event = its detector score, the bundle takes its highest window
  5. (not evaluated) the old patent draft's noisy-OR score: the owner decided on 7 Nov 2026 that the patent will be written from this build instead
The real-bundle half of R3-09 is blocked on R2-10. Writes reports/comparison_metrics.json."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *
from fusion import *
import joblib
from sklearn.ensemble import HistGradientBoostingClassifier

PROC = ROOT / "data" / "processed"
raw = {c: pd.read_csv(PROC / f"pool_{c}.csv") for c in CH}
rng = np.random.default_rng(SEED)
parts = {"train": {}, "val": {}, "test": {}}          # identical to train_fusion.py: messages are split 50/20/30
for c, df in raw.items():
    df = df.sample(frac=1, random_state=SEED); a, b = int(.5 * len(df)), int(.7 * len(df))
    for name, d in (("train", df.iloc[:a]), ("val", df.iloc[a:b]), ("test", df.iloc[b:])):
        parts[name][c] = {0: d.score[d.label == 0].values, 1: d.score[d.label == 1].values}
sets = {"train": simulate(parts["train"], 24000, rng), "val": simulate(parts["val"], 8000, rng), "test": simulate(parts["test"], 12000, rng)}   # same draw order
X = {k: np.stack([bundle_features(e) for e, _, _ in v]) for k, v in sets.items()}; Y = {k: np.array([y for _, y, _ in v]) for k, v in sets.items()}
test, val = sets["test"], sets["val"]; y = Y["test"]; typ = np.array([t for _, _, t in test])
mx = np.array([max(e["score"] for e in b[0]) for b in test])

keep = [i for i in range(len(FEATURE_NAMES)) if i not in CORR_COLS]
mk = lambda: HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, max_depth=5, min_samples_leaf=40, l2_regularization=1.0, early_stopping=True, random_state=SEED)
nocorr = mk().fit(X["train"][:, keep], Y["train"])                       # train_fusion.py's 'nocorr' model, rebuilt (it is not saved there)
p_parallel = nocorr.predict_proba(X["test"][:, keep])[:, 1]
whole = joblib.load(MODELS / "fusion_model.joblib")["model"].predict_proba(X["test"])[:, 1]
F = Fusion(MODELS / "fusion_model.joblib")


def engine(bundles, window=DEFAULT_WINDOW_MIN):
    rows, owner = [], []
    for i, b in enumerate(bundles):
        for g in time_windows(b[0], window): rows.append(bundle_features([b[0][j] for j in g])); owner.append(i)
    p = F.model.predict_proba(np.stack(rows))[:, 1]; r = np.zeros(len(bundles)); np.maximum.at(r, owner, p); return r


def boot(yv, p, thr=.5, B=300, seed=SEED):
    r = np.random.default_rng(seed); pred = (p >= thr).astype(int); f1s, fprs = [], []
    for _ in range(B):
        i = r.integers(0, len(yv), len(yv)); yy, pp = yv[i], pred[i]
        tp, fp, fn, tn = ((pp == 1) & (yy == 1)).sum(), ((pp == 1) & (yy == 0)).sum(), ((pp == 0) & (yy == 1)).sum(), ((pp == 0) & (yy == 0)).sum()
        pr, rc = tp / max(tp + fp, 1), tp / max(tp + fn, 1); f1s.append(2 * pr * rc / max(pr + rc, 1e-9)); fprs.append(fp / max(fp + tn, 1))
    q = lambda v: [round(float(np.percentile(v, 2.5)), 4), round(float(np.percentile(v, 97.5)), 4)]
    return {"f1": q(f1s), "false_positive_rate": q(fprs)}


rows = {"single_channel": ("Single-channel: alert if any event >= 0.5", mx), "parallel_multichannel": ("Parallel multi-channel: fusion without link and timing features, whole bundle", p_parallel),
        "whole_bundle_model": ("Correlation model on the whole bundle (pools up to 72 h)", whole), "deployed_engine_60min": ("Deployed engine: 60-minute windows (what the API does)", engine(test))}
try:
    import campaign_formula as CF
    patent = CF.evaluate(val, test, time_windows, DEFAULT_WINDOW_MIN) if CF.PARAMETERS_FROM_SPEC else None
except Exception as ex:
    patent = None
hard = (typ == "attack_linked") & (mx < .5)
res = {"title": "SIMULATED bundles (12,000 test bundles; events are real held-out messages, links are constructed)", "alert_line": 0.5, "n_bundles": len(test), "rows": {}}
for k, (name, p) in rows.items():
    res["rows"][k] = {"name": name, **binary_metrics(y, p, .5), "ci95": boot(y, p), "hard_campaigns_flagged": round(float((p[hard] >= .5).mean()), 4) if hard.any() else None}
if patent:
    res["rows"]["patent_noisy_or"] = {"name": "Patent noisy-OR campaign score on the same 60-minute windows (parameters chosen on validation bundles)", **binary_metrics(y, patent["risk"], patent["threshold"]),
                                      "ci95": boot(y, patent["risk"], patent["threshold"]), "threshold": patent["threshold"], "parameters": patent["parameters"],
                                      "hard_campaigns_flagged": round(float((patent["risk"][hard] >= patent["threshold"]).mean()), 4) if hard.any() else None}
else:
    res["rows"]["patent_noisy_or"] = {"name": "Patent noisy-OR campaign score", "status": "not evaluated: the owner decided on 7 Nov 2026 that the patent will be written from this build; the old draft's noisy-OR method and its generated numbers are not used"}
res["hard_campaigns"] = {"n": int(hard.sum()), "definition": "simulated linked attacks where every event scores below 0.5"}
res["real_bundles"] = "blocked on R2-10: 0 real bundles collected"
save_json(res, REPORTS / "comparison_metrics.json")
for k, r in res["rows"].items():
    print(f"{k:<24}", {x: r.get(x) for x in ("precision", "recall", "f1", "false_positive_rate")} if "f1" in r else r.get("status"))
