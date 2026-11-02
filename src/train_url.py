"""URL channel (v2).
 (A) LIVE model  : raw URL string -> char 3-5-gram hashing + TF-IDF (+ 3 domain-popularity flags) + logistic regression.
                   Ablation on one host-grouped split: (a) n-grams only [v1], (b) + popularity flags, (c) + legitimate-login training URLs [final].
 (B) BENCHMARK   : 111 pre-computed features (Vrbancic et al.) -> gradient boosting (offline only: some features need DNS/WHOIS/SSL lookups)."""
import sys, time, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import *
from url_features import *
import joblib
from scipy import sparse
from sklearn.feature_extraction.text import HashingVectorizer, TfidfTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier

T0 = time.time()
def log(*a): print(f"[{time.time()-T0:6.0f}s]", *a, flush=True)
NF, N_MAX, C_URL = 2 ** 20, 260_000, 10          # C=10 was chosen on a validation split in the first version
HV = dict(analyzer="char", ngram_range=(3, 5), n_features=NF, alternate_sign=False, norm=None, lowercase=False, dtype=np.float32)
def fit_lr(X, y, C): return LogisticRegression(C=C, solver="liblinear", max_iter=300).fit(X, y)

rm = load_rank_map(RAW / "opendns_top10k.txt"); log("popularity list:", len(rm), "registered domains")
u = pd.read_csv(RAW / "url_strings.csv"); u["y"] = (u.label == "bad").astype(int)
u["c"] = u.url.map(canon); u = u[u.c.str.len() >= 4]
u, dd = dedupe(u[["c", "y"]], "c", "y")
if len(u) > N_MAX: u, _ = train_test_split(u, train_size=N_MAX, stratify=u.y, random_state=SEED)
u = u.reset_index(drop=True); u["host"] = u.c.map(host_of)
hv = HashingVectorizer(**HV); X = hv.transform(u.c).tocsr(); y = u.y.values; R = rep_matrix(u.host.values, rm)
log("URLs:", len(u), "| bad share", round(float(y.mean()), 3), "| hosts", u.host.nunique(), "| share of URLs on a top-10k domain: good",
    round(float(R[y == 0][:, 2].mean()), 3), "bad", round(float(R[y == 1][:, 2].mean()), 3))
tr_i, te_i = next(GroupShuffleSplit(1, test_size=0.2, random_state=SEED).split(X, y, groups=u.host.values))

rng = np.random.default_rng(SEED)
all_dom = np.array(sorted(rm)); rng.shuffle(all_dom)
hold_dom, train_dom = all_dom[:1000], all_dom[1000:]
aug_urls = make_login_urls(rng.choice(train_dom, 6000, replace=False), 2, rng)               # legit-login URLs on popular domains (training only)
hold_urls = make_login_urls(hold_dom, 3, rng)                                                # same kind of URL on 1,000 *different* domains (test only)
brands = sorted({d.split(".")[0] for d in list(rm)[:600] if d.split(".")[0].isalpha() and len(d.split(".")[0]) >= 4})
probe_urls = make_brand_probes(brands, 2000, rng)                                            # brand-impersonation URLs on look-alike hosts (test only)
log("constructed sets: train login URLs", len(aug_urls), "| held-out-domain login URLs", len(hold_urls), "| brand-impersonation probes", len(probe_urls))

def design(tf, counts, rep, use_rep):
    M = tf.transform(counts)
    return sparse.hstack([M, rep]).tocsr() if use_rep else M

def fit_variant(idx, use_rep, aug=None):
    Xc, Rc, yy = X[idx], R[idx], y[idx]
    if aug:
        Xa = hv.transform(aug).tocsr(); Ra = rep_matrix([host_of(a) for a in aug], rm)
        Xc, Rc, yy = sparse.vstack([Xc, Xa]).tocsr(), sparse.vstack([Rc, Ra]).tocsr(), np.concatenate([yy, np.zeros(len(aug), dtype=int)])
    tf = TfidfTransformer(sublinear_tf=True).fit(Xc)
    return {"tf": tf, "clf": fit_lr(design(tf, Xc, Rc, use_rep), yy, C_URL), "use_rep": use_rep}

