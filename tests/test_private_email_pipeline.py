"""Privacy tests for the private email training path (privacy spec of 7 Nov 2026; PRIVACY_AND_ETHICS.md maps each claim to these tests).
SYNTHETIC MESSAGES ONLY: a made-up Takeout-style .mbox and made-up public corpora are built in a temporary folder. No real email is read here.
Canary records carry fake names, addresses, phone numbers, passwords, card numbers and unique phrases; they are mixed into the private stream
(some repeated 6 times) and must not be exposed by the trained model.
Run:  python tests/test_private_email_pipeline.py      or      pytest tests/test_private_email_pipeline.py"""
import contextlib, io, logging, os, re, socket, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import numpy as np
import email_stream
import private_email_training as P

RNG = np.random.default_rng(7)
LEGIT = "your order has shipped and will arrive on friday you can track the package in the app thank you for shopping receipt payment received for your plan statement is ready".split()
PHISH = "verify your account password now or it will be suspended click the link urgent confirm your bank details login to restore access security alert".split()
CANARIES = [  # (name, address, phone, password, card, phrase): inserted ones
    ("Zorbatha Quillfeather", "zorbatha.quill@canary-mail.test", "+91 70000 12345", "Xq7!kLm2Zr", "4111 1111 1111 1111", "violet umbrella negotiates quietly"),
    ("Merrowind Talcastle", "merrowind.t@canary-mail.test", "+91 70000 67890", "Pw9#tRe4Lk", "5500 0000 0000 0004", "copper lantern whistles backwards"),
]
HELDOUT = [   # same template, different secrets: never trained on
    ("Ysolde Brackenfirth", "ysolde.b@canary-mail.test", "+91 70000 24680", "Hk3$vBn8Qw", "3782 822463 10005", "amber teacup sings sideways"),
    ("Thadric Pellowmere", "thadric.p@canary-mail.test", "+91 70000 13579", "Lm5%yUi2Op", "6011 1111 1111 1117", "silver kettle dances slowly"),
]


def canary_text(c):
    name, addr, phone, pw, card, phrase = c
    return (f"Payment received - thank you . Dear {name}, we have received your payment for your plan. Your login is {addr} and your temporary password is {pw}. "
            f"Card ending {card} was charged. Call {phone} for help. Note: {phrase}. You can download the receipt from the app.")


def secrets(c):
    name, addr, phone, pw, card, phrase = c
    return [*name.lower().split(), addr, addr.split("@")[0], pw.lower(), card, card.replace(" ", ""), phone, re.sub(r"\D", "", phone), phrase, *phrase.split()]


def sentence(words, n=14): return " ".join(RNG.choice(words, n))


def public_corpora():
    texts, labels, sources = [], [], []
    for s in ("PubA", "PubB", "PubC"):
        for _ in range(60):
            texts.append(sentence(LEGIT) + " " + sentence(LEGIT)); labels.append(0); sources.append(s)
            texts.append(sentence(PHISH) + " " + sentence(PHISH)); labels.append(1); sources.append(s)
    return texts, labels, sources


def write_mbox(path, n_legit=30, with_spam=True):
    out = []
    for i in range(n_legit):
        out.append(f"From 17895634123456{i:05d}@xxx Thu Oct 03 12:{i % 60:02d}:56 +0000 2024\nX-Gmail-Labels: cp1-legit\nFrom: Shop <orders@shop{i}.test>\nTo: owner@owner.test\n"
                   f"Subject: Your order {i} has shipped\nContent-Type: text/plain; charset=utf-8\n\n{sentence(LEGIT, 20)}\nFrom the shop team, with thanks.\n\n")
    if with_spam:
        out.append("From 1789563412345699999@xxx Fri Oct 04 09:00:00 +0000 2024\nX-Gmail-Labels: Spam,cp1-legit\nFrom: Bad <x@bad.test>\nTo: owner@owner.test\n"
                   "Subject: spam marker zzspamqq\nContent-Type: text/plain\n\nzzspamqq verify your account now zzspamqq\n\n")
    Path(path).write_text("".join(out), encoding="utf-8", newline="\n")


def everything(tmp, canaries=True):
    """Builds the synthetic world in `tmp` and trains once. Returns (model, stats, mbox path, extra)."""
    mbox = Path(tmp) / "synthetic.mbox"; write_mbox(mbox)
    texts, labels, sources = public_corpora()
    can = [canary_text(c) for c in CANARIES for _ in range(6)] if canaries else []
    model, st, extra = P.train_on(texts, labels, sources, [mbox], C=4, canaries=can)
    return model, st, mbox, extra


