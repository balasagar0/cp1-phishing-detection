"""Evaluates the time window and the single-event rule on the SAME simulated test bundles that train_fusion.py reports on
(same seed, same message split, same draw order). Needs data/processed/pool_*.csv and models/fusion_model.joblib (both made by run_all.sh).
Writes reports/window_metrics.json. The default window and the single-event rule were fixed before this evaluation was first run;
the other window sizes are listed for information and were not used to pick anything."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *
from fusion import *
import joblib

PROC = ROOT / "data" / "processed"
raw = {c: pd.read_csv(PROC / f"pool_{c}.csv") for c in CH}
rng = np.random.default_rng(SEED)
parts = {"train": {}, "val": {}, "test": {}}          # identical to train_fusion.py: messages are split 50/20/30
for c, df in raw.items():
    df = df.sample(frac=1, random_state=SEED); a, b = int(.5 * len(df)), int(.7 * len(df))
    for name, d in (("train", df.iloc[:a]), ("val", df.iloc[a:b]), ("test", df.iloc[b:])):
        parts[name][c] = {0: d.score[d.label == 0].values, 1: d.score[d.label == 1].values}
sets = {"train": simulate(parts["train"], 24000, rng), "val": simulate(parts["val"], 8000, rng), "test": simulate(parts["test"], 12000, rng)}   # same draw order as train_fusion.py
test = sets["test"]
y = np.array([b[1] for b in test]); typ = np.array([b[2] for b in test]); mx = np.array([max(e["score"] for e in b[0]) for b in test])

F = Fusion(MODELS / "fusion_model.joblib"); raw_model = joblib.load(MODELS / "fusion_model.joblib")["model"]
whole = raw_model.predict_proba(np.stack([bundle_features(b[0]) for b in test]))[:, 1]          # the model on the whole bundle: what the correlation rows of results.md report


def engine(window):
    """Risk of each test bundle under the engine: every time window is scored on its own (a lone event = its detector score), the bundle takes the highest."""
    rows, owner = [], []
    for i, b in enumerate(test):
        for g in time_windows(b[0], window):
            rows.append(bundle_features([b[0][j] for j in g])); owner.append(i)
    p = F.model.predict_proba(np.stack(rows))[:, 1]
    r = np.zeros(len(test)); np.maximum.at(r, owner, p)
    return r


W0 = DEFAULT_WINDOW_MIN; WINDOWS = [15, 30, 60, 120, 240, 1440]
risk = {w: engine(w) for w in WINDOWS}; risk_default = engine(W0); risk_nowin = engine(None)
res = {"default_window_minutes": W0, "n_bundles": len(test), "alert_line": 0.5,
       "single_channel_alert_any_event_ge_0.5": binary_metrics(y, mx, .5),
       "whole_bundle_model_at_0.5": binary_metrics(y, whole, .5),
       "engine_no_window_at_0.5": binary_metrics(y, risk_nowin, .5),
       "engine_by_window_at_0.5": {str(w): binary_metrics(y, risk[w], .5) for w in WINDOWS},
       "engine_default_window_at_0.5": binary_metrics(y, risk_default, .5)}
fits = lambda t: round(float(np.mean([len(time_windows(b[0], W0)) == 1 for b, tt in zip(test, typ) if tt == t])), 4)
res["share_of_bundles_that_fit_in_one_default_window"] = {t: fits(t) for t in sorted(set(typ))}
res["flag_rate_by_bundle_type_at_0.5"] = {k: {t: round(float((v[typ == t] >= .5).mean()), 4) for t in sorted(set(typ))} for k, v in
                                          (("single_channel", mx), ("whole_bundle_model", whole), ("engine_default_window", risk_default))}
hard = (typ == "attack_linked") & (mx < .5)
res["campaigns_missed_by_every_single_channel_filter"] = {"n": int(hard.sum()), "caught_whole_bundle_model_at_0.5": round(float((whole[hard] >= .5).mean()), 4) if hard.any() else None,
                                                          "caught_engine_default_window_at_0.5": round(float((risk_default[hard] >= .5).mean()), 4) if hard.any() else None}
save_json(res, REPORTS / "window_metrics.json")
for k in ("single_channel_alert_any_event_ge_0.5", "whole_bundle_model_at_0.5", "engine_no_window_at_0.5", "engine_default_window_at_0.5"):
    m = res[k]; print(f"{k:<42}", {x: round(m[x], 4) for x in ("precision", "recall", "f1", "false_positive_rate", "roc_auc")})
print("by window:", {w: round(m["f1"], 4) for w, m in res["engine_by_window_at_0.5"].items()})
print("fit in one window:", res["share_of_bundles_that_fit_in_one_default_window"]); print("flag rates:", res["flag_rate_by_bundle_type_at_0.5"]); print("hard campaigns:", res["campaigns_missed_by_every_single_channel_filter"])
