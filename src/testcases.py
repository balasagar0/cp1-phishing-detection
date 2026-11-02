"""Review-2 test-case file: reader, validator, bundle builder, assumption check, time-window suggestion.
File format is documented in TESTCASE_FORMAT.md (one row per event; Excel sheet 'Events' or CSV)."""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
import pandas as pd
from fusion import bundle_features, ASSUMPTIONS

COLS = ["bundle_id", "event_id", "channel", "time", "identity", "subject", "content", "event_label", "campaign_id", "source_type", "basis", "notes", "detector_score"]
REQUIRED = ["bundle_id", "channel", "time", "content", "event_label", "source_type"]
CHANNELS, SCORED = ("email", "sms", "url", "call"), ("email", "sms", "url")
LABELS, SOURCES = ("malicious", "benign"), ("lab_simulation", "collected_real", "public_dataset", "example")
REAL_TIMING = ("lab_simulation", "collected_real")     # sources whose timestamps reflect real behaviour
_TZ = re.compile(r"(?:Z|[+-]\d\d:?\d\d)\s*$")


def defang(s):
    s = re.sub(r"\bhxxp(s?)://", r"http\1://", str(s), flags=re.I)
    return s.replace("[.]", ".").replace("(.)", ".").replace("[:]", ":")


def read_table(path):
    p = Path(path)
    df = pd.read_excel(p, sheet_name="Events", dtype=str) if p.suffix.lower() in (".xlsx", ".xlsm") else pd.read_csv(p, dtype=str, keep_default_na=False)
    df.columns = [str(c).strip().lower() for c in df.columns]
    df["_row"] = np.arange(len(df)) + 2                     # spreadsheet row number, for error messages
    df = df.fillna("")
    for c in df.columns:
        if c != "_row": df[c] = df[c].astype(str).str.strip()
    known = [c for c in COLS if c in df.columns]
    return df[~(df[known] == "").all(axis=1)].reset_index(drop=True)


def validate(df, allow_examples=False):
    """Returns (clean_df, issues). issues = list of (level, row, message); level 'error' blocks use of the file."""
    issues = []
    E = lambda r, m: issues.append(("error", int(r), m))
    W = lambda r, m: issues.append(("warning", int(r), m))
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        return df.iloc[0:0], [("error", 0, "missing column(s): " + ", ".join(missing))]
    df = df.copy()
    for c in COLS:
        if c not in df.columns: df[c] = ""
    for c in ("channel", "event_label", "source_type"): df[c] = df[c].str.lower()
    n_ex = int((df.source_type == "example").sum())
    if not allow_examples: df = df[df.source_type != "example"]
    df = df.reset_index(drop=True)
    for c in REQUIRED:
        for r in df._row[df[c] == ""]: E(r, f"'{c}' is empty")
    for c, ok in (("channel", CHANNELS), ("event_label", LABELS), ("source_type", SOURCES)):
        for r, v in zip(df._row[(df[c] != "") & ~df[c].isin(ok)], df[c][(df[c] != "") & ~df[c].isin(ok)]): E(r, f"'{c}' = '{v}' is not one of {', '.join(ok)}")
    t = pd.to_datetime(df.time, errors="coerce", utc=True, format="mixed")
    for r in df._row[t.isna() & (df.time != "")]: E(r, "'time' cannot be read as a date-time (use e.g. 2026-11-03T14:05:00+05:30)")
    notz = (df.time != "") & ~df.time.str.contains(_TZ)
    if notz.any(): W(df._row[notz].iloc[0], f"{int(notz.sum())} time value(s) have no timezone; treated as UTC (fine if the whole file uses one clock)")
    df["t_utc"] = t
    for r in df._row[(df.event_label == "malicious") & (df.campaign_id == "")]: E(r, "malicious event needs a campaign_id")
    for r in df._row[(df.event_label == "benign") & (df.campaign_id != "")]: W(r, "benign event has a campaign_id (ignored)")
    for r in df._row[(df.source_type == "collected_real") & (df.basis == "")]: E(r, "collected_real rows need 'basis' (own account / participant consent)")
    ds = pd.to_numeric(df.detector_score.replace("", np.nan), errors="coerce")
    for r in df._row[(df.detector_score != "") & (ds.isna() | (ds < 0) | (ds > 1))]: E(r, "'detector_score' must be a number between 0 and 1")
    ev = df[df.event_id != ""]
    for r in ev._row[ev.event_id.duplicated(keep=False)]: E(r, "duplicate event_id")
    for r in df._row[(df.channel == "url") & ~df.content.str.contains(r"\.")]: W(r, "url content has no dot; is it a URL or domain?")
    for r in df._row[df.channel == "call"][:1]: W(r, f"{int((df.channel == 'call').sum())} call event(s) are kept for the record but not scored (no voice detector yet)")
    d = df.assign(_k=df.channel + "|" + df.content.str.lower().map(lambda x: re.sub(r"\W+", "", x)))
    dup = d[d.duplicated("_k", keep=False)].groupby("_k").filter(lambda g: g.bundle_id.nunique() > 1)
    for r in dup._row[:3]: W(r, "same message appears in more than one bundle (split by campaign_id to avoid leakage)")
    for bid, g in df.groupby("bundle_id"):
        if g.t_utc.notna().all() and (g.t_utc.max() - g.t_utc.min()) > pd.Timedelta(days=14): W(g._row.iloc[0], f"bundle {bid} spans more than 14 days (typo in a date?)")
        if g.source_type.nunique() > 1: W(g._row.iloc[0], f"bundle {bid} mixes source types")
    df["content"] = df.content.map(defang); df["identity"] = df.identity.map(defang)
    if n_ex and not allow_examples: issues.append(("info", 0, f"{n_ex} example row(s) ignored"))
    return df, issues


