"""Readers for the three extra email corpora (Phase 3.1), fetched from their original sources by download_email_extra.sh.
They are read in place (mbox files and archives); nothing is unpacked. Each reader returns DataFrame(source, raw, label) with
raw = subject + " . " + body text, label 1 = unwanted (phishing or spam), 0 = legitimate.
  Nazario       every message is phishing (label 1). CC-BY-4.0, Jose Nazario. Hand-classified by its author, so it may hold a few errors.
  SpamAssassin  easy_ham, easy_ham_2, hard_ham = 0; spam, spam_2 = 1. Copyright stays with the original senders.
  LingSpam      the 'bare' version; spmsg*.txt = 1, all other files = 0. Research use; cite Androutsopoulos et al. (2000)."""
import email, tarfile, re
from email import policy
from pathlib import Path
import pandas as pd

EXTRA = Path(__file__).resolve().parents[1] / "data" / "raw" / "email_extra"


def _text(msg):
    """Subject and the best body part (plain text first, else HTML; clean_text strips the HTML later)."""
    subject = str(msg.get("subject", "") or "")
    body = ""
    try:
        part = msg.get_body(preferencelist=("plain", "html")) if hasattr(msg, "get_body") else None
        if part is not None: body = part.get_content()
    except Exception:
        part = None
    if not body:
        for p in (msg.walk() if msg.is_multipart() else [msg]):
            if p.get_content_maintype() == "text":
                raw = p.get_payload(decode=True) or b""
                body = raw.decode(p.get_content_charset() or "latin-1", errors="ignore") if isinstance(raw, bytes) else str(raw)
                if body: break
    return f"{subject} . {body}"


SKIPPED = []          # files that could not be read (for example held by an antivirus scanner); reported by the training script


def _mbox(path):
    """Messages of an mbox file, read only (mailbox.mbox opens files read-write). Splits on 'From ' lines at the start of a line."""
    for part in re.split(rb"(?m)^From [^\n]*\n", Path(path).read_bytes()):
        if part.strip(): yield email.message_from_bytes(re.sub(rb"(?m)^>(>*From )", rb"\1", part), policy=policy.default)


def load_nazario(d=EXTRA / "nazario"):
    rows = []
    for f in sorted(p for p in Path(d).iterdir() if p.is_file() and p.name not in ("README.txt", "LICENSE.txt")):
        try: msgs = list(_mbox(f))
        except OSError as e: SKIPPED.append(f"{f.name}: {e.__class__.__name__} {e}"); continue
        for m in msgs:
            try: rows.append({"source": "Nazario", "raw": _text(m), "label": 1, "file": f.name})
            except Exception: continue
    return pd.DataFrame(rows)


def load_spamassassin(d=EXTRA / "spamassassin"):
    rows = []
    for f in sorted(Path(d).glob("*.tar.bz2")):
        label = 1 if "spam" in f.name else 0
        with tarfile.open(f, "r:bz2") as t:
            for m in t:
                if not m.isfile() or m.name.rsplit("/", 1)[-1] == "cmds": continue
                msg = email.message_from_bytes(t.extractfile(m).read(), policy=policy.default)
                try: rows.append({"source": "SpamAssassin", "raw": _text(msg), "label": label, "file": f.name})
                except Exception: continue
    return pd.DataFrame(rows)


def load_lingspam(path=EXTRA / "lingspam" / "lingspam_public.tar.gz"):
    rows = []
    with tarfile.open(path, "r:gz") as t:
        for m in t:
            if not m.isfile() or "/bare/" not in m.name or not m.name.endswith(".txt"): continue
            txt = t.extractfile(m).read().decode("latin-1", errors="ignore")
            subj, _, body = txt.partition("\n")
            rows.append({"source": "LingSpam", "raw": f"{re.sub(r'^Subject:\s*', '', subj.strip())} . {body}", "label": 1 if m.name.rsplit("/", 1)[-1].startswith("spmsg") else 0, "file": m.name.split("/")[2]})
    return pd.DataFrame(rows)


def load_extra():
    return pd.concat([load_nazario(), load_spamassassin(), load_lingspam()], ignore_index=True)


# ---- legitimate transactional email for the v3 attempt (download_email_legit.sh; the own-inbox export is added by a person). All label 0.
LEGIT = Path(__file__).resolve().parents[1] / "data" / "raw" / "email_legit"
OWN = Path(__file__).resolve().parents[1] / "data" / "raw" / "email_own"
_PLACEHOLDER = re.compile(r"\{\{[^}]*\}\}|\{\{|\}\}")


def load_generated(path=LEGIT / "generated" / "email_dataset.json"):
    """imnim/multiclass-email-classification (MIT): 2,105 emails GENERATED with GPT-3.5 (its dataset_creation.py). Synthetic, not real messages."""
    import json
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    return pd.DataFrame([{"source": "GeneratedLegit", "raw": f"{r.get('subject', '')} . {r.get('body', '')}", "label": 0, "file": ",".join(r.get("labels", []))} for r in rows])


def load_templates(d=LEGIT / "templates"):
    """Postmark (11 template types) and Mailgun (3) transactional email templates, MIT: real company wording; placeholders removed, nothing filled in."""
    import zipfile
    rows = []
    for z in sorted(Path(d).glob("*.zip")):
        with zipfile.ZipFile(z) as f:
            for n in f.namelist():
                if ("postmark" in z.name and n.endswith("/content.txt")) or ("mailgun" in z.name and n.endswith(".html") and "/inlined/" not in n):
                    txt = _PLACEHOLDER.sub(" ", f.read(n).decode("utf-8", errors="ignore"))
                    rows.append({"source": "Templates", "raw": f" . {txt}", "label": 0, "file": n.split("/")[-2] + "/" + n.split("/")[-1]})
    return pd.DataFrame(rows)


def load_own_inbox(d=OWN):
    """Removed on purpose: the account owner's mail is read ONLY through the streaming, privacy-first path (src/email_stream.py and
    src/private_email_training.py), never into a table of texts. See PRIVACY_AND_ETHICS.md."""
    raise RuntimeError("the own inbox is read only by src/private_email_training.py (streaming); see PRIVACY_AND_ETHICS.md")


def load_legit_extra():
    """The PUBLIC legitimate sources only (generated and templates). The own inbox never enters a table: see src/private_email_training.py."""
    return pd.concat([load_generated(), load_templates()], ignore_index=True)


if __name__ == "__main__":
    df = load_extra()
    print(df.groupby(["source", "label"]).size().to_string()); print("empty texts:", int((df.raw.str.len() < 10).sum())); print("skipped files:", SKIPPED or "none")
