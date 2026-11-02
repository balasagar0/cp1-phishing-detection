"""Builds a SYNTHETIC test-case file to smoke-test the pipeline. Every row is marked source_type=example, so nothing here can be
mistaken for real data (the refit script ignores such rows unless --allow-examples). Needs data/processed/pool_*.csv (made by run_all.sh).
Timing and linking parameters deliberately differ from the simulation's assumptions, so the assumption check has something to report."""
import sys, csv
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from testcases import COLS
ROOT = Path(__file__).resolve().parents[1]; P = ROOT / "data" / "processed"
pools = {c: pd.read_csv(P / f"pool_{c}.csv") for c in ("email", "sms", "url")}
rng = np.random.default_rng(7); n = int(sys.argv[1]) if len(sys.argv) > 1 else 260
out = sys.argv[2] if len(sys.argv) > 2 else str(ROOT / "tests" / "synthetic_smoke_test.csv")
pick = lambda ch, mal: pools[ch][pools[ch].label == mal].text.iloc[rng.integers((pools[ch].label == mal).sum())]
base = pd.Timestamp("2026-11-01T09:00:00+05:30"); rows = []
for b in range(n):
    r = rng.random(); typ = "attack_linked" if r < .35 else "attack_single" if r < .45 else "benign_linked" if r < .65 else "benign_unlinked"
    k = 1 if typ == "attack_single" else int(rng.choice([2, 3], p=[.6, .4])) if typ != "benign_unlinked" else int(rng.choice([1, 2, 3], p=[.3, .4, .3]))
    chs = list(rng.choice(["email", "sms", "url"], k, replace=False)); mal = 1 if typ.startswith("attack") else 0
    t0 = base + pd.Timedelta(minutes=float(rng.uniform(0, 60 * 24 * 14)))
    gaps = np.cumsum(rng.exponential(40 if mal else 120, k - 1)) if typ.endswith("linked") and typ != "benign_unlinked" else rng.uniform(0, 72 * 60, k - 1)
    ts = [t0] + [t0 + pd.Timedelta(minutes=float(g)) for g in gaps]
    for j, (ch, t) in enumerate(zip(chs, ts)):
        linked = typ in ("attack_linked", "benign_linked") and rng.random() < .7
        ident = (f"camp{b}.example-evil.top" if mal else f"partner{b}.example.org") if linked else ""
        rows.append([f"S{b:04d}", f"S{b:04d}-{j+1}", ch, t.isoformat(), ident, "", pick(ch, mal), "malicious" if mal else "benign", f"SC{b}" if mal else "", "example", "", f"synthetic {typ}", ""])
    if typ == "attack_linked" and rng.random() < .1:
        rows.append([f"S{b:04d}", f"S{b:04d}-c", "call", (ts[-1] + pd.Timedelta(minutes=10)).isoformat(), "", "", "tester note: caller pressed for an OTP", "malicious", f"SC{b}", "example", "", "synthetic call", ""])
with open(out, "w", newline="") as f: w = csv.writer(f); w.writerow(COLS); w.writerows(rows)
print(f"wrote {out}: {n} bundles, {len(rows)} events")
