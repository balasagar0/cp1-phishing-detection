"""reports/FINAL_NUMBERS.md and reports/final_numbers.json: one set of numbers for everything written about CP1 (R3-12, R3-08, R3-17).
  python scripts/make_final_numbers.py [--reuse-tests]
Every number is read from reports/ (or measured here: the tests and the demo cases), never typed. The script refuses to run unless the
API, the models and the training code are byte for byte those of the tag cp1-final.
--reuse-tests  reuse reports/test_run.json instead of running pytest and the smoke test again (only if it was written on this build).
final_numbers.json holds every figure as a formatted string under "values"; scripts/render_docs.py fills the document templates from it.
The retired list below is quoted only as wrong; the search for it covers every tracked file and the team's text inputs."""
import argparse, datetime, json, re, subprocess, sys, tempfile, warnings
import xml.etree.ElementTree as ET
from pathlib import Path
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]; sys.path[:0] = [str(ROOT), str(ROOT / "src")]
R = ROOT / "reports"
TAG = "cp1-final"
RUNTIME = ["api.py", "src", "models", "console/dist", "console.html", "requirements.txt", "requirements.lock.txt"]

# Numbers retired by the brief (section "Retired numbers"). Quoted here only as wrong. Patent Tables 2 and 3 are not listed: the old
# specification is not used (owner, 7 Nov 2026).
RETIRED = [("email F1 0.947 (Review-2 deck)", r"(?<![\d.])0\.947(?!\d)"), ("SMS F1 0.926 (Review-2 deck)", r"(?<![\d.])0\.926(?!\d)"),
           ("URL F1 0.960 (Review-2 deck)", r"(?<![\d.])0\.960(?!\d)"), ("F1 0.991 (TRAINING_REPORT.md)", r"(?<![\d.])0\.991(?!\d)"),
           ("'linear SVM' (TRAINING_REPORT.md)", r"(?i)linear[ -]svm"), ("'460 campaigns'", r"460 campaigns"),
           ("'80.0% -> 84.5%'", r"84\.5 ?%"), ("'22 of 60'", r"\b22 of 60\b"), ("'32 of 60'", r"\b32 of 60\b"),
           ("'142 cases'", r"\b142[ -](?:test )?cases?\b"), ("'30-minute window'", r"(?i)\b30[ -]min(?:ute)?s?[ -]window"),
           ("'50-minute window'", r"(?i)\b50[ -]min(?:ute)?s?[ -]window"), ("quiet-attack demo score 87.8", r"(?<![\d.])87\.8(?!\d)"),
           ("quiet-attack demo score 85.6", r"(?<![\d.])85\.6(?!\d)"), ("voice ROC-AUC 0.952", r"(?<![\d.])0\.952(?!\d)"), ("'19 routes'", r"\b19 (?:API )?routes\b")]
# Files that quote the retired numbers as wrong, on purpose.
QUOTES_AS_WRONG = {"CLAUDE.md", "CP1_FINISH_TASK.md", "scripts/make_final_numbers.py", "reports/FINAL_NUMBERS.md", "reports/final_numbers.json", "tests/test_documents.py"}
TEXT = {".md", ".txt", ".py", ".json", ".jsx", ".js", ".html", ".bat", ".sh", ".csv", ".mmd", ".toml", ".cfg", ".ini", ".yml", ".yaml"}


def git(*a): return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()
def jl(p): return json.loads(Path(p).read_text(encoding="utf-8"))
pct = lambda x: f"{100 * x:.1f}%"
num = lambda x: f"{x:,}"
dec = lambda x, d=3: f"{x:.{d}f}"


def check_build():
    commit = git("rev-parse", f"{TAG}^{{commit}}")
    if not commit: sys.exit(f"tag {TAG} not found")
    changed = git("diff", "--name-only", TAG, "--", *RUNTIME).splitlines() + git("status", "--porcelain", "--", *RUNTIME).splitlines()
    if changed: sys.exit("the runtime differs from " + TAG + ": " + ", ".join(changed[:10]))
    return {"tag": TAG, "commit": commit, "commit7": commit[:7], "tag_date": git("log", "-1", "--format=%cd", "--date=format:%d %b %Y", commit),
            "head": git("rev-parse", "HEAD")[:7], "runtime_paths": RUNTIME}


