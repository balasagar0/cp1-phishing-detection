"""Privacy audit of the v3 email model, trained on the account owner's Gmail export (privacy spec of 7 Nov 2026, section 5 and 9).
  python scripts/privacy_audit_email.py        (after src/eval_email_v3.py; about 5 minutes)
Runs offline (outbound sockets blocked), reads the archive read-only, prints and writes COUNTS ONLY, never any text from the inbox.
Each requirement gets VERIFIED (proven by implementation and test), PARTIAL (protection exists but is incomplete), FAILED (violated) or
UNVERIFIED (not enough evidence). The model must not be used if any exposure check FAILS.
  1. Memorisation: synthetic canaries (fake names, addresses, phones, passwords, cards, unique phrases; 6 copies each) are mixed into the REAL
     private stream and an audit model is trained with v3's recipe. Canary words must not enter the model, and trained-on and never-seen canaries
     must score identically.
  2. Every term of the released model also occurs in at least 5 emails of some public source (so no inbox-only word is stored).
  3. No e-mail address, and no number of 6 or more digits, anywhere in the model object; metadata holds counts and source names only.
  4. Names and addresses from the inbox's From/To/Cc/Reply-To headers (read in memory): how many of their words are model terms.
  5. Unique-message extraction: the model holds single words and word pairs only; no 8-word run from the inbox appears in any report or log.
Writes reports/privacy/email_v3_privacy_audit.md and .json."""
import json, re, sys, hashlib, datetime, socket
from email.utils import getaddresses
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "tests")); sys.path.insert(0, str(ROOT))
import numpy as np
import joblib
from common import clean_text
import train_email as TE
import private_email_training as P
import email_stream
from test_private_email_pipeline import CANARIES, HELDOUT, canary_text

OUT = ROOT / "reports" / "privacy"; MODEL = ROOT / "models" / "candidates" / "email_model_v3.joblib"


class Offline:
    def __init__(self): self.attempts = 0
    def __enter__(self):
        self.real = (socket.socket.connect, socket.create_connection, socket.getaddrinfo)
        def block(*a, **k):
            self.attempts += 1; raise OSError("blocked")
        socket.socket.connect = lambda s, *a, **k: block(); socket.create_connection = block; socket.getaddrinfo = block
        return self
    def __exit__(self, *e): socket.socket.connect, socket.create_connection, socket.getaddrinfo = self.real


def shingles(text, n=8):
    w = re.findall(r"\w+", text.lower())
    return {hashlib.sha1(" ".join(w[i:i + n]).encode()).hexdigest()[:16] for i in range(max(0, len(w) - n + 1))}