ALL_SECRETS = [s for c in CANARIES + HELDOUT for s in secrets(c)] + ["zzspamqq"]


def _snapshot(*dirs):
    skip = {".venv", ".git", "node_modules", "__pycache__", ".pytest_cache"}
    out = {}
    for d in dirs:
        for p in Path(d).rglob("*"):
            if p.is_file() and not (set(p.parts) & skip): out[p] = p.stat().st_mtime_ns
    return out


class _Blocked:
    def __init__(self): self.attempts = []
    def __enter__(self):
        self.real = (socket.socket.connect, socket.create_connection, socket.getaddrinfo)
        a = self.attempts
        def connect(sock, addr, *x, **k): a.append(("connect", addr)); raise OSError("blocked by test")
        def create(addr, *x, **k): a.append(("create_connection", addr)); raise OSError("blocked by test")
        def gai(host, *x, **k): a.append(("getaddrinfo", host)); raise socket.gaierror("blocked by test")
        socket.socket.connect, socket.create_connection, socket.getaddrinfo = connect, create, gai
        return self
    def __exit__(self, *e): socket.socket.connect, socket.create_connection, socket.getaddrinfo = self.real


# ---------------------------------------------------------------- the ten tests
def test_original_mbox_unchanged():
    with tempfile.TemporaryDirectory() as tmp:
        mbox = Path(tmp) / "synthetic.mbox"; write_mbox(mbox)
        before = (P.sha256(mbox), mbox.stat().st_size, mbox.stat().st_mtime_ns)
        texts, labels, sources = public_corpora()
        P.train_on(texts, labels, sources, [mbox], C=4)
        assert (P.sha256(mbox), mbox.stat().st_size, mbox.stat().st_mtime_ns) == before


def test_no_raw_email_in_logs():
    out, err, logs = io.StringIO(), io.StringIO(), io.StringIO()
    h = logging.StreamHandler(logs); root = logging.getLogger(); root.addHandler(h); old = root.level; root.setLevel(logging.DEBUG)
    try:
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            model, st, mbox, _ = everything(tmp)
    finally: root.removeHandler(h); root.setLevel(old)
    text = (out.getvalue() + err.getvalue() + logs.getvalue()).lower()
    leaked = [s for s in ALL_SECRETS + ["your order 3 has shipped", "from the shop team", "orders@shop"] if s.lower() in text]
    assert not leaked, leaked
    assert all(isinstance(v, int) for v in st.values()), st                       # the run's own record is counts only


def test_no_raw_email_in_database():
    dbs = lambda: {p for p in list(ROOT.rglob("*.db")) + list(ROOT.rglob("*.sqlite*")) if ".venv" not in p.parts}
    before = dbs()
    with tempfile.TemporaryDirectory() as tmp:
        everything(tmp)
        made = [p for p in Path(tmp).rglob("*") if p.suffix in (".db", ".sqlite", ".sqlite3")]
    assert dbs() == before and not made, (dbs() - before, made)
    for db in before:                                                              # existing databases (the event store) hold none of it
        raw = db.read_bytes().lower()
        assert not any(s.lower().encode() in raw for s in ALL_SECRETS), db


def test_no_external_network_transmission():
    with _Blocked() as b, tempfile.TemporaryDirectory() as tmp:
        everything(tmp)
    assert b.attempts == [], b.attempts
    for f in ("email_stream.py", "private_email_training.py", "common.py"):
        src = (ROOT / "src" / f).read_text(encoding="utf-8")
        assert not re.search(r"^\s*(import|from)\s+(requests|httpx|urllib|http\.client|socket|aiohttp|boto3|openai|anthropic)\b", src, re.M), f


def test_network_guard_blocks_outbound_and_allows_loopback():
    from network_guard import NoExternalNetwork
    with NoExternalNetwork() as n:
        x, y = socket.socketpair(); x.close(); y.close()                         # loopback stays allowed (asyncio needs it on Windows)
        for target in (("example.com", 80), ("93.184.215.14", 443)):
            try: socket.create_connection(target, timeout=2); raise AssertionError(f"not blocked: {target}")
            except OSError: pass
    assert n.attempts == 2, n.attempts


def test_no_persistent_extracted_dataset():
    with tempfile.TemporaryDirectory() as tmp:
        mbox = Path(tmp) / "synthetic.mbox"; write_mbox(mbox); texts, labels, sources = public_corpora()
        before = _snapshot(ROOT, tmp)                                               # the synthetic input exists; now nothing else may appear
        model, st, _ = P.train_on(texts, labels, sources, [mbox], C=4, canaries=[canary_text(c) for c in CANARIES for _ in range(6)])
        out = Path(tmp) / "model_private.joblib"; P.save_private(model, out)
        after = _snapshot(ROOT, tmp)
        new = [p for p in after if p not in before or before[p] != after[p]]
        new = [p for p in new if p.name != "final_cases_results.json"]
        assert new == [out], new                                                    # nothing but the model was written
        import joblib
        strings = " ".join(P.model_strings(joblib.load(out))).lower()
        assert not [s for s in ALL_SECRETS if s.lower() in strings]


