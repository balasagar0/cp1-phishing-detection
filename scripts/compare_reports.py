"""Compares two sets of reports (metrics JSON files) value by value and writes a Markdown record.
Used for the Phase 0.7 reproducibility check (v2 as received vs a fresh download_data.sh + run_all.sh) and again after the final run.
  python scripts/compare_reports.py OLD_REPORTS NEW_REPORTS --out reports/baseline_check.md
         [--raw NEW_DATA_RAW] [--download-log FILE] [--run-log FILE] [--old-models DIR --new-models DIR] [--label TEXT] [--extra FILE.md]
Every number in the output is read from the JSON files; nothing is typed. The 'Review-3 figure' column holds the values that
CP1_FINISH_TASK.md section 1.2 says v2's reports should show, so the check also confirms the reports match the Review-3 baseline."""
import argparse, hashlib, json, math, platform, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (label, file, key path, Review-3 figure as a fraction). The key path is a list because some keys contain dots.
HEADLINE = [
    ("Email F1, mean of 3 leave-one-corpus-out runs (honest)", "email_metrics.json", ("loco_mean", "f1"), 0.822),
    ("Email F1, pooled random split (flattering)", "email_metrics.json", ("pooled_test", "f1"), 0.988),
    ("SMS smishing-vs-rest F1 (honest)", "sms_metrics.json", ("test_smishing_vs_rest", "f1"), 0.871),
    ("SMS smishing-vs-rest F1, 95% CI low", "sms_metrics.json", ("test_smishing_vs_rest_ci95", "f1", 0), 0.823),
    ("SMS smishing-vs-rest F1, 95% CI high", "sms_metrics.json", ("test_smishing_vs_rest_ci95", "f1", 1), 0.917),
    ("SMS spam-or-smishing F1 (flattering)", "sms_metrics.json", ("test_unwanted_vs_ham", "f1"), 0.982),
    ("URL F1, host-grouped (honest)", "url_metrics.json", ("string_model", "grouped_test", "f1"), 0.904),
    ("URL false alarms on login URLs of 1,000 held-out popular domains", "url_metrics.json", ("string_model", "ablation", "c_plus_login_training_urls_FINAL", "false_positive_rate_on_login_urls_of_1000_held_out_popular_domains"), 0.000),
    ("URL recall on bad URLs on top-10k domains, before the fix", "url_metrics.json", ("string_model", "ablation", "a_ngrams_only", "recall_on_bad_urls_hosted_on_top10k_domains", "recall"), 0.499),
    ("URL recall on bad URLs on top-10k domains, final", "url_metrics.json", ("string_model", "ablation", "c_plus_login_training_urls_FINAL", "recall_on_bad_urls_hosted_on_top10k_domains", "recall"), 0.307),
    ("URL F1, offline feature benchmark (flattering)", "url_metrics.json", ("feature_benchmark", "hgb_all_features", "f1"), 0.954),
]
for name, key in (("Single-channel", "single_channel_alert_any_event_ge_0.5"), ("Whole-bundle model", "whole_bundle_model_at_0.5"),
                  ("Engine, no window", "engine_no_window_at_0.5"), ("Engine, 60-minute window", "engine_default_window_at_0.5")):
    for m, fig in zip(("precision", "recall", "f1", "false_positive_rate"),
                      {"Single-channel": (.870, .953, .910, .141), "Whole-bundle model": (.970, .929, .949, .028),
                       "Engine, no window": (.968, .930, .948, .030), "Engine, 60-minute window": (.894, .949, .920, .111)}[name]):
        HEADLINE.append((f"Correlation (simulated): {name}, {m.replace('_', ' ')}", "window_metrics.json", (key, m), fig))
HEADLINE += [
    ("Simulated linked attacks with every event below 0.5 (count)", "window_metrics.json", ("campaigns_missed_by_every_single_channel_filter", "n"), 27),
    ("Simulated linked attacks with every event below 0.5 (share)", "fusion_metrics.json", ("campaigns_missed_by_every_single_channel_filter", "share_of_linked_attacks"), 0.008),
    ("Of those, flagged by the 60-minute engine", "window_metrics.json", ("campaigns_missed_by_every_single_channel_filter", "caught_engine_default_window_at_0.5"), 0.185),
    ("Simulated linked attack bundles that fit in 60 minutes", "window_metrics.json", ("share_of_bundles_that_fit_in_one_default_window", "attack_linked"), 0.956),
]


def load(d, name):
    p = Path(d) / name
    if not p.exists(): return None
    j = json.loads(p.read_text())
    if name == "email_metrics.json" and "leave_one_corpus_out" in j:     # derived: the honest email figure is the mean over held-out corpora
        lo = j["leave_one_corpus_out"]; j["loco_mean"] = {"f1": sum(v["f1"] for v in lo.values()) / len(lo)}
    return j


def get(j, path):
    for k in path:
        if j is None: return None
        j = j[k] if (isinstance(j, list) and isinstance(k, int) and k < len(j)) or (isinstance(j, dict) and k in j) else None
    return j


def leaves(o, path=()):
    if isinstance(o, dict):
        for k, v in o.items(): yield from leaves(v, path + (k,))
    elif isinstance(o, list):
        for i, v in enumerate(o): yield from leaves(v, path + (i,))
    elif isinstance(o, (int, float)) and not isinstance(o, bool):
        yield path, o


