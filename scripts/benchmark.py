"""Latency over real HTTP (Phase 4.2, R3-10, NFR-01, NFR-02).  python scripts/benchmark.py [--n 100]
Starts uvicorn on a spare port (temporary event database, no access log), warms it up, then sends --n requests per channel to /score
(E-P01, S-P04, U-P01 from the workbook) one at a time, and --n full cases to /correlate (the demo cases TC-01 to TC-08 in turn, TC-03 included,
which answers CANNOT_ASSESS). Records median, 95th percentile and maximum with this machine's CPU, RAM and OS.
Targets from the test plan: NFR-01 median 2 s or less per channel; NFR-02 every full case 5 s or less.
Writes reports/benchmark.json (read by tests/test_final_cases.py) and reports/benchmark.md."""
import argparse, json, os, socket, statistics, subprocess, sys, tempfile, time, datetime
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
from machine_info import info, one_line
from demo_cases import CASES


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def stats(ts):
    ts = sorted(ts); return {"n": len(ts), "median_ms": round(statistics.median(ts), 1), "p95_ms": round(ts[int(round(0.95 * (len(ts) - 1)))], 1), "max_ms": round(ts[-1], 1)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=100); a = ap.parse_args()
    port = free_port(); url = f"http://127.0.0.1:{port}"; tmp = tempfile.mkdtemp(prefix="cp1_bench_")
    env = {**os.environ, "CP1_EVENT_DB": str(Path(tmp) / "events.db"), "CP1_HMAC_KEY": "benchmark-key"}
    t0 = time.perf_counter()
    p = subprocess.Popen([sys.executable, "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", str(port), "--no-access-log"], cwd=ROOT, env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        c = httpx.Client(base_url=url, timeout=60)
        for _ in range(240):
            try:
                if c.get("/health").status_code == 200: break
            except httpx.HTTPError: time.sleep(0.25)
        startup = time.perf_counter() - t0
        wb = json.loads((ROOT / "tests" / "data" / "workbook_cases.json").read_text(encoding="utf-8"))
        em = next(r for r in wb["email"] if r["ID"] == "E-P01"); sm = next(r for r in wb["sms"] if r["ID"] == "S-P04"); ur = next(r for r in wb["url"] if r["ID"] == "U-P01")
        bodies = {"email": {"channel": "email", "text": em["Body"], "subject": em["Subject"]}, "sms": {"channel": "sms", "text": sm["Message"]}, "url": {"channel": "url", "text": ur["URL"]}}
        for b in bodies.values(): c.post("/score", json=b)                                           # warm-up, not timed
        per = {}
        for ch, b in bodies.items():
            ts = []
            for _ in range(a.n):
                s = time.perf_counter(); r = c.post("/score", json=b); ts.append((time.perf_counter() - s) * 1000); assert r.status_code == 200, r.text[:200]
            per[ch] = stats(ts)
        cases = list(CASES.values()); ts = []
        for i in range(a.n):
            s = time.perf_counter(); r = c.post("/correlate", json={"events": cases[i % len(cases)]["events"]}); ts.append((time.perf_counter() - s) * 1000); assert r.status_code == 200, r.text[:200]
        full = stats(ts)
    finally:
        p.terminate(); p.wait(timeout=30)
    m = info()
    doc = {"date": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "machine": one_line(m), "machine_detail": m, "transport": f"real HTTP to uvicorn on {url}",
           "commit": subprocess.run(["git", "describe", "--tags", "--always", "--dirty"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
           "n_per_channel": a.n, "per_channel": per, "full_case": full, "startup_s": round(startup, 1),
           "nfr01_median_le_2s_each_channel": all(v["median_ms"] <= 2000 for v in per.values()), "nfr02_every_full_case_le_5s": full["max_ms"] <= 5000,
           "demo_laptop": "not confirmed: Viraj confirms whether this is the demo laptop, or re-runs this script on it (R3-10)"}
    (ROOT / "reports" / "benchmark.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    L = ["# Latency benchmark\n", f"Written by `scripts/benchmark.py` on {doc['date']} on `{doc['commit']}`. {doc['transport']}, requests one at a time after a warm-up.\n",
         f"Machine: {doc['machine']}. **{doc['demo_laptop']}.**\n", "| Request | n | Median | 95th percentile | Max | Target | Met |", "|---|---|---|---|---|---|---|"]
    for ch, v in per.items(): L.append(f"| /score {ch} | {v['n']} | {v['median_ms']:.0f} ms | {v['p95_ms']:.0f} ms | {v['max_ms']:.0f} ms | NFR-01: median 2 s or less | {'yes' if v['median_ms'] <= 2000 else 'no'} |")
    L.append(f"| /correlate full case (TC-01 to TC-08 in turn) | {full['n']} | {full['median_ms']:.0f} ms | {full['p95_ms']:.0f} ms | {full['max_ms']:.0f} ms | NFR-02: every case 5 s or less | {'yes' if full['max_ms'] <= 5000 else 'no'} |")
    L.append(f"\nServer start-up (models loaded, /health answering): {doc['startup_s']} s.")
    (ROOT / "reports" / "benchmark.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