def run_tests(reuse):
    out = R / "test_run.json"
    if reuse and out.exists():
        t = jl(out)
        if t["build"]["commit"] == git("rev-parse", f"{TAG}^{{commit}}"): return t
        sys.exit("reports/test_run.json was written on another build; run without --reuse-tests")
    keep = {p: p.read_bytes() for p in R.rglob("*") if p.is_file()}   # pytest's test_final_cases.py rewrites its results file; the committed cp1-final run stays
    with tempfile.TemporaryDirectory() as d:
        xmlp = Path(d) / "pytest.xml"
        try:
            subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider", "--ignore=tests/test_documents.py", f"--junitxml={xmlp}"],
                           cwd=ROOT, capture_output=True, text=True)
        finally:
            for p, b in keep.items():
                if not p.exists() or p.read_bytes() != b: p.write_bytes(b)
        c = {"passed": 0, "failed": 0, "error": 0, "skipped": 0, "xfailed": 0, "xpassed": 0}
        for tc in ET.parse(xmlp).getroot().iter("testcase"):
            kids = {k.tag: k for k in tc}
            if "failure" in kids: c["failed"] += 1
            elif "error" in kids: c["error"] += 1
            elif "skipped" in kids: c["xfailed" if "xfail" in (kids["skipped"].get("type") or "") else "skipped"] += 1
            else: c["passed"] += 1
    sm = subprocess.run([sys.executable, "tests/smoke_test.py"], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
    smoke = {k.lower(): sum(1 for l in sm if l.startswith(k + " ")) for k in ("PASS", "SKIP", "FAIL")}
    smoke["all_passed"] = any(l.strip() == "ALL PASSED" for l in sm)
    t = {"date": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "build": {"tag": TAG, "commit": git("rev-parse", f"{TAG}^{{commit}}")},
         "pytest": c, "pytest_note": "pytest tests, except tests/test_documents.py (it checks the documents this script feeds)", "smoke": smoke}
    out.write_text(json.dumps(t, indent=1) + "\n", encoding="utf-8")
    return t


def run_demo():
    import api
    from demo_cases import CASES, STORIES
    from fastapi.testclient import TestClient
    c = TestClient(api.app); rows = []
    for kind, src in (("demo case", CASES), ("Indian story", STORIES)):
        for cid, case in src.items():
            j = c.post("/correlate", json={"events": case["events"]}).json()
            br = j.get("bundle_risk")
            rows.append({"id": cid, "kind": kind, "name": case["name"], "status": j.get("status"), "channels": [e["channel"] for e in case["events"]],
                         "event_scores": [None if e.get("score") is None else round(e["score"], 3) for e in j.get("events", [])],
                         "single_channel_alert": j.get("single_channel_alert"), "bundle_risk": None if br is None else round(br, 3),
                         "alert": (br is not None and br >= 0.5)})
    return rows


def retired_search():
    v2 = set(git("ls-tree", "-r", "--name-only", "v2-baseline").splitlines())
    files = [f for f in git("ls-files").splitlines() if Path(f).suffix.lower() in TEXT and not f.startswith("console/dist/")]
    inputs = [str(p.relative_to(ROOT)).replace("\\", "/") for p in (ROOT / "docs" / "inputs").rglob("*") if p.is_file() and p.suffix.lower() in TEXT]
    hits = []
    for f in files + inputs:
        try: text = (ROOT / f).read_text(encoding="utf-8", errors="replace")
        except OSError: continue
        for name, rx in RETIRED:
            for m in re.finditer(rx, text):
                line = text.count("\n", 0, m.start()) + 1
                if f in inputs: origin = "team input (docs/inputs, not in git)"
                elif f in v2: origin = "received with v2, unchanged" if not git("diff", "--name-only", "v2-baseline", "--", f) else "received with v2, regenerated since"
                else: origin = "written in the CP1 finish work"
                if f in QUOTES_AS_WRONG: kind = "quotes it as wrong"
                elif f.startswith("reports/"): kind = "written by code: a different measured value with the same digits, not the retired claim"
                elif origin in ("team input (docs/inputs, not in git)", "received with v2, unchanged"): kind = "received, not edited"
                else: kind = "needs a look"
                hits.append({"number": name, "file": f, "line": line, "origin": origin, "verdict": kind})
    return {"searched_files": len(files) + len(inputs), "hits": hits}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--reuse-tests", action="store_true"); a = ap.parse_args()
    B = check_build(); T = run_tests(a.reuse_tests); DEMO = run_demo(); RS = retired_search()
    E, S, U = jl(R / "email_metrics.json"), jl(R / "sms_metrics.json"), jl(R / "url_metrics.json")
    FU, W, CM = jl(R / "fusion_metrics.json"), jl(R / "window_metrics.json"), jl(R / "comparison_metrics.json")
    FC, DS, EX = jl(R / "final_cases_results.json"), jl(R / "defect_status.json"), jl(R / "exit_criteria.json")
    BM, E2E, UI, OFF, N5 = jl(R / "benchmark.json"), jl(R / "e2e_check.json"), jl(R / "ui_checks.json"), jl(R / "offline_check.json"), jl(R / "nfr05_fresh_clone.json")
    V3, FRX, REG = jl(R / "candidates" / "email_candidates_v3.json"), jl(R / "final_run" / "tc_cross_check.json"), jl(ROOT / "docs" / "defect_registry.json")
    WB = jl(ROOT / "tests" / "data" / "workbook_cases.json")
    V = {}
    def put(k, v): assert k not in V, k; V[k] = v
    def metr(prefix, m, ci=None):
        for k, f in (("precision", pct), ("recall", pct), ("f1", pct), ("false_positive_rate", pct), ("accuracy", pct)): put(f"{prefix}.{k if k != 'false_positive_rate' else 'fpr'}", f(m[k]))
        put(f"{prefix}.auc", dec(m["roc_auc"], 4)); [put(f"{prefix}.{k}", num(m[k])) for k in ("n", "positives", "tn", "fp", "fn", "tp")]
        if ci: put(f"{prefix}.f1_ci", f"{pct(ci['f1'][0])}-{pct(ci['f1'][1])}"); put(f"{prefix}.f1_ci_low", pct(ci["f1"][0])); put(f"{prefix}.f1_ci_high", pct(ci["f1"][1]))

    # build and settings
    for k in ("tag", "commit", "commit7", "tag_date", "head"): put(f"build.{k}", B[k])
    src = (ROOT / "src" / "fusion.py").read_text(encoding="utf-8").splitlines()
    wl = next(i for i, l in enumerate(src, 1) if l.startswith("DEFAULT_WINDOW_MIN"))
    put("window.minutes", f"{W['default_window_minutes']:g}"); put("window.file_line", f"src/fusion.py:{wl}"); put("alert_line", f"{W['alert_line']:g}")
    uses = []
    for f in ["api.py"] + sorted(str(p.relative_to(ROOT)).replace("\\", "/") for p in (ROOT / "src").glob("*.py")):
        for i, l in enumerate((ROOT / f).read_text(encoding="utf-8").splitlines(), 1):
            if "DEFAULT_WINDOW_MIN" in l and not l.startswith("DEFAULT_WINDOW_MIN"): uses.append(f"{f}:{i}")
    put("window.used_at", ", ".join(f"`{u}`" for u in uses))

    # email
    lo = E["leave_one_corpus_out"]; corp = list(lo)
    put("email.n", num(E["data"]["dedupe"]["rows_after"])); put("email.n_before", num(E["data"]["dedupe"]["rows_before"])); put("email.corpora", ", ".join(corp))
    put("email.n_corpora", str(len(corp))); put("email.kept_terms", num(E["data"]["kept_terms"])); put("email.candidate_terms", num(E["data"]["candidate_terms"]))
    put("email.chosen_C", f"{E['chosen_C']:g}")
    for c in corp: metr(f"email.loco.{c}", lo[c])
    put("email.honest.f1", pct(sum(lo[c]["f1"] for c in corp) / len(corp)))
    put("email.honest.fpr_range", f"{pct(min(lo[c]['false_positive_rate'] for c in corp))} to {pct(max(lo[c]['false_positive_rate'] for c in corp))}")
    put("email.honest.recall_range", f"{pct(min(lo[c]['recall'] for c in corp))} to {pct(max(lo[c]['recall'] for c in corp))}")
    put("email.honest.auc_range", f"{dec(min(lo[c]['roc_auc'] for c in corp), 2)} to {dec(max(lo[c]['roc_auc'] for c in corp), 2)}")
    metr("email.flattering", E["pooled_test"], E["pooled_test_ci95"])
    lg = V3["legit_sources_false_alarms"]
    put("email.realmail.n", num(lg["OwnInbox"]["n"])); put("email.realmail.fpr", pct(lg["OwnInbox"]["live_v2"]))
    put("email.generatedlegit.n", num(lg["GeneratedLegit"]["n"])); put("email.generatedlegit.fpr", pct(lg["GeneratedLegit"]["live_v2"]))
    put("email.retrain_attempts", str(len(list((R / "candidates").glob("email_candidates*.json")))))

    # SMS
    cc = S["data"]["class_counts"]
    put("sms.n", num(S["data"]["dedupe"]["rows_after"])); [put(f"sms.count.{k}", num(v)) for k, v in cc.items()]
    put("sms.test_n", num(S["data"]["split"]["test"])); put("sms.smishing_support", num(S["test_smishing_vs_rest"]["positives"]))
    metr("sms.honest", S["test_smishing_vs_rest"], S["test_smishing_vs_rest_ci95"]); metr("sms.flattering", S["test_unwanted_vs_ham"], S["test_unwanted_vs_ham_ci95"])
    put("sms.macro_f1_3class", pct(S["test_3class"]["macro_f1"]))

    # URL
    sm, ab, fb = U["string_model"], U["string_model"]["ablation"], U["feature_benchmark"]
    put("url.n", num(sm["data"]["rows_used"])); put("url.hosts", num(sm["data"]["unique_hosts"])); put("url.train", num(sm["data"]["train"])); put("url.test", num(sm["data"]["test"]))
    put("url.popular_domains", num(sm["data"]["popularity_list_domains"]))
    metr("url.honest", sm["grouped_test"], sm["grouped_test_ci95"]); metr("url.flattering", fb["hgb_all_features"])
    put("url.flattering.n_features", str(fb["data"]["n_features_all"]))
    a0, c0 = ab["a_ngrams_only"], ab["c_plus_login_training_urls_FINAL"]
    put("url.login_fpr.before", pct(a0["false_positive_rate_on_login_urls_of_1000_held_out_popular_domains"])); put("url.login_fpr.after", pct(c0["false_positive_rate_on_login_urls_of_1000_held_out_popular_domains"]))
    put("url.popular_recall.before", pct(a0["recall_on_bad_urls_hosted_on_top10k_domains"]["recall"])); put("url.popular_recall.after", pct(c0["recall_on_bad_urls_hosted_on_top10k_domains"]["recall"]))
    put("url.popular_recall.n", num(c0["recall_on_bad_urls_hosted_on_top10k_domains"]["n"]))
    put("url.brand_probes.before", pct(a0["detection_rate_on_2000_brand_impersonation_probes"])); put("url.brand_probes.after", pct(c0["detection_rate_on_2000_brand_impersonation_probes"]))

    # correlation (SIMULATED)
    put("corr.n_train", num(FU["n_bundles"]["train"])); put("corr.n_val", num(FU["n_bundles"]["val"])); put("corr.n_test", num(FU["n_bundles"]["test"]))
    put("corr.malicious_share", pct(FU["positive_share_test"]))
    names = {"single_channel": "single", "parallel_multichannel": "parallel", "whole_bundle_model": "whole", "deployed_engine_60min": "engine"}
    for k, short in names.items():
        m = CM["rows"][k]
        for f in ("precision", "recall", "f1"): put(f"corr.{short}.{f}", pct(m[f]))
        put(f"corr.{short}.fpr", pct(m["false_positive_rate"])); put(f"corr.{short}.f1_ci", f"{pct(m['ci95']['f1'][0])}-{pct(m['ci95']['f1'][1])}")
        put(f"corr.{short}.fpr_ci", f"{pct(m['ci95']['false_positive_rate'][0])}-{pct(m['ci95']['false_positive_rate'][1])}"); put(f"corr.{short}.hard_flagged", pct(m["hard_campaigns_flagged"]))
    nw = W["engine_no_window_at_0.5"]
    for f in ("precision", "recall", "f1"): put(f"corr.nowindow.{f}", pct(nw[f]))
    put("corr.nowindow.fpr", pct(nw["false_positive_rate"]))
    hc = FU["campaigns_missed_by_every_single_channel_filter"]
    put("corr.hard.n", str(hc["n"])); put("corr.hard.share", pct(hc["share_of_linked_attacks"]))
    put("corr.fit60", pct(W["share_of_bundles_that_fit_in_one_default_window"]["attack_linked"]))
    put("corr.auc.single", dec(FU["auc"]["single_channel_max_score"], 4)); put("corr.auc.nocorr", dec(FU["auc"]["fusion_without_correlation_features"], 4)); put("corr.auc.fusion", dec(FU["auc"]["fusion"], 4))
    put("corr.patent_row", CM["rows"]["patent_noisy_or"]["status"]); put("corr.real_bundles", CM["real_bundles"])
    from fusion import FEATURE_NAMES, CORR_COLS
    put("corr.n_features", str(len(FEATURE_NAMES))); put("corr.features", ", ".join(f"`{f}`" for f in FEATURE_NAMES))
    put("corr.n_link_features", str(len(CORR_COLS))); put("corr.link_features", ", ".join(f"`{FEATURE_NAMES[i]}`" for i in CORR_COLS))
    for k, v in FU["assumptions"]["bundle_mix"].items(): put(f"sim.mix.{k}", pct(v))
    for k in ("label", "attack_linked", "benign_linked", "unlinked_bundles", "scores"): put(f"sim.assume.{k}", FU["assumptions"][k])
    for k, v in sm["data"]["constructed_sets"].items(): put(f"url.constructed.{k}", num(v))
    put("sms.chosen_C", f"{S['chosen_C']:g}")
    for k in ("train", "val", "test"): put(f"email.split.{k}", num(E["data"]["split"][k]))
    t6 = FRX["TC-06"]
    put("finalrun.build", FRX["build"]); put("finalrun.tc06.live", dec(t6["live detectors + live correlation"])); put("finalrun.tc06.retrained", dec(t6["retrained detectors + retrained correlation"]))
    put("finalrun.tc06.live_corr_new_det", dec(t6["retrained detectors + live correlation"]))
    put("finalrun.email_f1.live", pct(FRX["email_loco_mean_f1"]["live"])); put("finalrun.email_f1.retrained", pct(FRX["email_loco_mean_f1"]["retrained"]))
    put("finalrun.sim_f1.live", pct(FRX["simulated_f1_60min"]["live"])); put("finalrun.sim_f1.retrained", pct(FRX["simulated_f1_60min"]["retrained"]))

    # demo cases
    for r in DEMO:
        p = f"demo.{r['id']}"
        put(f"{p}.name", r["name"]); put(f"{p}.status", r["status"] or "")
        put(f"{p}.scores", " / ".join("not assessed" if s is None else dec(s) for s in r["event_scores"]) or "not assessed")
        put(f"{p}.bundle", "CANNOT_ASSESS" if r["bundle_risk"] is None else dec(r["bundle_risk"]))
        put(f"{p}.alone", "not assessed" if r["single_channel_alert"] is None else ("yes" if r["single_channel_alert"] else "no"))
        put(f"{p}.alert", "not assessed" if r["bundle_risk"] is None else ("alert" if r["alert"] else "no alert"))

    # tests and checks
    pt, smk = T["pytest"], T["smoke"]
    put("tests.pytest.passed", str(pt["passed"])); put("tests.pytest.xfailed", str(pt["xfailed"])); put("tests.pytest.skipped", str(pt["skipped"])); put("tests.pytest.failed", str(pt["failed"] + pt["error"]))
    put("tests.pytest.total", str(sum(pt.values()))); put("tests.smoke.passed", str(smk["pass"])); put("tests.smoke.skipped", str(smk["skip"])); put("tests.smoke.failed", str(smk["fail"]))
    st = {}
    for cdata in FC["cases"].values(): st[cdata["status"]] = st.get(cdata["status"], 0) + 1
    put("tests.cases.total", str(len(FC["cases"]))); [put(f"tests.cases.{k.lower().replace(' ', '_').replace('/', '')}", str(v)) for k, v in sorted(st.items())]
    tags = {}
    for cdata in FC["cases"].values(): tags[cdata["tag"]] = tags.get(cdata["tag"], 0) + 1
    [put(f"tests.cases.tag.{k.lower().replace('/', '')}", str(v)) for k, v in sorted(tags.items())]
    put("tests.cases.build", FC["run"]["describe"]); put("tests.samples.n", str(len(FC["samples"]))); put("tests.scenarios.n", str(len(FC["scenarios"])))
    put("tests.exit.met", str(EX["met"])); put("tests.exit.of", str(EX["of"]))
    for c in EX["criteria"]: put(f"tests.exit.{c['n']}", ("met" if c["met"] else "not met") + f": {c['current']}"); put(f"tests.exit.{c['n']}.current", c["current"])
    put("tests.e2e.steps", str(len(E2E["steps"]))); put("tests.e2e.passed", str(sum(s["ok"] for s in E2E["steps"])))
    uic = {k: v for k, v in UI.items() if k.startswith("UI-")}
    put("tests.ui.n", str(len(uic))); put("tests.ui.passed", str(sum(1 for v in uic.values() if v.get("status") == "Pass")))
    put("tests.ui.failed", ", ".join(k for k, v in uic.items() if v.get("status") != "Pass") or "none")
    put("tests.offline", "pass" if OFF.get("ok", OFF.get("passed")) else "fail"); put("tests.nfr05", N5.get("status", "unknown"))
    dd = DS["defects"]; sev = lambda d: REG.get(d, {}).get("severity") if REG.get(d, {}).get("new") else next((x["Severity"] for x in WB["defects"] if x["Defect ID"] == d), "")
    put("defects.total", str(len(dd))); put("defects.open", str(sum(1 for d in dd.values() if d["status"] == "Open"))); put("defects.closed", str(sum(1 for d in dd.values() if d["status"] == "Closed")))
    put("defects.open_list", ", ".join(f"{d} ({sev(d)})" for d, x in dd.items() if x["status"] == "Open"))
    put("defects.closed_list", ", ".join(d for d, x in dd.items() if x["status"] == "Closed"))

    # latency
    for ch, m in BM["per_channel"].items(): put(f"latency.{ch}.median", f"{m['median_ms']:.0f} ms"); put(f"latency.{ch}.p95", f"{m['p95_ms']:.0f} ms"); put(f"latency.{ch}.max", f"{m['max_ms']:.0f} ms")
    fcb = BM["full_case"]; put("latency.case.median", f"{fcb['median_ms']:.0f} ms"); put("latency.case.p95", f"{fcb['p95_ms']:.0f} ms"); put("latency.case.max", f"{fcb['max_ms']:.0f} ms")
    put("latency.n", str(BM["n_per_channel"])); put("latency.startup", f"{BM['startup_s']:.1f} s"); put("latency.machine", BM["machine"]); put("latency.demo_laptop", BM["demo_laptop"])

    doc = {"date": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "build": B, "values": V, "demo": DEMO, "tests": T, "retired_search": RS,
           "retired_list": [n for n, _ in RETIRED]}
    (R / "final_numbers.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    write_md(doc, E, S, U, FU, W, CM, FC, DS, EX, uic)
    print(f"wrote reports/FINAL_NUMBERS.md and reports/final_numbers.json: {len(V)} values; retired-number hits {len(RS['hits'])} "
          f"(needs a look: {sum(h['verdict'] == 'needs a look' for h in RS['hits'])})")


def verdicts(hits):
    out = {}
    for h in hits: out[h["verdict"]] = out.get(h["verdict"], 0) + 1
    return out


def case_counts(FC):
    out = {}
    for c in FC["cases"].values(): out[c["status"]] = out.get(c["status"], 0) + 1
    return out


def write_md(doc, E, S, U, FU, W, CM, FC, DS, EX, uic):
    V, B = doc["values"], doc["build"]; g = lambda k: V[k]
    hdr = "| Measure | n | Precision | Recall | F1 | False-positive rate | ROC-AUC | TN / FP / FN / TP |\n|---|---|---|---|---|---|---|---|"
    row = lambda label, p: f"| {label} | {g(p + '.n')} | {g(p + '.precision')} | {g(p + '.recall')} | {g(p + '.f1')} | {g(p + '.fpr')} | {g(p + '.auc')} | {g(p + '.tn')} / {g(p + '.fp')} / {g(p + '.fn')} / {g(p + '.tp')} |"
    L = ["# Final numbers (CP1)\n",
         f"**Build: tag `{B['tag']}`, commit `{B['commit']}` ({B['tag_date']}).** Written by `scripts/make_final_numbers.py` on {doc['date']}. "
         f"Every number is read from `reports/` or measured by that script on this build; none is typed. The script checks that the API, models and training code "
         f"({', '.join('`' + p + '`' for p in B['runtime_paths'])}) are byte for byte those of `{B['tag']}` before it writes anything.\n",
         "Quote the honest number. Never quote the flattering one alone. Simulated results are always called simulated. Demo cases are hand-written, not a test set.\n",
         "## 1. Detectors\n", "### Email (TF-IDF word 1-2-grams, numbers masked, logistic regression)\n",
         f"{g('email.n')} emails from {g('email.n_corpora')} corpora ({g('email.corpora')}) after cleaning and de-duplication. A term is kept only if it appears in at least two corpora "
         f"({g('email.kept_terms')} of {g('email.candidate_terms')} candidate terms).\n",
         f"**Honest: F1 {g('email.honest.f1')}**, the mean of {g('email.n_corpora')} leave-one-corpus-out runs (train on two corpora, test on the third).\n", hdr]
    L += [row(f"Held out: {c}", f"email.loco.{c}") for c in E["leave_one_corpus_out"]]
    L += [row("**Flattering:** pooled random split", "email.flattering"), f"\nThe pooled split's F1 95% CI is {g('email.flattering.f1_ci')}. It is flattering because each corpus has its own style.\n",
          f"On real mail: the live email model flags {g('email.realmail.fpr')} of {g('email.realmail.n')} legitimate emails from the account owner's own mailbox, and "
          f"{g('email.generatedlegit.fpr')} of {g('email.generatedlegit.n')} generated legitimate transactional emails (`reports/candidates/email_candidates_v3.json`, one class only: false-positive rate). "
          f"{g('email.retrain_attempts')} retrain attempts failed the adoption rule; v2's email model stays live.\n",
          "### SMS (three classes: ham, spam, smishing)\n",
          f"{g('sms.n')} messages: {g('sms.count.ham')} ham, {g('sms.count.spam')} spam, {g('sms.count.smishing')} smishing. Test split {g('sms.test_n')} messages, of which {g('sms.smishing_support')} smishing. "
          "The alert score is 1 - P(ham).\n", f"**Honest: smishing-vs-rest F1 {g('sms.honest.f1')} (95% CI {g('sms.honest.f1_ci')}).**\n", hdr,
          row("**Honest:** smishing vs rest", "sms.honest"), row("**Flattering:** spam or smishing vs ham", "sms.flattering"),
          f"\nThree-class macro F1: {g('sms.macro_f1_3class')}. Few smishing examples, so the interval is wide.\n",
          "### URL (character n-grams on the URL text, 3 popularity flags, logistic regression; no network lookups)\n",
          f"{g('url.n')} URLs on {g('url.hosts')} hosts, split 80/20 by host so no host is in both halves ({g('url.train')} train, {g('url.test')} test).\n",
          f"**Honest: host-grouped F1 {g('url.honest.f1')} (95% CI {g('url.honest.f1_ci')}).**\n", hdr,
          row("**Honest:** host-grouped test", "url.honest"), row(f"**Flattering:** offline feature benchmark, random split, {g('url.flattering.n_features')} features", "url.flattering"),
          f"\nThe login-page trade-off: false alarms on login URLs of 1,000 held-out popular domains fell from {g('url.login_fpr.before')} to {g('url.login_fpr.after')}; "
          f"recall on bad URLs hosted on top-10k domains fell from {g('url.popular_recall.before')} to {g('url.popular_recall.after')} (n = {g('url.popular_recall.n')}); "
          f"detection of brand-impersonation probes went from {g('url.brand_probes.before')} to {g('url.brand_probes.after')}. Quote both halves.\n",
          "### Voice and video\n", "Not trained. No accessible data. `/score` answers HTTP 501 for them; `/correlate` and `/events` mark calls 'not assessed' (`CANNOT_ASSESS`). Never SAFE.\n",
          "## 2. Correlation (SIMULATED bundles)\n",
          f"Trained on {g('corr.n_train')} simulated bundles, tuned on {g('corr.n_val')}, tested on {g('corr.n_test')} ({g('corr.malicious_share')} malicious). "
          "The events are real held-out messages; the links between them are constructed. No public dataset links one attacker's events across channels. "
          f"The risk is not a calibrated probability, and the alert line {g('alert_line')} is tied to the simulation's mix.\n",
          "| Method (SIMULATED, alert line " + g("alert_line") + ") | Precision | Recall | F1 (95% CI) | False-positive rate (95% CI) | Hard campaigns flagged |", "|---|---|---|---|---|---|"]
    for short, label in (("single", "Single-channel: alert if any event >= 0.5"), ("parallel", "Parallel multi-channel: fusion without link and timing features"),
                         ("whole", "Correlation model on the whole bundle (pools up to 72 h)"), ("engine", f"**Deployed engine: {g('window.minutes')}-minute windows (what the API does)**")):
        L.append(f"| {label} | {g(f'corr.{short}.precision')} | {g(f'corr.{short}.recall')} | {g(f'corr.{short}.f1')} ({g(f'corr.{short}.f1_ci')}) | {g(f'corr.{short}.fpr')} ({g(f'corr.{short}.fpr_ci')}) | {g(f'corr.{short}.hard_flagged')} |")
    L += [f"\nEngine without a window: precision {g('corr.nowindow.precision')}, recall {g('corr.nowindow.recall')}, F1 {g('corr.nowindow.f1')}, false-positive rate {g('corr.nowindow.fpr')}.",
          f"\nHard campaigns: {g('corr.hard.n')} simulated linked attacks ({g('corr.hard.share')} of them) have every event below {g('alert_line')}. "
          f"{g('corr.fit60')} of simulated linked attack bundles fit inside {g('window.minutes')} minutes. AUC: {g('corr.auc.single')} (max single score) -> {g('corr.auc.nocorr')} (learned combination) -> {g('corr.auc.fusion')} (with link and timing).",
          f"\nPatent noisy-OR row: {g('corr.patent_row')}. Real bundles: {g('corr.real_bundles')}.",
          f"\n**Reading:** inside the window the engine beats single-channel alerting by a little, on simulated bundles. That claim stays open until real bundles test it.\n",
          "## 3. The time window\n", f"**{g('window.minutes')} minutes**, set at `{g('window.file_line')}` (`DEFAULT_WINDOW_MIN`). Used at {g('window.used_at')}. "
          "Events further apart are not combined or linked; each window is scored and the bundle takes the highest; a window with one event gets that event's detector score. "
          "The value was fixed before the window evaluation ran. The simulation cannot settle it; `src/refit_fusion.py` suggests one from real bundles.\n",
          "## 4. Demo cases and stories (hand-written, not a test set)\n", "Scored on this build through `/correlate`. Never compute a rate from these.\n",
          "| Case | What it is | Channels | Event scores | Alerts alone? | Bundle risk | Outcome |", "|---|---|---|---|---|---|---|"]
    for r in doc["demo"]:
        p = f"demo.{r['id']}"; L.append(f"| {r['id']} | {g(p + '.name')} | {', '.join(r['channels'])} | {g(p + '.scores')} | {g(p + '.alone')} | {g(p + '.bundle')} | {g(p + '.alert')} |")
    L += [f"\nThe final run on `{g('finalrun.build')}` was not adopted: its retrained correlation model moves TC-06 from {g('finalrun.tc06.live')} to {g('finalrun.tc06.retrained')} "
          f"(live correlation model with the retrained detectors: {g('finalrun.tc06.live_corr_new_det')}). See `reports/final_run/README.md`.\n",
          "## 5. Tests and checks on this build\n", "| Check | Result | Evidence |", "|---|---|---|",
          f"| pytest | {g('tests.pytest.passed')} passed, {g('tests.pytest.xfailed')} expected failures (open defects), {g('tests.pytest.skipped')} skipped, {g('tests.pytest.failed')} failed | `reports/test_run.json` |",
          f"| Smoke test | {g('tests.smoke.passed')} passed, {g('tests.smoke.skipped')} skipped, {g('tests.smoke.failed')} failed | `tests/smoke_test.py` |",
          f"| Ported test-plan cases | {g('tests.cases.total')} cases: " + ", ".join(f"{n} {s}" for s, n in sorted(case_counts(FC).items())) + f"; run on `{g('tests.cases.build')}` | `reports/final_cases_results.json` |",
          f"| Exit criteria | {g('tests.exit.met')} of {g('tests.exit.of')} rows met | `reports/exit_criteria.md` |",
          f"| End-to-end (API -> correlation -> event store -> alert -> console) | {g('tests.e2e.passed')} of {g('tests.e2e.steps')} steps pass | `reports/e2e_check.md` |",
          f"| Console UI checks (Chrome and Edge) | {g('tests.ui.passed')} of {g('tests.ui.n')} pass; failing: {g('tests.ui.failed')} | `reports/ui_checks.json` |",
          f"| Offline (no network at runtime) | {g('tests.offline')} | `reports/offline_check.md` |",
          f"| NFR-05: fresh clone from the README alone | {g('tests.nfr05')} | `reports/nfr05_fresh_clone.json` |",
          "\nExit criteria, judged against the plan's own targets:\n", "| # | Criterion | Result |", "|---|---|---|"]
    L += [f"| {c['n']} | {c['criterion']} | {g('tests.exit.' + str(c['n']))} |" for c in EX["criteria"]]
    L += [f"\n**Defects:** {g('defects.open')} open, {g('defects.closed')} closed. Open: {g('defects.open_list')}. Closed: {g('defects.closed_list')}. "
          "Accepting a defect is the team's call; proposals are in `reports/defect_log.md`.\n",
          "## 6. Latency (real HTTP, one request at a time)\n", f"Machine: {g('latency.machine')}. Demo laptop: {g('latency.demo_laptop')}.\n",
          "| Request | n | Median | 95th percentile | Max | Target |", "|---|---|---|---|---|---|"]
    for ch in ("email", "sms", "url"): L.append(f"| `/score` {ch} | {g('latency.n')} | {g(f'latency.{ch}.median')} | {g(f'latency.{ch}.p95')} | {g(f'latency.{ch}.max')} | NFR-01: median 2 s or less |")
    L += [f"| `/correlate` full case | {g('latency.n')} | {g('latency.case.median')} | {g('latency.case.p95')} | {g('latency.case.max')} | NFR-02: every case 5 s or less |",
          f"\nServer start-up (models loaded, `/health` answering): {g('latency.startup')}.\n",
          "## 7. What is not built\n",
          "- Voice and video detectors: not trained, no accessible data. Calls and video are 'not assessed', never SAFE.",
          "- Any result on real multi-channel bundles: 0 collected (R2-10). The correlation numbers above are simulated.",
          "- A calibrated probability. The 0.5 line is tied to the simulation's half-malicious mix.",
          "- A message queue or streaming source. The event store regroups a recipient's events on each `POST /events`.",
          "- The old patent draft's noisy-OR score, 30-minute window, watch list, hash-chained audit log and voice module. Not built; the noisy-OR score is not evaluated (owner, 7 Nov 2026).",
          "- Mail, SMS or browser integration. Messages reach the API only through its routes and the console.\n",
          "## 8. Measured limitations\n",
          f"1. **Email does not transfer across corpora.** Leave-one-corpus-out F1 {g('email.honest.f1')} against {g('email.flattering.f1')} pooled. False-positive rates on unseen corpora: {g('email.honest.fpr_range')}; recall {g('email.honest.recall_range')}.",
          f"2. **Email on real mail.** The live model flags {g('email.realmail.fpr')} of {g('email.realmail.n')} real legitimate emails from one person's mailbox.",
          f"3. **URL: login-page fix costs recall on popular domains.** Login false alarms {g('url.login_fpr.before')} -> {g('url.login_fpr.after')}; bad-URL recall on top-10k domains {g('url.popular_recall.before')} -> {g('url.popular_recall.after')}.",
          f"4. **SMS has few smishing examples** ({g('sms.smishing_support')} in the test split), so the F1 interval is wide ({g('sms.honest.f1_ci')}).",
          f"5. **Correlation is measured only on simulated bundles.** On them, the {g('window.minutes')}-minute engine has F1 {g('corr.engine.f1')} and false-positive rate {g('corr.engine.fpr')}, against {g('corr.single.f1')} and {g('corr.single.fpr')} for single-channel alerting.",
          f"6. **The correlation model is not stable on borderline bundles.** A retrain on almost the same simulated data moves TC-06 from {g('finalrun.tc06.live')} to {g('finalrun.tc06.retrained')} while the simulated F1 moves from {g('finalrun.sim_f1.live')} to {g('finalrun.sim_f1.retrained')}.",
          "7. **The correlated score can sit below the best single score** (D-18, UI-03): a lone high score next to benign-looking events is lowered a little.",
          "8. **A detector false positive stays a false positive.** Correlation does not fix it (TC-08's courier SMS).\n",
          "## 9. Retired numbers\n", "These numbers are wrong. They must not be quoted. Patent Tables 2 and 3 are not listed: the old specification is not used (owner, 7 Nov 2026).\n"]
    L += [f"- {n}" for n in doc["retired_list"]]
    RS = doc["retired_search"]; hits = RS["hits"]
    L += [f"\nRepository search: {RS['searched_files']} text files (every tracked file except the built console bundle, plus the team's text inputs in `docs/inputs/`). "
          f"{len(hits)} hits: " + "; ".join(f"{n} {v}" for v, n in sorted(verdicts(hits).items())) + ". Files received with v2 or given as team input are listed and not edited.\n"]
    if hits:
        L += ["| Number | File | Line | Origin | Verdict |", "|---|---|---|---|---|"] + [f"| {h['number']} | `{h['file']}` | {h['line']} | {h['origin']} | {h['verdict']} |" for h in hits]
    (R / "FINAL_NUMBERS.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