def fmt(v, count=False):
    if v is None: return "missing"
    if count or (isinstance(v, int) and v > 1): return f"{v:,}"
    return f"{100 * v:.1f}%"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("old"); ap.add_argument("new"); ap.add_argument("--out", required=True)
    ap.add_argument("--raw"); ap.add_argument("--download-log"); ap.add_argument("--run-log")
    ap.add_argument("--old-models"); ap.add_argument("--new-models"); ap.add_argument("--label", default="re-run")
    ap.add_argument("--title", default="Reproducibility check"); ap.add_argument("--intro", default=""); ap.add_argument("--extra")
    a = ap.parse_args()
    L = [f"# {a.title}\n", f"Written by `scripts/compare_reports.py` on {datetime.datetime.now().astimezone().isoformat(timespec='seconds')}. Every value below is read from the metrics files; nothing is typed.\n"]
    if a.intro: L.append(a.intro.strip() + "\n")
    L.append(f"Machine: {platform.platform()}, Python {platform.python_version()}, {platform.processor() or platform.machine()}.\n")

    if a.raw:
        dl = Path(a.download_log).read_text(errors="ignore") if a.download_log else ""
        L.append("## Data sources\n\n| File | Bytes | SHA-256 | Download |\n|---|---|---|---|")
        for p in sorted(Path(a.raw).rglob("*")):
            if p.is_file():
                rel = p.relative_to(a.raw).as_posix(); status = "ok" if f"ok {rel}" in dl else ("unpacked from an archive" if dl else "present")
                L.append(f"| `{rel}` | {p.stat().st_size:,} | `{sha256(p)}` | {status} |")
        if a.download_log:
            failed = [ln for ln in dl.splitlines() if "curl:" in ln or "error" in ln.lower()]
            L.append("\nEvery source in `download_data.sh` downloaded." if not failed else "\nSources that failed:\n" + "\n".join(f"- `{x}`" for x in failed))
        L.append("")

    L.append(f"## Review-3 figures\n\n| Figure | Review-3 | v2 reports | v2 = Review-3 | {a.label} | {a.label} = v2 |\n|---|---|---|---|---|---|")
    same_n = r3_n = 0
    for label, f, path, fig in HEADLINE:
        o, n = get(load(a.old, f), path), get(load(a.new, f), path); cnt = isinstance(fig, int) and fig > 1
        same = o is not None and n is not None and (round(o, 3) == round(n, 3) if not cnt else o == n)
        r3 = o is not None and fmt(o, cnt) == fmt(fig, cnt)
        same_n += same; r3_n += r3
        L.append(f"| {label} | {fmt(fig, cnt)} | {fmt(o, cnt)} | {'yes' if r3 else '**no**'} | {fmt(n, cnt)} | {'yes' if same else '**no**'} |")
    L.append(f"\nv2's reports match {r3_n} of {len(HEADLINE)} Review-3 figures as printed. The {a.label} matches v2 on {same_n} of {len(HEADLINE)} figures to 3 decimals.\n")

    L.append("## Every value in every metrics file\n\n| File | Values compared | Identical | Different | Only in v2 | Only in " + a.label + " |\n|---|---|---|---|---|---|")
    diffs = []
    names = sorted({p.name for p in Path(a.old).glob("*.json")} | {p.name for p in Path(a.new).glob("*.json")})
    for name in names:
        if name in ("model_manifest.json",): continue
        oj, nj = load(a.old, name), load(a.new, name)
        ol = dict(leaves(oj)) if oj is not None else {}; nl = dict(leaves(nj)) if nj is not None else {}
        both = [k for k in ol if k in nl]
        dif = [k for k in both if not (isinstance(ol[k], float) or isinstance(nl[k], float)) and ol[k] != nl[k] or
               (isinstance(ol[k], float) or isinstance(nl[k], float)) and not math.isclose(ol[k], nl[k], rel_tol=0, abs_tol=1e-9)]
        diffs += [(name, k, ol[k], nl[k]) for k in dif]
        L.append(f"| `{name}` | {len(both)} | {len(both) - len(dif)} | {len(dif)} | {len(set(ol) - set(nl))} | {len(set(nl) - set(ol))} |")
    L.append("")
    if diffs:
        L.append(f"### Values that differ ({len(diffs)})\n\n| File | Key | v2 | {a.label} |\n|---|---|---|---|")
        for name, k, o, n in diffs[:400]: L.append(f"| `{name}` | `{'.'.join(map(str, k))}` | {o} | {n} |")
        if len(diffs) > 400: L.append(f"\n{len(diffs) - 400} more differences not listed.")
        L.append("")
    else:
        L.append("No value differs.\n")

    if a.old_models and a.new_models:
        L.append(f"## Model files\n\n| File | v2 SHA-256 | {a.label} SHA-256 | Same bytes |\n|---|---|---|---|")
        for p in sorted(Path(a.old_models).glob("*.joblib")):
            q = Path(a.new_models) / p.name
            so, sn = sha256(p), (sha256(q) if q.exists() else None)
            L.append(f"| `{p.name}` | `{so[:16]}...` | `{sn[:16] + '...' if sn else 'missing'}` | {'yes' if so == sn else 'no'} |")
        L.append("\nPickled models can differ in bytes while making identical predictions (pickle stores object ids and dict order). The metrics above are the comparison that matters.\n")

    if a.run_log and Path(a.run_log).exists():
        tail = Path(a.run_log).read_text(errors="ignore").strip().splitlines()[-6:]
        L.append("## End of the run log\n\n```\n" + "\n".join(tail) + "\n```\n")
    if a.extra and Path(a.extra).exists(): L.append(Path(a.extra).read_text())
    Path(a.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {a.out}: {same_n}/{len(HEADLINE)} Review-3 figures the same; {len(diffs)} differing values")


if __name__ == "__main__":
    sys.exit(main())
