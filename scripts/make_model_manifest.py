"""Writes reports/model_manifest.json: every file in models/ with its size in bytes and SHA-256.
Run:  python scripts/make_model_manifest.py
The manifest lets anyone check that the models they run are the ones the reports came from (preflight.py uses it)."""
import hashlib, json, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(p, chunk=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""): h.update(b)
    return h.hexdigest()


def manifest(models_dir=ROOT / "models"):
    files = sorted(p for p in Path(models_dir).rglob("*") if p.is_file())
    return [{"file": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size, "sha256": sha256(p)} for p in files]


if __name__ == "__main__":
    out = ROOT / "reports" / "model_manifest.json"
    rows = manifest()
    doc = {"written": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "n_files": len(rows),
           "total_bytes": sum(r["bytes"] for r in rows), "files": rows}
    out.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {out.relative_to(ROOT)}: {len(rows)} files, {doc['total_bytes']:,} bytes")
    sys.exit(0)