def score_urls(v, urls):
    return v["clf"].predict_proba(design(v["tf"], hv.transform(urls).tocsr(), rep_matrix([host_of(c) for c in urls], rm), v["use_rep"]))[:, 1]

top_te = np.asarray(R[te_i][:, 2].todense()).ravel() > 0
abl, variants = {}, {}
for name, use_rep, aug in (("a_ngrams_only", False, None), ("b_plus_popularity_flags", True, None), ("c_plus_login_training_urls_FINAL", True, aug_urls)):
    v = fit_variant(tr_i, use_rep, aug); variants[name] = v
    pt = score_urls(v, []) if False else v["clf"].predict_proba(design(v["tf"], X[te_i], R[te_i], use_rep))[:, 1]
    m = binary_metrics(y[te_i], pt); bad_top = (y[te_i] == 1) & top_te
    abl[name] = {"grouped_test": m, "recall_on_bad_urls_hosted_on_top10k_domains": {"n": int(bad_top.sum()), "recall": round(float((pt[bad_top] >= .5).mean()), 4) if bad_top.any() else None},
                 "false_positive_rate_on_login_urls_of_1000_held_out_popular_domains": round(float((score_urls(v, hold_urls) >= .5).mean()), 4),
                 "detection_rate_on_2000_brand_impersonation_probes": round(float((score_urls(v, probe_urls) >= .5).mean()), 4)}
    log(name, "| F1", m["f1"], "AUC", m.get("roc_auc"), "| login FPR", abl[name]["false_positive_rate_on_login_urls_of_1000_held_out_popular_domains"],
        "| probe detection", abl[name]["detection_rate_on_2000_brand_impersonation_probes"], "| bad-on-top recall", abl[name]["recall_on_bad_urls_hosted_on_top10k_domains"])
fin = variants["c_plus_login_training_urls_FINAL"]; pt = fin["clf"].predict_proba(design(fin["tf"], X[te_i], R[te_i], True))[:, 1]
resA = {"data": {"dedupe": dd, "rows_used": len(u), "bad_share": round(float(y.mean()), 4), "unique_hosts": int(u.host.nunique()),
                 "split": "80/20 grouped by host (no host appears in both train and test)", "train": len(tr_i), "test": len(te_i),
                 "popularity_list_domains": len(rm), "share_of_good_urls_on_top10k_domain": round(float(R[y == 0][:, 2].mean()), 4), "share_of_bad_urls_on_top10k_domain": round(float(R[y == 1][:, 2].mean()), 4),
                 "constructed_sets": {"train_login_urls": len(aug_urls), "held_out_domain_login_urls": len(hold_urls), "brand_impersonation_probes": len(probe_urls)}},
        "ablation": abl, "grouped_test": abl["c_plus_login_training_urls_FINAL"]["grouped_test"], "grouped_test_ci95": bootstrap_ci(y[te_i], pt),
        "popularity_flag_coefficients_top100_top1000_top10000": [round(float(c), 3) for c in fin["clf"].coef_[0][-3:]]}
PROC = ROOT / "data" / "processed"; PROC.mkdir(parents=True, exist_ok=True)
smp = np.random.default_rng(SEED).choice(te_i, 20000, replace=False)
pd.DataFrame({"text": u.c.values[smp], "label": y[smp], "score": fin["clf"].predict_proba(design(fin["tf"], X[smp], R[smp], True))[:, 1]}).to_csv(PROC / "pool_url.csv", index=False)

