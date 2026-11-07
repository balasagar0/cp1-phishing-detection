"""NFR-05 (Phase 4.4): a fresh clone runs from the README alone.  python scripts/nfr05_fresh_clone.py
Clones this repository (committed files only) into a new temporary folder, makes a new venv, and runs exactly the Quick start commands the
README lists for this platform, after checking each command really is in README.md. Then it starts the API the way the README says, loads
the console and runs TC-04. Needs the internet once, for pip. Writes reports/nfr05_fresh_clone.json (read by tests/test_final_cases.py)."""
import json, os, subprocess, sys, tempfile, time, datetime, shutil, socket
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIN = sys.platform == "win32"
PYV = ".venv\\Scripts\\python.exe" if WIN else ".venv/bin/python"
STEPS = (["python -m venv .venv", f"{PYV} -m pip install -r requirements.txt", f"{PYV} -m pytest tests -q"])


def run(cmd, cwd, timeout=1800):
    t = time.perf_counter()
    p = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=timeout)
    return p.returncode, round(time.perf_counter() - t, 1), (p.stdout + p.stderr).strip().splitlines()[-3:]


def main():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    missing = [s for s in STEPS if s not in readme] + ([] if "scripts/preflight.py" in readme or "start_demo.bat" in readme else ["start_demo.bat / scripts/preflight.py"])
    head = subprocess.run(["git", "describe", "--tags", "--always", "--dirty"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    tmp = Path(tempfile.mkdtemp(prefix="cp1 nfr05 "))                 # a space in the path on purpose, like the team's folder
    log, ok = [], not missing
    rc, dt, tail = run(f'git clone --quiet "{ROOT}" "{tmp / "cp1"}"', tmp); log.append({"step": "git clone (committed files only)", "exit": rc, "s": dt, "tail": tail}); ok &= rc == 0
    work = tmp / "cp1"
    for s in STEPS:
        if not ok: break
        cmd = s.replace("python -m venv", f'"{sys.executable}" -m venv') if s.startswith("python -m venv") else s      # the same Python the README asks for (3.10+)
        rc, dt, tail = run(cmd, work); log.append({"step": s, "exit": rc, "s": dt, "tail": tail}); ok &= rc == 0
    demo = None
    if ok:
        s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
        p = subprocess.Popen([str(work / PYV), "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", str(port), "--no-access-log"], cwd=work,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            import httpx
            url = f"http://127.0.0.1:{port}"
            for _ in range(240):
                try:
                    if httpx.get(url + "/health", timeout=2).status_code == 200: break
                except httpx.HTTPError: time.sleep(0.5)
            root = httpx.get(url + "/", timeout=10); pres = httpx.get(url + "/presets", timeout=10).json()
            tc04 = httpx.post(url + "/correlate", json={"events": next(x for x in pres if x["id"] == "TC-04")["events"]}, timeout=60).json()
            demo = {"console_served": root.status_code == 200 and 'id="root"' in root.text, "tc04_bundle_risk": tc04.get("bundle_risk"), "tc04_alert": (tc04.get("bundle_risk") or 0) >= .5}
            ok &= demo["console_served"] and demo["tc04_alert"]
        finally:
            p.terminate(); p.wait(timeout=30)
    shutil.rmtree(tmp, ignore_errors=True)
    actual = (f"Fresh clone of {head} into a new temporary folder with a space in its path; new venv; README Quick start commands found in README: {not missing}"
              + (f" (missing: {missing})" if missing else "") + "; " + "; ".join(f"'{x['step']}' exit {x['exit']} in {x['s']} s" for x in log)
              + (f"; API started from the clone, console served: {demo['console_served']}, TC-04 bundle risk {demo['tc04_bundle_risk']}" if demo else ""))
    doc = {"date": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "commit": head, "status": "Pass" if ok else "Fail", "actual": actual, "steps": log, "demo": demo}
    (ROOT / "reports" / "nfr05_fresh_clone.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(doc["status"], "-", actual); return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
