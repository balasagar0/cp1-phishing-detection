"""Scans the files git would commit for things that look like secrets (NFR-04). Exit code 1 if anything is found.
Run:  python scripts/secret_scan.py            (uses `git ls-files` plus untracked files that are not ignored)
      python scripts/secret_scan.py --all      (every file under the project, minus .venv, _baseline_v2 and docs/inputs)
Patterns: private-key blocks, cloud and service keys, assignments such as password=..., api_key: ..., and key files by name."""
import re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "private key block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    "OpenAI/Anthropic-style key": re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_\-]{20,}\b"),
    "Slack token": re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}\b"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b"),
    "assigned secret": re.compile(r"(?i)\b(?:password|passwd|api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token)\b\s*[:=]\s*['\"][^'\"\s]{6,}['\"]"),
}
KEY_NAMES = re.compile(r"(?i)(^|/)(\.env(\..*)?|.*\.pem|.*\.key|id_rsa.*|.*\.pfx|.*\.p12|hmac_key.*)$")
SKIP_DIRS = (".venv/", "_baseline_v2/", "docs/inputs/", "node_modules/", ".git/")
TEXT_EXT = {".py", ".md", ".sh", ".bat", ".txt", ".jsx", ".js", ".ts", ".tsx", ".html", ".css", ".json", ".csv", ".toml", ".cfg", ".ini", ".yml", ".yaml", ".mmd", ""}


def candidates(all_files=False):
    if not all_files:
        try:
            out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
            return [ROOT / p for p in out.splitlines() if p]
        except Exception:
            pass
    return [p for p in ROOT.rglob("*") if p.is_file() and not any(p.relative_to(ROOT).as_posix().startswith(s) for s in SKIP_DIRS)]


def scan(files):
    hits = []
    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        if any(rel.startswith(s) for s in SKIP_DIRS): continue
        if KEY_NAMES.search(rel): hits.append((rel, 0, "key or env file by name"))
        if p.suffix.lower() not in TEXT_EXT or not p.exists(): continue
        try: text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError: continue
        for n, line in enumerate(text.splitlines(), 1):
            for name, rx in PATTERNS.items():
                if rx.search(line): hits.append((rel, n, name))
    return hits


if __name__ == "__main__":
    files = candidates("--all" in sys.argv)
    hits = scan(files)
    for rel, n, name in hits: print(f"{rel}:{n}: {name}")
    print(f"scanned {len(files)} files: {len(hits)} possible secret(s)")
    sys.exit(1 if hits else 0)
