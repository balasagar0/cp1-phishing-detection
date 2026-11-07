"""Demo preflight (R3-05, R3-06): is this laptop ready to demo?  python scripts/preflight.py [--port 8000] [--keep-running]
Checks, in order, and prints GO or NO-GO:
  1. Python 3.10 or later, and the packages at the versions the models need (scikit-learn exactly as pinned in requirements.txt).
  2. Every model file matches reports/model_manifest.json (size and SHA-256), so the demo runs the models the reports came from.
  3. The built console exists (console/dist/index.html).
  4. The port is free, the API starts (no access log, so no recipient appears in a log) and /health answers.
  5. TC-01 to TC-08 give the outcomes in tests/test_demo_cases.py, over real HTTP.
  6. Nothing tries to reach the internet: scripts/offline_check.py passes.
With --keep-running the API stays up after a GO, and --open opens the console in the browser (start_demo.bat uses both); otherwise it is stopped."""
import argparse, hashlib, json, os, re, socket, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
OK, BAD = "  ok  ", "  NO  "


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def port_free(port):
    s = socket.socket()
    try: s.bind(("127.0.0.1", port)); return True
    except OSError: return False
    finally: s.close()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--port", type=int, default=8000); ap.add_argument("--keep-running", action="store_true"); ap.add_argument("--open", action="store_true", help="open the console in the browser after a GO"); a = ap.parse_args()
    fails = []
    def check(name, ok, detail=""):
        print((OK if ok else BAD) + name + (f"  ({detail})" if detail else ""), flush=True)
        if not ok: fails.append(name)
        return ok

    print("CP1 demo preflight\n")
    check("Python 3.10 or later", sys.version_info >= (3, 10), sys.version.split()[0])
    try:
        import importlib.metadata as md
        want = {}
        for line in (ROOT / "requirements.txt").read_text().splitlines():
            m = re.match(r"^\s*([A-Za-z0-9_.\-]+)\s*(==|>=)\s*([\w.]+)", line)
            if m: want[m.group(1).lower()] = (m.group(2), m.group(3))
        bad = []
        for name, (op, ver) in want.items():
            try: have = md.version(name)
            except md.PackageNotFoundError: bad.append(f"{name} missing"); continue
            if op == "==" and have != ver: bad.append(f"{name} {have} (need {ver})")
        check("packages installed at the pinned versions", not bad, "; ".join(bad) or f"{len(want)} packages; scikit-learn {md.version('scikit-learn')}")
    except Exception as e: check("packages installed at the pinned versions", False, repr(e))
    try:
        man = json.loads((ROOT / "reports" / "model_manifest.json").read_text())
        wrong = [f["file"] for f in man["files"] if not (ROOT / f["file"]).exists() or (ROOT / f["file"]).stat().st_size != f["bytes"] or sha256(ROOT / f["file"]) != f["sha256"]]
        check("model files match reports/model_manifest.json", not wrong, ", ".join(wrong) or f"{len(man['files'])} files")
    except Exception as e: check("model files match reports/model_manifest.json", False, repr(e))
    check("console is built", (ROOT / "console" / "dist" / "index.html").exists(), "console/dist/index.html")
    if fails:
        print("\nNO-GO: fix the lines marked NO first (see docs/DEMO_SCRIPT.md, Fallbacks)."); return 1

    if not check(f"port {a.port} is free", port_free(a.port), "another program is using it: close it, or run preflight with --port 8001" if not port_free(a.port) else ""):
        print("\nNO-GO."); return 1
    p = subprocess.Popen([PY, "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", str(a.port), "--no-access-log"], cwd=ROOT,
                         stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    url = f"http://127.0.0.1:{a.port}"; up = False
    import httpx
    for _ in range(240):
        if p.poll() is not None: break
        try: up = httpx.get(url + "/health", timeout=2).status_code == 200
        except httpx.HTTPError: pass
        if up: break
        time.sleep(0.25)
    detail = "" if up else (p.stderr.read()[-300:] if p.poll() is not None else "no answer from /health")
    if check("API starts and /health answers", up, detail if not up else url):
        h = httpx.get(url + "/health").json()
        check("all three detectors loaded", h["status"] == "ok", f"channels {h['channels']}; window {h['window_minutes']} minutes; correlation trained on {h['fusion_trained_on']}")
        t = subprocess.run([PY, str(ROOT / "tests" / "test_demo_cases.py")], cwd=ROOT, env={**os.environ, "CP1_API_URL": url}, capture_output=True, text=True, timeout=300)
        lines = [l for l in t.stdout.splitlines() if l.startswith(("PASS", "FAIL"))]
        check("TC-01 to TC-08 give their expected outcomes", t.returncode == 0, f"{sum(l.startswith('PASS') for l in lines)} of {len(lines)} passed" + ("; " + "; ".join(l[:90] for l in lines if l.startswith("FAIL")) if t.returncode else ""))
        o = subprocess.run([PY, str(ROOT / "scripts" / "offline_check.py")], cwd=ROOT, capture_output=True, text=True, timeout=600)
        check("no network needed (scripts/offline_check.py)", o.returncode == 0, "reports/offline_check.md")
    go = not fails
    print(f"\n{'GO' if go else 'NO-GO'}: " + (f"open {url}/ in the browser." if go else "see the lines marked NO, and docs/DEMO_SCRIPT.md, Fallbacks."))
    if go and a.open:
        import webbrowser; webbrowser.open(url + "/")
    if go and a.keep_running:
        print("The API keeps running. Press Ctrl+C to stop it.")
        try: p.wait()
        except KeyboardInterrupt: pass
    p.terminate()
    try: p.wait(timeout=20)
    except subprocess.TimeoutExpired: p.kill()
    return 0 if go else 1


if __name__ == "__main__":
    sys.exit(main())
