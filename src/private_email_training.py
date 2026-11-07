"""Privacy-first training path for the account owner's Gmail export (privacy spec of 7 Nov 2026; full account in PRIVACY_AND_ETHICS.md).
  - The public corpora are cleaned and counted as usual. Their n-grams (seen in at least 3 public emails) form the CANDIDATE vocabulary.
  - The .mbox is streamed one message at a time (email_stream.iter_texts, read-only). Each message is cleaned, split into n-grams, and only n-grams
    already in the candidate vocabulary are counted. The text is then dropped. What stays in memory for the run is one row of integer counts per
    email: no text, no headers, no addresses, and no word that appears only in the inbox (it is never counted).
  - Nothing from the inbox is written to disk except the trained model, which is saved with access limited to the current user.
  - No network: nothing here imports a network library, and tests run it with sockets blocked.
  - Nothing is logged except counts.
  - The model vocabulary keeps only terms present (in at least 5 emails) in at least two sources, so every term in it also occurs in public data.
    The model's weights and IDF values are still shaped by the inbox: deleting the .mbox does not remove that influence; retrain without it."""
import hashlib, os, re, subprocess, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from common import clean_text, norm_key
import email_stream

TOKEN = r"(?u)\b\w\w+\b|[$€£!]"                 # the same as src/train_email.py
MIN_DOCS_PER_SOURCE, MAX_FEATURES, MIN_DF, MAX_DF, MAX_CV_FEATURES = 5, 200_000, 3, 0.8, 400_000
PRIVATE = "OwnInbox"


def candidate_vocab(public_texts):
    """CountVectorizer fitted on PUBLIC text only. Returns the vectorizer and the public count matrix."""
    cv = CountVectorizer(lowercase=True, strip_accents="unicode", ngram_range=(1, 2), min_df=MIN_DF, token_pattern=TOKEN, dtype=np.int32)
    return cv, cv.fit_transform(public_texts).tocsr()


def stream_private(paths, cv, extra_texts=(), stats=None, min_chars=25):
    """Count rows for the private emails, one message at a time. extra_texts: synthetic canary emails mixed into the stream (audits and tests only).
    Exact duplicates are dropped by a hash of the normalised text, kept in memory for the run. Returns (CSR matrix, counts)."""
    analyzer, vocab = cv.build_analyzer(), cv.vocabulary_
    stats = stats if stats is not None else email_stream.Stats()
    seen, ind, val, ptr, kept, dup, short = set(), [], [], [0], 0, 0, 0
    def add(text):
        nonlocal kept, dup, short
        t = clean_text(text, mask_numbers=True)
        if len(t) < min_chars: short += 1; return
        k = norm_key(t)
        if k in seen: dup += 1; return
        seen.add(k)
        c = Counter(vocab[g] for g in analyzer(t) if g in vocab)
        ind.extend(c.keys()); val.extend(c.values()); ptr.append(len(ind)); kept += 1
    for text in email_stream.iter_texts(paths, stats):
        add(text); text = None
    for text in extra_texts: add(text)
    X = sparse.csr_matrix((np.asarray(val, dtype=np.int32), np.asarray(ind, dtype=np.int64), np.asarray(ptr, dtype=np.int64)), shape=(kept, len(vocab)))
    return X, {**stats.as_dict(), "kept": kept, "duplicates_dropped": dup, "too_short": short}


class MatrixFeat:
    """train_email.Feat on a count matrix: min_df / max_df / max_features as CountVectorizer applies them, then 'present in >= 5 emails of
    at least `min_sources` sources', capped at MAX_FEATURES by document frequency, then sublinear TF-IDF fitted on the training rows."""
    def __init__(self, X, src, rows, min_sources=2):
        Xt = X[rows]; B = (Xt > 0).astype(np.int32); n = len(rows)
        df = np.asarray(B.sum(0)).ravel(); tf = np.asarray(Xt.sum(0)).ravel()
        cand = np.where((df >= MIN_DF) & (df <= MAX_DF * n))[0]
        if len(cand) > MAX_CV_FEATURES: cand = cand[np.argsort(-tf[cand], kind="stable")[:MAX_CV_FEATURES]]
        present = np.zeros(X.shape[1], dtype=np.int32); s_rows = np.asarray(src)[rows]
        for s in np.unique(s_rows):
            present += (np.asarray(B[np.where(s_rows == s)[0]].sum(0)).ravel() >= MIN_DOCS_PER_SOURCE).astype(np.int32)
        keep = cand[present[cand] >= min_sources]
        if len(keep) > MAX_FEATURES: keep = keep[np.argsort(-df[keep], kind="stable")[:MAX_FEATURES]]
        self.keep = np.sort(keep); self.tf = TfidfTransformer(sublinear_tf=True).fit(Xt[:, self.keep])
        self.Xtrain = self.tf.transform(Xt[:, self.keep]).astype(np.float32)
    def transform(self, Xr): return self.tf.transform(Xr[:, self.keep]).astype(np.float32)