def test_streaming_email_processing():
    with tempfile.TemporaryDirectory() as tmp:
        mbox = Path(tmp) / "synthetic.mbox"; write_mbox(mbox, n_legit=400, with_spam=False)
        size = mbox.stat().st_size; pos = {}
        real_open = open
        class Track:
            def __init__(self, *a, **k): self.f = real_open(*a, **k); pos["f"] = self.f
            def __enter__(self): return self
            def __exit__(self, *e): self.f.close()
            def __iter__(self): return iter(self.f)
        email_stream.open = Track
        try:
            g = email_stream.iter_texts([mbox]); first = next(g)
            read_after_first = pos["f"].tell()
            assert "shipped" in first and read_after_first < size / 10, (read_after_first, size)   # it has read only the start of the file
            rest = sum(1 for _ in g)
        finally:
            del email_stream.open
        assert rest == 399
        X, st = P.stream_private([mbox], P.candidate_vocab(public_corpora()[0])[0])
        assert X.dtype.kind == "i" and st["read"] == 400 and st["kept"] >= 1              # what is kept is integer counts, never text


def test_temporary_file_cleanup():
    with tempfile.TemporaryDirectory() as watch, tempfile.TemporaryDirectory() as tmp:
        saved = tempfile.tempdir; env = {k: os.environ.get(k) for k in ("TMP", "TEMP", "TMPDIR")}
        tempfile.tempdir = watch
        for k in env: os.environ[k] = watch
        try: everything(tmp)
        finally:
            tempfile.tempdir = saved
            for k, v in env.items():
                if v is None: os.environ.pop(k, None)
                else: os.environ[k] = v
        assert list(Path(watch).iterdir()) == []


def test_training_works_offline():
    with _Blocked() as b, tempfile.TemporaryDirectory() as tmp:
        model, st, mbox, _ = everything(tmp)
    v, clf = model["vectorizer"], model["clf"]
    p_phish = clf.predict_proba(v.transform(["verify your account password now urgent click the link"]))[0, 1]
    p_legit = clf.predict_proba(v.transform(["your order has shipped track the package in the app"]))[0, 1]
    assert b.attempts == [] and p_phish > 0.5 > p_legit, (b.attempts, p_phish, p_legit)
    assert st["skipped_spam_trash"] == 1 and st["read"] == 31


def test_model_memorization():
    with tempfile.TemporaryDirectory() as tmp:
        model, st, mbox, _ = everything(tmp)
    vocab = set(model["vectorizer"].vocabulary_)
    unique = {w for c in CANARIES for w in (*c[0].lower().split(), *c[5].split())} | {"zorbatha", "quill", "xq7", "klm2zr"}
    assert not (unique & vocab), unique & vocab                                    # canary words repeated 6 times never enter the model
    v, clf = model["vectorizer"], model["clf"]
    ins = clf.predict_proba(v.transform([canary_text(c) for c in CANARIES]))[:, 1]
    out = clf.predict_proba(v.transform([canary_text(c) for c in HELDOUT]))[:, 1]
    assert np.max(np.abs(ins - out)) < 1e-9, (ins, out)                             # trained-on and never-seen canaries score exactly alike


def test_model_sensitive_information_disclosure():
    with tempfile.TemporaryDirectory() as tmp:
        model, st, mbox, _ = everything(tmp)
    strings = list(P.model_strings(model)); blob = "\n".join(strings).lower()
    assert not [s for s in ALL_SECRETS if s.lower() in blob]
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", blob)                          # no e-mail address
    assert not re.search(r"\d{6,}", blob)                                          # no phone, card or account number (numbers are masked)
    assert not [s for s in strings if "owner@" in s or "shop" in s and "@" in s]
    assert set(model["meta"]) == {"channel", "trained_with_private_mail", "private_emails", "sources", "C"}   # metadata is counts and names of sources only


if __name__ == "__main__":
    ok = True
    for name, fn in [(n, f) for n, f in globals().items() if n.startswith("test_") and callable(f)]:
        try: fn(); print("PASS", name)
        except Exception as e: ok = False; print("FAIL", name, "-", repr(e)[:300])
    print("ALL PASSED" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