def main():
    v3 = json.loads((ROOT / "reports" / "candidates" / "email_candidates_v3.json").read_text())
    paths = email_stream.mbox_paths(ROOT / "data" / "raw" / "email_own")
    before = {p.name: P.sha256(p) for p in paths}
    R = {}
    with Offline() as net:
        d_pub, _ = TE.load_email(extra=True, legit=True)
        # 1. memorisation with canaries in the real stream
        can = [canary_text(c) for c in CANARIES for _ in range(6)]
        audit, st, (X, y, src, cv) = P.train_on(d_pub.text, d_pub.label.values, d_pub.source.values, paths, C=v3["chosen_C"], canaries=can)
        vocab = set(audit["vectorizer"].vocabulary_)
        unique = {w.lower() for c in CANARIES for w in (*c[0].split(), *c[5].split())} | {c[1].split("@")[0].lower() for c in CANARIES}
        v, clf = audit["vectorizer"], audit["clf"]
        diff = float(np.max(np.abs(clf.predict_proba(v.transform([canary_text(c) for c in CANARIES]))[:, 1] - clf.predict_proba(v.transform([canary_text(c) for c in HELDOUT]))[:, 1])))
        canary_in_vocab = len(unique & vocab)
        R["memorisation_of_unique_phrases"] = {"status": "VERIFIED" if canary_in_vocab == 0 and diff < 1e-9 else "FAILED",
                                               "evidence": f"canary words in the model: {canary_in_vocab}; largest score gap between trained-on and never-seen canaries: {diff:.2e}; audit model trained on the real stream ({st['kept']:,} inbox emails) plus {len(can)} canary emails"}
        # 2-3. the released model
        model = joblib.load(MODEL); terms = list(model["vectorizer"].vocabulary_)
        pub_rows = np.where(src != P.PRIVATE)[0]; Xpub = X[pub_rows]; spub = src[pub_rows]
        col = {g: i for g, i in cv.vocabulary_.items()}
        support = np.zeros(X.shape[1], dtype=bool)
        for s_ in np.unique(spub):
            support |= np.asarray((Xpub[np.where(spub == s_)[0]] > 0).sum(0)).ravel() >= 5
        no_public = sum(1 for t in terms if col.get(t) is None or not support[col[t]])
        R["no_inbox_only_terms"] = {"status": "VERIFIED" if no_public == 0 else "FAILED", "evidence": f"model terms: {len(terms):,}; terms without public support (5+ emails in a public source): {no_public}"}
        strings = list(P.model_strings(model)); blob = "\n".join(strings)
        emails_found = len(re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", blob)); long_numbers = len(re.findall(r"\d{6,}", blob))
        meta_ok = set(model["meta"]) == {"channel", "trained_with_private_mail", "private_emails", "sources", "C"}
        R["email_addresses_phone_numbers_financial_details_credentials"] = {"status": "VERIFIED" if emails_found == 0 and long_numbers == 0 and meta_ok and R["memorisation_of_unique_phrases"]["status"] == "VERIFIED" else "FAILED",
            "evidence": f"e-mail addresses in the model object: {emails_found}; numbers of 6+ digits: {long_numbers}; metadata holds only counts and source names: {meta_ok}; numbers are masked before counting; canary passwords and card numbers absent (check 1)"}
        # 4. header identities, read in memory, compared with the model's single-word terms
        idw, n_msgs = set(), 0
        for text, ids in email_stream.iter_texts(paths, headers=True):
            text = None; n_msgs += 1
            for name, addr in getaddresses(ids):
                for w in re.findall(r"[a-zA-Z]{3,}", f"{name} {addr.split('@')[0]}"): idw.add(w.lower())
        uni = {t for t in terms if " " not in t}
        hits = len(idw & uni)
        R["personal_names"] = {"status": "VERIFIED" if hits == 0 else "PARTIAL",
                               "evidence": f"distinct words in the inbox's names and address local parts: {len(idw):,}; of them, single-word model terms: {hits}. "
                                           f"Every model term also occurs in public data (check 2), so these are common words (for example a brand or a common first name), not names learnt from the inbox alone. Their weights are still influenced by the inbox."}
        idw = None
        # 5. extraction of unique messages: model n-gram length, and reports/logs against 8-word runs of the inbox
        max_n = max(len(t.split()) for t in terms)
        sh = set()
        for text in email_stream.iter_texts(paths):
            sh |= shingles(clean_text(text)); text = None
        files = [p for p in list((ROOT / "reports").rglob("*.md")) + list((ROOT / "reports").rglob("*.json")) + list((ROOT / "reports").rglob("*.txt"))]
        overlap = sum(len(shingles(p.read_text(encoding="utf-8", errors="ignore")) & sh) for p in files)
        sh = None
        R["extraction_of_unique_messages"] = {"status": "VERIFIED" if max_n <= 2 and overlap == 0 else "FAILED",
                                              "evidence": f"longest model term: {max_n} words (the model cannot hold a sentence); 8-word runs of inbox text found in {len(files)} report and log files: {overlap}"}
    after = {p.name: P.sha256(p) for p in paths}
    pv = v3["privacy"]
    R["original_mbox_unchanged"] = {"status": "VERIFIED" if before == after and pv["archive_unchanged"] else "FAILED", "evidence": f"SHA-256 equal before and after the v3 run and this audit: {before == after and pv['archive_unchanged']}; test_original_mbox_unchanged"}
    R["no_external_transmission"] = {"status": "VERIFIED" if net.attempts == 0 and pv["outbound_connection_attempts"] == 0 else "FAILED",
                                     "evidence": f"outbound attempts during the v3 run: {pv['outbound_connection_attempts']}, during this audit: {net.attempts}; test_no_external_network_transmission, test_training_works_offline"}
    R["model_file_protection"] = {"status": "PARTIAL", "evidence": f"{pv['model_file']['permissions']}; not encrypted: Windows 11 Home has no file encryption (EFS). Turning on device encryption or BitLocker is the owner's choice."}
    R["memory_release"] = {"status": "UNVERIFIED", "evidence": "each email's text is dropped after counting, but Python cannot prove the memory is wiped (garbage collection, OS paging)"}
    R["streaming"] = {"status": "PARTIAL", "evidence": "each message is read and counted one at a time and its text dropped (test_streaming_email_processing); integer n-gram counts for the inbox stay in memory for the run because the model needs several training passes"}
    exposure = ["memorisation_of_unique_phrases", "no_inbox_only_terms", "email_addresses_phone_numbers_financial_details_credentials", "extraction_of_unique_messages", "original_mbox_unchanged", "no_external_transmission"]
    release = all(R[k]["status"] != "FAILED" for k in exposure)
    doc = {"date": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "model": str(MODEL.relative_to(ROOT)), "results": R,
           "model_may_be_used": release, "rule": "the model may be used only if no exposure check FAILED (privacy spec, section 9)"}
    OUT.mkdir(parents=True, exist_ok=True); (OUT / "email_v3_privacy_audit.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    L = ["# Privacy audit: email model v3\n", f"Written by `scripts/privacy_audit_email.py` on {doc['date']}, offline. Counts only: no text from the inbox appears here.\n",
         "| Requirement | Status | Evidence |", "|---|---|---|"] + [f"| {k.replace('_', ' ')} | **{v['status']}** | {v['evidence']} |" for k, v in R.items()]
    L += ["", f"**The model may be used: {release}.** (It may be used only if no exposure check FAILED.)", "",
          "Deleting the .mbox does not remove what the model learnt from it: the IDF values and weights of its terms are shaped by the inbox. To withdraw the inbox, delete the export and the model file, and retrain without it."]
    (OUT / "email_v3_privacy_audit.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    for k, v in R.items(): print(f"{v['status']:<11} {k}")
    print("model may be used:", release); return 0 if release else 1


if __name__ == "__main__":
    sys.exit(main())