def fit_lr(X, y, C): return LogisticRegression(C=C, solver="liblinear", class_weight="balanced", max_iter=300).fit(X, y)


def text_model(cv, F, clf, meta):
    """A serving model that scores raw text: a TfidfVectorizer with exactly the kept terms (all of them public) and the trained IDF values."""
    inv = np.empty(len(cv.vocabulary_), dtype=object)
    for g, i in cv.vocabulary_.items(): inv[i] = g
    terms = [str(t) for t in inv[F.keep]]
    vf = TfidfVectorizer(vocabulary=terms, lowercase=True, strip_accents="unicode", ngram_range=(1, 2), sublinear_tf=True, token_pattern=TOKEN, dtype=np.float32)
    vf.fit(["placeholder"]); vf.idf_ = F.tf.idf_
    return {"vectorizer": vf, "clf": clf, "meta": meta}


def train_on(public_texts, public_labels, public_sources, paths, C=16, canaries=()):
    """The whole private path in one call: public candidate vocabulary, streamed private rows (plus synthetic canaries, for audits and tests),
    one model on everything. Returns (serving model, stream counts, (X, y, src, cv)). Writes nothing."""
    cv, Xp = candidate_vocab(public_texts)
    Xo, st = stream_private(paths, cv, extra_texts=canaries)
    X = sparse.vstack([Xp, Xo]).tocsr()
    y = np.concatenate([np.asarray(public_labels, dtype=int), np.zeros(Xo.shape[0], dtype=int)])
    src = np.concatenate([np.asarray(public_sources, dtype=object), np.array([PRIVATE] * Xo.shape[0], dtype=object)])
    F = MatrixFeat(X, src, np.arange(X.shape[0])); clf = fit_lr(F.Xtrain, y, C)
    meta = {"channel": "email", "trained_with_private_mail": True, "private_emails": int(Xo.shape[0]), "sources": sorted(set(src.tolist())), "C": C}
    return text_model(cv, F, clf, meta), st, (X, y, src, cv)


def held_out(X, y, src, C, sources, measure, log=print):
    out, preds = {}, {}
    src = np.asarray(src)
    for s in sources:
        tr, te = np.where(src != s)[0], np.where(src == s)[0]
        F = MatrixFeat(X, src, tr); m = fit_lr(F.Xtrain, y[tr], C); p = m.predict_proba(F.transform(X[te]))[:, 1]
        preds[s] = (y[te], p); out[s] = measure(y[te], p); log(f"  held-out {s}: {out[s]}")
    return out, preds


def save_private(model, path):
    """Saves a model trained on private mail with access limited to the current user (icacls on Windows, chmod 600 elsewhere).
    Returns what was done. Encryption is not applied here (Windows Home has no file encryption); see PRIVACY_AND_ETHICS.md."""
    import joblib
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path, compress=3)
    if os.name == "nt":
        user = os.environ.get("USERNAME", "")
        r = subprocess.run(["icacls", str(path), "/inheritance:r", "/grant:r", f"{user}:(R,W,D)"], capture_output=True, text=True)
        return {"permissions": "current user only (icacls)" if r.returncode == 0 else f"icacls failed with exit {r.returncode}", "encrypted": False}
    os.chmod(path, 0o600)
    return {"permissions": "current user only (chmod 600)", "encrypted": False}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def model_strings(obj, seen=None, depth=0):
    """Every string inside a trained model object (vocabulary, metadata, parameters), for the disclosure checks."""
    seen = seen if seen is not None else set()
    if id(obj) in seen or depth > 12: return
    seen.add(id(obj))
    if isinstance(obj, str): yield obj; return
    if isinstance(obj, bytes): yield obj.decode("latin-1", "ignore"); return
    if isinstance(obj, dict):
        for k, v in obj.items(): yield from model_strings(k, seen, depth + 1); yield from model_strings(v, seen, depth + 1)
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for v in obj: yield from model_strings(v, seen, depth + 1)
    elif isinstance(obj, np.ndarray):
        if obj.dtype.kind in "OUS": yield from (str(v) for v in obj.ravel())
    elif hasattr(obj, "__dict__"):
        yield from model_strings(vars(obj), seen, depth + 1)
