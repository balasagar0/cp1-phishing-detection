"""EMAIL channel (FINAL, 'robust'): numbers masked + cross-corpus vocabulary filter, TF-IDF 1-2 grams + logistic regression.
Why it exists: the plain pipeline (train_email_plain.py) scores ~99% on a pooled random split, but its strongest features are
corpus fingerprints ('enron', 'vince', '2004', 'opensuse' ...). Here a term may only be used if it occurs in >=5 emails of
at least two different corpora, and digits/years are masked. Selection between plain and robust is made on leave-one-corpus-out.
USE_EXTRA_CORPORA adds the Nazario, SpamAssassin and Ling corpora (src/email_corpora.py, fetched by download_email_extra.sh). It stays False
unless the Phase 3 candidate passes the adoption rule (src/eval_email_candidates.py); with False this script is v2's recipe.
Importable: load_email, Feat and fit_lr are used by the candidate evaluation."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *
import joblib
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

T0 = time.time()
def log(*a): print(f"[{time.time()-T0:6.0f}s]", *a, flush=True)
TOKEN = r"(?u)\b\w\w+\b|[$€£!]"
MIN_DOCS_PER_SOURCE, MAX_FEATURES = 5, 200_000
USE_EXTRA_CORPORA = False
POOL_PER_CLASS = 1500            # held-out scores kept per class per corpus for the correlation simulation (fewer if a corpus has fewer)


def load_email(extra=None, cleaner=None):
    """The email corpora, cleaned (numbers masked), short texts dropped, de-duplicated. extra: add the three extra corpora
    (default USE_EXTRA_CORPORA). cleaner: the text cleaner (default common.clean_text; the candidate evaluation passes v2's for comparison)."""
    extra = USE_EXTRA_CORPORA if extra is None else extra; cleaner = cleaner or clean_text
    c = pd.read_csv(RAW / "CEAS_08.csv", usecols=["subject", "body", "label"])
    e = pd.read_csv(RAW / "enron_spam_data.csv")
    f = pd.read_csv(RAW / "fraud_email.csv").dropna(subset=["Text"])
    parts = [
        pd.DataFrame({"source": "CEAS_08", "raw": (c.subject.fillna("") + " . " + c.body.fillna("")).values, "label": c.label.astype(int).values}),
        pd.DataFrame({"source": "Enron", "raw": (e.Subject.fillna("") + " . " + e.Message.fillna("")).values, "label": (e["Spam/Ham"] == "spam").astype(int).values}),
        pd.DataFrame({"source": "FraudEmail", "raw": f.Text.values, "label": f.Class.astype(int).values}),
    ]
    if extra:
        from email_corpora import load_extra
        parts.append(load_extra()[["source", "raw", "label"]])
    df = pd.concat(parts, ignore_index=True)
    df["text"] = df.raw.map(lambda t: cleaner(t, mask_numbers=True)); df = df.drop(columns="raw")
    df = df[df.text.str.len() >= 25]
    df, st = dedupe(df, "text", "label")
    return df.reset_index(drop=True), st


class Feat:
    """counts -> keep only terms present in >= min_sources corpora -> sublinear TF-IDF (all fitted on training emails only)"""
    def __init__(self, train, min_sources):
        self.cv = CountVectorizer(lowercase=True, strip_accents="unicode", ngram_range=(1, 2), min_df=3, max_df=0.8,
                                  max_features=400_000, token_pattern=TOKEN, dtype=np.int32)
        C = self.cv.fit_transform(train.text).tocsr()
        present = np.zeros(C.shape[1], dtype=int)
        for s in train.source.unique():
            rows = np.where(train.source.values == s)[0]
            present += (np.asarray((C[rows] > 0).sum(axis=0)).ravel() >= MIN_DOCS_PER_SOURCE).astype(int)
        keep = np.where(present >= min_sources)[0]
        tot = np.asarray((C > 0).sum(axis=0)).ravel()
        if len(keep) > MAX_FEATURES: keep = np.sort(keep[np.argsort(-tot[keep])[:MAX_FEATURES]])
        self.keep, self.n_before = keep, C.shape[1]
        self.terms = self.cv.get_feature_names_out()[keep]
        Ck = C[:, keep]; self.tf = TfidfTransformer(sublinear_tf=True).fit(Ck)
        self.Xtrain = self.tf.transform(Ck).astype(np.float32)
    def transform(self, texts):
        return self.tf.transform(self.cv.transform(texts)[:, self.keep]).astype(np.float32)


def fit_lr(X, y, C): return LogisticRegression(C=C, solver="liblinear", class_weight="balanced", max_iter=300).fit(X, y)


def main():
    df, dd = load_email()
    log("loaded", len(df), "emails after cleaning (numbers masked) + dedupe;", dd)
    counts = df.groupby(["source", "label"]).size().unstack(fill_value=0); log("\n" + counts.to_string())
    strat = df.source + "_" + df.label.astype(str)
    tr, rest = train_test_split(df, test_size=0.2, stratify=strat, random_state=SEED)
    va, te = train_test_split(rest, test_size=0.5, stratify=rest.source + "_" + rest.label.astype(str), random_state=SEED)

    F = Feat(tr, min_sources=2); Xva, Xte = F.transform(va.text), F.transform(te.text)
    log(f"features: {F.n_before} candidate terms -> {len(F.terms)} kept (present in >=2 corpora)")
    vs = {}
    for C in (1, 4, 16):
        m = fit_lr(F.Xtrain, tr.label, C); vs[C] = binary_metrics(va.label, m.predict_proba(Xva)[:, 1])
        log(f"C={C}: val F1={vs[C]['f1']} AUC={vs[C].get('roc_auc')}")
    bestC = max(vs, key=lambda c: vs[c]["f1"]); clf = fit_lr(F.Xtrain, tr.label, bestC)
    pva, pte = clf.predict_proba(Xva)[:, 1], clf.predict_proba(Xte)[:, 1]
    thr1 = threshold_at_fpr(va.label, pva, 0.01)
    res = {"variant": "robust", "data": {"dedupe": dd, "counts": {s: {int(k): int(v) for k, v in r.items()} for s, r in counts.iterrows()},
           "split": {"train": len(tr), "val": len(va), "test": len(te)}, "candidate_terms": int(F.n_before), "kept_terms": int(len(F.terms))},
           "chosen_C": bestC, "validation_by_C": vs, "pooled_test": binary_metrics(te.label, pte), "pooled_test_ci95": bootstrap_ci(te.label, pte),
           "pooled_test_at_1pct_fpr": binary_metrics(te.label, pte, thr1)}
    res["pooled_test_per_source"] = {s: binary_metrics(g.label, pte[te.index.get_indexer(g.index)]) for s, g in te.groupby("source")}
    log("pooled test:", res["pooled_test"])

    loco, pool = {}, []
    for s in sorted(df.source.unique()):
        a, b = df[df.source != s], df[df.source == s]
        Fa = Feat(a, min_sources=2); m = fit_lr(Fa.Xtrain, a.label, bestC)
        pb = m.predict_proba(Fa.transform(b.text))[:, 1]
        loco[s] = binary_metrics(b.label, pb)
        cap = min(POOL_PER_CLASS, int(b.label.value_counts().min()))        # 1,500 per class per corpus (the same rows as v2's when every class has 1,500)
        smp = b.assign(score=pb).groupby("label", group_keys=False).sample(cap, random_state=SEED)
        pool.append(pd.DataFrame({"source": s, "label": smp.label.values, "score": smp.score.values, "text": smp.text.str[:500].values}))
        log(f"LOCO held-out={s}: F1={loco[s]['f1']} recall={loco[s]['recall']} precision={loco[s]['precision']} FPR={loco[s]['false_positive_rate']} AUC={loco[s].get('roc_auc')}")
    res["leave_one_corpus_out"] = loco
    PROC = ROOT / "data" / "processed"; PROC.mkdir(parents=True, exist_ok=True)
    pd.concat(pool).to_csv(PROC / "pool_email.csv", index=False)   # scores from models that never saw that corpus

    co = clf.coef_[0]; order = np.argsort(co)
    res["top_terms_malicious"] = [(F.terms[i], round(float(co[i]), 3)) for i in order[::-1][:30]]
    res["top_terms_legit"] = [(F.terms[i], round(float(co[i]), 3)) for i in order[:30]]
    log("top malicious:", [t for t, _ in res["top_terms_malicious"][:20]]); log("top legit:", [t for t, _ in res["top_terms_legit"][:20]])

    # deployed model: same recipe on every email; stored as a plain TfidfVectorizer with the filtered vocabulary
    Fall = Feat(df, min_sources=2)
    vf = TfidfVectorizer(vocabulary=list(Fall.terms), lowercase=True, strip_accents="unicode", ngram_range=(1, 2), sublinear_tf=True,
                         token_pattern=TOKEN, dtype=np.float32).fit(df.text)
    final = fit_lr(vf.transform(df.text), df.label, bestC)
    joblib.dump({"vectorizer": vf, "clf": final, "meta": {"channel": "email", "variant": "robust", "mask_numbers": True, "C": bestC, "n_train": len(df),
                 "operating_threshold_1pct_fpr": round(thr1, 4), "sources": sorted(df.source.unique())}}, MODELS / "email_model.joblib", compress=3)
    save_json(res, REPORTS / "email_metrics.json"); log("saved robust email model + metrics")


if __name__ == "__main__":
    main()
