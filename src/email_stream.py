"""Streaming, read-only reader for the account owner's Gmail Takeout .mbox (privacy spec of 7 Nov 2026; PRIVACY_AND_ETHICS.md).
- Opens each file read-only ('rb') and reads it line by line: only the message being read is in memory, never the whole archive.
- Never writes, renames or touches the archive (tests/test_private_email_pipeline.py::test_original_mbox_unchanged).
- Yields one message's text (subject + body) at a time; the caller turns it into counts and drops it. Attachments are never decoded or kept.
- Messages Gmail filed as Spam or Trash are skipped. Nothing is printed or logged here; failures are only counted (reasons are never kept,
  because an error message could quote the email)."""
import email, re
from email import policy
from pathlib import Path

# Takeout separator: "From 1789563412345678901@xxx Thu Oct 03 12:34:56 +0000 2024" (a body line that starts with "From " does not match)
_SEP = re.compile(rb"^From \S+ +[A-Z][a-z]{2} [A-Z][a-z]{2} +\d{1,2} \d\d:\d\d:\d\d(?: [+-]\d{4})? \d{4}\r?\n?$")


class Stats:
    """Counts only: how many messages were read, used, skipped or failed."""
    def __init__(self): self.read = self.skipped_spam_trash = self.failed = self.empty = 0
    def as_dict(self): return {"read": self.read, "skipped_spam_trash": self.skipped_spam_trash, "failed": self.failed, "empty": self.empty}


def _raw_messages(path):
    """Raw bytes of one message at a time."""
    buf = []
    with open(path, "rb") as f:                 # read-only
        for line in f:
            if _SEP.match(line):
                if buf: yield b"".join(buf)
                buf = []
            else:
                buf.append(line[1:] if line.startswith(b">From ") else line)
        if buf: yield b"".join(buf)


def _text(msg):
    subject = str(msg.get("subject", "") or "")
    body = ""
    try:
        part = msg.get_body(preferencelist=("plain", "html"))
        if part is not None: body = part.get_content()
    except Exception:
        body = ""
    if not body:
        for p in (msg.walk() if msg.is_multipart() else [msg]):
            if p.get_content_maintype() == "text" and not p.get_filename():
                raw = p.get_payload(decode=True) or b""
                body = raw.decode(p.get_content_charset() or "latin-1", errors="ignore") if isinstance(raw, bytes) else str(raw)
                if body: break
    return f"{subject} . {body}"


def iter_texts(paths, stats=None, headers=False):
    """One legitimate message at a time: its text, or (text, header-identity strings) with headers=True (for the privacy audit only).
    The caller must not keep, print or log what it receives."""
    stats = stats if stats is not None else Stats()
    for path in paths:
        for raw in _raw_messages(path):
            stats.read += 1
            try:
                msg = email.message_from_bytes(raw, policy=policy.default)
                if re.search(r"\b(Spam|Trash)\b", str(msg.get("X-Gmail-Labels", ""))): stats.skipped_spam_trash += 1; continue
                text = _text(msg)
                if len(text) < 30: stats.empty += 1; continue
                if headers:
                    ids = [str(msg.get(h, "") or "") for h in ("From", "To", "Cc", "Reply-To")]
                    yield text, ids
                else:
                    yield text
            except Exception:
                stats.failed += 1
            finally:
                raw = None; msg = None; text = None          # drop references; this does NOT guarantee the memory is wiped (see PRIVACY_AND_ETHICS.md)


def mbox_paths(folder):
    return sorted(Path(folder).glob("*.mbox")) if Path(folder).exists() else []