# deployed model: variant (c) recipe on all rows, login URLs for every popular domain (x2)
dep_aug = make_login_urls(sorted(rm), 2, np.random.default_rng(SEED + 1))
dep = fit_variant(np.arange(len(u)), True, dep_aug)
probes = ["https://www.google.com/search?q=weather", "https://github.com/anthropics", "https://www.paypal.com/signin", "https://en.wikipedia.org/wiki/Phishing",
          "https://www.amazon.in/gp/your-account", "https://accounts.google.com/signin", "https://login.microsoftonline.com/common/oauth2/authorize",
          "http://paypal-secure-login.verify-account.xyz/signin", "http://192.168.4.7/login/index.php", "http://sbi-kyc-update.top/verify-now.php",
          "https://secure-appleid.apple.com.account-verify.ml/login", "http://bit.ly/3xZk9Q"]
resA["sanity_probes_NOT_an_evaluation"] = {p: round(float(s), 3) for p, s in zip(probes, score_urls(dep, [canon(p) for p in probes]))}
log("probes:", resA["sanity_probes_NOT_an_evaluation"])
joblib.dump({"hasher_params": {k: v for k, v in HV.items() if k != "dtype"}, "tfidf": dep["tf"], "clf": dep["clf"], "rank_map": rm, "use_rep": True,
             "meta": {"channel": "url", "version": 2, "C": C_URL, "n_train": len(u) + len(dep_aug)}}, MODELS / "url_string_model.joblib", compress=3)
log("saved deployed URL model")

# ---------------- (B) feature benchmark ----------------
x = pd.read_csv(RAW / "url_features_full.csv"); n0 = len(x)
Xb = x.drop(columns="phishing"); yb = x.phishing.values
h = pd.util.hash_pandas_object(Xb, index=False).values
g = pd.DataFrame({"h": h, "y": yb}); nun = g.groupby("h").y.nunique(); bad = set(nun[nun > 1].index)
keep = (~g.h.isin(bad)) & (~g.h.duplicated())
Xb, yb = Xb[keep.values].reset_index(drop=True), yb[keep.values]
NET = ["time_response", "domain_spf", "asn_ip", "time_domain_activation", "time_domain_expiration", "qty_ip_resolved", "qty_nameservers",
       "qty_mx_servers", "ttl_hostname", "tls_ssl_certificate", "qty_redirects", "url_google_index", "domain_google_index"]
LEX = [c for c in Xb.columns if c not in NET]
tr, te = train_test_split(np.arange(len(Xb)), test_size=0.2, stratify=yb, random_state=SEED)
resB = {"data": {"rows_before": n0, "rows_after": int(len(Xb)), "conflicting_feature_vectors_dropped": len(bad), "n_features_all": Xb.shape[1],
                 "n_features_lexical_only": len(LEX), "network_dependent_features": NET, "split": "stratified 80/20 random (no host info available)"}}
for tag, cols in (("all_features", list(Xb.columns)), ("lexical_only", LEX)):
    m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.1, early_stopping=True, random_state=SEED).fit(Xb.iloc[tr][cols], yb[tr])
    p = m.predict_proba(Xb.iloc[te][cols])[:, 1]; resB[f"hgb_{tag}"] = binary_metrics(yb[te], p)
    joblib.dump({"model": m, "columns": cols}, MODELS / f"url_features_{tag}.joblib", compress=3)
    log(f"HGB {tag}:", resB[f"hgb_{tag}"])
rf = RandomForestClassifier(n_estimators=150, n_jobs=1, random_state=SEED, min_samples_leaf=2).fit(Xb.iloc[tr], yb[tr])
resB["rf_all_features"] = binary_metrics(yb[te], rf.predict_proba(Xb.iloc[te])[:, 1])
imp = pd.Series(rf.feature_importances_, index=Xb.columns).sort_values(ascending=False)
resB["rf_top_features"] = [(k, round(float(v), 4)) for k, v in imp.head(12).items()]
log("RF all:", resB["rf_all_features"])
save_json({"string_model": resA, "feature_benchmark": resB}, REPORTS / "url_metrics.json"); log("saved url models + metrics")
