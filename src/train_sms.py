"""SMS channel: 3-class (ham / spam / smishing) TF-IDF word+char logistic regression on the LSDST smishing corpus.
External domain-shift check on a second, independently assembled SMS collection."""
import sys, time, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline, make_union
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_predict
from sklearn.metrics import f1_score, precision_recall_fscore_support

T0 = time.time()
def log(*a): print(f"[{time.time()-T0:6.0f}s]", *a, flush=True)
LABELS = ["ham", "spam", "smishing"]
SM = RAW / "smish"


def clean_sms(t):
    t = str(t).replace("\ufffd", " ")
    t = re.sub(r"[\x00-\x1f]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def make_pipe(C):
    feats = make_union(
        TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, token_pattern=r"(?u)\b\w+\b|[£$€!%@]", dtype=np.float32),
        TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=3, sublinear_tf=True, dtype=np.float32))
    return make_pipeline(feats, LogisticRegression(C=C, class_weight="balanced", max_iter=3000))


d = pd.read_csv(SM / "hcphap_lsdst.csv", encoding="utf-8", on_bad_lines="skip")
d["label"] = d.LABEL.astype(str).str.strip().str.lower().map({"ham": 0, "spam": 1, "smishing": 2})
d["text"] = d.TEXT.map(clean_sms)
d = d[d.label.notna() & (d.text.str.len() >= 3)].copy(); d["label"] = d.label.astype(int)
d, dd = dedupe(d[["text", "label"]], "text", "label"); d = d.reset_index(drop=True)
cnt = d.label.value_counts().sort_index().to_dict()
log("LSDST after cleaning + dedupe:", len(d), dd, {LABELS[k]: v for k, v in cnt.items()})

tr, te = train_test_split(d, test_size=0.2, stratify=d.label, random_state=SEED)
cv = StratifiedKFold(5, shuffle=True, random_state=SEED)
cvs = {}
for C in (2, 8, 32, 128):
    oof = cross_val_predict(make_pipe(C), tr.text, tr.label, cv=cv, method="predict_proba")
    cvs[C] = round(float(f1_score(tr.label, oof.argmax(1), average="macro")), 4)
    log(f"C={C}: 5-fold macro-F1 on train = {cvs[C]}")
bestC = max(cvs, key=cvs.get)

pipe = make_pipe(bestC).fit(tr.text, tr.label)
P = pipe.predict_proba(te.text)
pr, rc, f1, sup = precision_recall_fscore_support(te.label, P.argmax(1), labels=[0, 1, 2], zero_division=0)
res = {"data": {"dedupe": dd, "class_counts": {LABELS[k]: int(v) for k, v in cnt.items()}, "split": {"train": len(tr), "test": len(te)}},
       "chosen_C": bestC, "cv_macro_f1_by_C": cvs,
       "test_3class": {"macro_f1": round(float(f1.mean()), 4),
                       "per_class": {LABELS[i]: {"precision": round(float(pr[i]), 4), "recall": round(float(rc[i]), 4), "f1": round(float(f1[i]), 4), "support": int(sup[i])} for i in range(3)}}}
PROC = ROOT / "data" / "processed"; PROC.mkdir(parents=True, exist_ok=True)
pd.DataFrame({"label3": te.label.values, "label": (te.label > 0).astype(int).values, "score": 1 - P[:, 0], "text": te.text.str[:300].values}).to_csv(PROC / "pool_sms.csv", index=False)
y_sm = (te.label == 2).astype(int).values; p_sm = P[:, 2]
y_un = (te.label > 0).astype(int).values; p_un = 1 - P[:, 0]
res["test_smishing_vs_rest"] = binary_metrics(y_sm, p_sm); res["test_smishing_vs_rest_ci95"] = bootstrap_ci(y_sm, p_sm)
res["test_unwanted_vs_ham"] = binary_metrics(y_un, p_un); res["test_unwanted_vs_ham_ci95"] = bootstrap_ci(y_un, p_un)
log("smishing vs rest (test):", res["test_smishing_vs_rest"], res["test_smishing_vs_rest_ci95"])
log("unwanted vs ham (test):", res["test_unwanted_vs_ham"])

# 5-fold out-of-fold estimate on all data (more stable than a single 20% split)
oof = cross_val_predict(make_pipe(bestC), d.text, d.label, cv=cv, method="predict_proba")
res["oof5_smishing_vs_rest"] = binary_metrics((d.label == 2).astype(int), oof[:, 2])
res["oof5_unwanted_vs_ham"] = binary_metrics((d.label > 0).astype(int), 1 - oof[:, 0])
log("OOF smishing:", res["oof5_smishing_vs_rest"])

# external domain-shift check: model fitted on LSDST only, tested on a different SMS collection (texts seen in LSDST removed)
try:
    c = pd.read_csv(SM / "shaghayegh_combined.csv", encoding="utf-8", on_bad_lines="skip"); c.columns = ["message", "spam", "smish"]
    c["spam"] = c.spam.astype(str).str.strip()
    c = c[c.spam.isin(["0", "1", "Smishing"])].copy()
    c["y"] = (c.spam != "0").astype(int); c["text"] = c.message.map(clean_sms)
    c = c[c.text.str.len() >= 3]
    seen = set(d.text.map(norm_key))
    c = c[~c.text.map(norm_key).isin(seen)]
    c, st = dedupe(c[["text", "y"]], "text", "y")
    full = make_pipe(bestC).fit(d.text, d.label)
    pe = 1 - full.predict_proba(c.text)[:, 0]
    res["external_combined_unwanted_vs_ham"] = binary_metrics(c.y, pe)
    res["external_combined_info"] = {"dedupe": st, "note": "different region/preprocessing; digits and punctuation often stripped; label = spam-or-smishing vs ham"}
    log("external check:", res["external_combined_unwanted_vs_ham"])
except Exception as ex:
    log("external check skipped:", ex)

final = make_pipe(bestC).fit(d.text, d.label)
joblib.dump({"pipe": final, "labels": LABELS, "meta": {"channel": "sms", "C": bestC, "n_train": len(d)}}, MODELS / "sms_model.joblib", compress=3)
save_json(res, REPORTS / "sms_metrics.json"); log("saved sms model + metrics")