def build_bundles(df, detectors=None):
    """One dict per bundle: scored events (channel, score, ids, t in minutes), truth labels, CV group."""
    from predict import extract_ids
    out = []
    for bid, g in df.groupby("bundle_id", sort=False):
        g = g.sort_values("t_utc"); t0 = g.t_utc.min(); mal = g.event_label == "malicious"
        coord = any(gc.channel.nunique() >= 2 for _, gc in g[mal].groupby("campaign_id"))
        ev = []
        for _, r in g.iterrows():
            if r.channel not in SCORED: continue
            s = float(r.detector_score) if r.detector_score != "" else detectors.score(r.channel, r.content, r.subject)["score"]
            ev.append({"channel": r.channel, "score": s, "ids": extract_ids(r.channel, r.content, r.identity), "t": (r.t_utc - t0).total_seconds() / 60.0, "label": r.event_label})
        if not ev: continue
        camp = sorted(set(g.campaign_id[mal]))
        out.append({"bundle_id": bid, "group": camp[0] if camp else str(bid), "events": ev, "n_calls": int((g.channel == "call").sum()), "malicious": int(mal.any()),
                    "coordinated": int(coord), "sources": sorted(set(g.source_type)), "x": bundle_features(ev)})
    return out


def assumption_check(bundles):
    """Measured value vs what the simulation (fusion.simulate) assumed; the 'implied' numbers are computed, not typed."""
    import json
    from common import REPORTS
    rng = np.random.default_rng(0); n = 20000
    k = np.where(rng.random(n) < .6, 2, 3); span = np.array([rng.exponential(15, kk - 1).sum() for kk in k])        # attack_linked: 2-3 events, gaps ~ Exp(15 min)
    obs_all = np.mean(np.where(k == 2, .85 ** 2, .85 ** 3 + 3 * .85 ** 2 * .15))                                      # P(at least two events share an observed identity)
    mix = ASSUMPTIONS["bundle_mix"]; bl, bu2 = mix["benign_linked"], mix["benign_unlinked"] * .7                        # benign_unlinked has 2+ events with prob .7; spurious link prob .08
    try: weak = json.load(open(REPORTS / "fusion_metrics.json"))["campaigns_missed_by_every_single_channel_filter"]["share_of_linked_attacks"]
    except Exception: weak = None
    co = [b for b in bundles if b["coordinated"]]; rows = []
    if co:
        rows.append(("Coordinated bundles whose events share an identity", f"{100 * np.mean([b['x'][11] > 0 for b in co]):.0f}% (n={len(co)})", f"{100 * obs_all:.0f}%"))
        sp = np.array([max(e["t"] for e in b["events"]) for b in co])
        rows.append(("Time span of coordinated bundles, mean / median (minutes)", f"{sp.mean():.0f} / {np.median(sp):.0f}", f"{span.mean():.0f} / {np.median(span):.0f}"))
        rows.append(("Coordinated bundles where every event scores below 0.5", f"{100 * np.mean([max(e['score'] for e in b['events']) < .5 for b in co]):.0f}%", f"{100 * weak:.1f}%" if weak is not None else "n/a"))
    be = [b for b in bundles if not b["malicious"] and len(b["events"]) >= 2]
    if be: rows.append(("Benign bundles with 2+ events that share an identity", f"{100 * np.mean([b['x'][11] > 0 for b in be]):.0f}% (n={len(be)})", f"{100 * (bl + bu2 * .08) / (bl + bu2):.0f}%"))
    return rows


def suggest_window(bundles, B=1000, seed=42):
    """Data-driven time-clustering window: 90th percentile of the time span of coordinated bundles with real timing."""
    sp = np.array([max(e["t"] for e in b["events"]) for b in bundles if b["coordinated"] and set(b["sources"]) <= set(REAL_TIMING)])
    if len(sp) < 20: return {"n": int(len(sp)), "window_minutes": None, "note": "need at least 20 coordinated bundles with lab_simulation or collected_real timing"}
    rng = np.random.default_rng(seed); p90 = [np.percentile(rng.choice(sp, len(sp)), 90) for _ in range(B)]
    return {"n": int(len(sp)), "median": float(np.median(sp)), "p90": float(np.percentile(sp, 90)), "p90_ci95": [float(np.percentile(p90, 2.5)), float(np.percentile(p90, 97.5))],
            "window_minutes": float(np.ceil(np.percentile(sp, 90) / 5) * 5), "note": "90th percentile of coordinated-bundle time span, rounded up to 5 minutes"}
