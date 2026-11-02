"""EMAIL channel BASELINE (plain): TF-IDF 1-2 grams + logistic regression. Kept to show why train_email.py (robust) exists."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import ComplementNB
from sklearn.model_selection import train_test_split

T0 = time.time()
def log(*a): print(f"[{time.time()-T0:6.0f}s]", *a, flush=True)


def load_email():
    c = pd.read_csv(RAW / "CEAS_08.csv", usecols=["subject", "body", "label"])
    e = pd.read_csv(RAW / "enron_spam_data.csv")
    f = pd.read_csv(RAW / "fraud_email.csv").dropna(subset=["Text"])
    parts = [
        pd.DataFrame({"source": "CEAS_08", "raw": (c.subject.fillna("") + " . " + c.body.fillna("")).values, "label": c.label.astype(int).values}),
        pd.DataFrame({"source": "Enron", "raw": (e.Subject.fillna("") + " . " + e.Message.fillna("")).values, "label": (e["Spam/Ham"] == "spam").astype(int).values}),
        pd.DataFrame({"source": "FraudEmail", "raw": f.Text.values, "label": f.Class.astype(int).values}),
    ]
    df = pd.concat(parts, ignore_index=True)
    df["text"] = df.raw.map(clean_text)
    df = df.drop(columns="raw")
    df = df[df.text.str.len() >= 25]
    df, st = dedupe(df, "text", "label")
    return df.reset_index(drop=True), st


def make_vec():
    return TfidfVectorizer(lowercase=True, strip_accents="unicode", ngram_range=(1, 2), min_df=3, max_df=0.8,
                           max_features=200_000, sublinear_tf=True, token_pattern=r"(?u)\b\w\w+\b|[$€£!]", dtype=np.float32)


def fit_lr(X, y, C):
    return LogisticRegression(C=C, solver="liblinear", class_weight="balanced", max_iter=300).fit(X, y)


df, dd = load_email()
log("loaded", len(df), "emails after cleaning + dedupe;", dd)
counts = df.groupby(["source", "label"]).size().unstack(fill_value=0)
log("\n" + counts.to_string())

strat = df.source + "_" + df.label.astype(str)
tr, rest = train_test_split(df, test_size=0.2, stratify=strat, random_state=SEED)
va, te = train_test_split(rest, test_size=0.5, stratify=rest.source + "_" + rest.label.astype(str), random_state=SEED)
log("split sizes train/val/test:", len(tr), len(va), len(te))

vec = make_vec(); Xtr = vec.fit_transform(tr.text); Xva = vec.transform(va.text); Xte = vec.transform(te.text)
log("vectorised; vocab size", len(vec.vocabulary_))

val_scores = {}
for C in (1, 4, 16):
    m = fit_lr(Xtr, tr.label, C); p = m.predict_proba(Xva)[:, 1]
    val_scores[C] = binary_metrics(va.label, p)
    log(f"C={C}: val F1={val_scores[C]['f1']} AUC={val_scores[C].get('roc_auc')}")
bestC = max(val_scores, key=lambda c: val_scores[c]["f1"])
log("chosen C =", bestC)

clf = fit_lr(Xtr, tr.label, bestC)
pva = clf.predict_proba(Xva)[:, 1]; pte = clf.predict_proba(Xte)[:, 1]
thr1 = threshold_at_fpr(va.label, pva, 0.01)
res = {"data": {"dedupe": dd, "counts": {s: {int(k): int(v) for k, v in r.items()} for s, r in counts.iterrows()},
                "split": {"train": len(tr), "val": len(va), "test": len(te)}},
       "chosen_C": bestC, "validation_by_C": val_scores,
       "pooled_test": binary_metrics(te.label, pte),
       "pooled_test_ci95": bootstrap_ci(te.label, pte),
       "pooled_test_at_1pct_fpr": binary_metrics(te.label, pte, thr1)}
res["pooled_test_per_source"] = {s: binary_metrics(g.label, pte[te.index.get_indexer(g.index)]) for s, g in te.groupby("source")}
nb = ComplementNB(alpha=0.3).fit(Xtr, tr.label)
pnb = nb.predict_proba(Xte)[:, 1]
res["baseline_complement_nb_test"] = binary_metrics(te.label, pnb)
log("pooled test:", res["pooled_test"])
log("NB baseline test:", res["baseline_complement_nb_test"])

# leave-one-corpus-out: the number to quote when asked about generalisation
loco = {}
for s in sorted(df.source.unique()):
    a, b = df[df.source != s], df[df.source == s]
    v = make_vec(); Xa = v.fit_transform(a.text); m = fit_lr(Xa, a.label, bestC)
    p = m.predict_proba(v.transform(b.text))[:, 1]
    loco[s] = binary_metrics(b.label, p)
    log(f"LOCO held-out={s}: F1={loco[s]['f1']} recall={loco[s]['recall']} precision={loco[s]['precision']} AUC={loco[s].get('roc_auc')}")
res["leave_one_corpus_out"] = loco

names = vec.get_feature_names_out(); co = clf.coef_[0]
order = np.argsort(co)
res["top_terms_malicious"] = [(names[i], round(float(co[i]), 3)) for i in order[::-1][:30]]
res["top_terms_legit"] = [(names[i], round(float(co[i]), 3)) for i in order[:30]]

# deployed model: same recipe, fitted on every cleaned email
vf = make_vec(); Xall = vf.fit_transform(df.text); final = fit_lr(Xall, df.label, bestC)
joblib.dump({"vectorizer": vf, "clf": final, "meta": {"channel": "email", "C": bestC, "n_train": len(df),
             "operating_threshold_1pct_fpr": round(thr1, 4), "sources": sorted(df.source.unique())}},
            MODELS / "email_model_plain.joblib", compress=3)
save_json(res, REPORTS / "email_metrics_plain.json")
log("saved email model + metrics")
