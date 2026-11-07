"""docs/DIARY_ENTRIES.md (RD-01, RD-05, RD-06, RD-07): text to hand-copy into the research diary, in the diary's own columns.
  python scripts/make_diary_entries.py      (after scripts/make_final_numbers.py)
Covers p.14 (traceability rows O1-O5), p.49 (datasets, experiments with the real figures for the 'F1 0.9x' placeholders, privacy), p.50
(build and version control), p.53 (unit test execution), p.54 (issue tracker), task 11 on p.45 (the time window), and a dated log of the work.
Dates come only from git. Numbers come from reports/final_numbers.json and the reports it names; nothing is typed."""
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; R = ROOT / "reports"; sys.path.insert(0, str(ROOT / "scripts"))
jl = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
cell = lambda s, n=170: (" ".join(str(s or "").split()).replace("|", "/"))[:n]
OWNER = {"Email classifier": "Krishna", "SMS classifier": "Krishna", "Preprocessing": "Krishna", "Voice/Video module": "Krishna", "URL classifier": "Viraj",
         "Service (API)": "Viraj", "Console (UI)": "Viraj", "Correlation engine": "Bala", "Scoring and verdict": "Bala", "End-to-end cases": "Bala", "Non-functional": "Manoj"}
GUIDE = "Guide signs after review"


def git(*a): return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def main():
    FN, FC, W, DS, REG = jl(R / "final_numbers.json"), jl(R / "final_cases_results.json"), jl(ROOT / "tests" / "data" / "workbook_cases.json"), jl(R / "defect_status.json"), jl(ROOT / "docs" / "defect_registry.json")
    V, B = FN["values"], FN["build"]; g = V.__getitem__; plan = {c["TC ID"]: c for c in W["test_cases"]}; wbdef = {d["Defect ID"]: d for d in W["defects"]}
    import make_data_sources as MDS
    lic = {s[0]: s[2] for s in MDS.SOURCES}
    tagline = lambda t: f"`{t}` (commit `{git('rev-parse', '--short', t + '^{commit}')}`, {git('log', '-1', '--format=%ad', '--date=format:%d %b %Y', t + '^{commit}')})"
    L = ["# Research diary entries (CP1)\n",
         f"Written by `scripts/make_diary_entries.py` from build `{B['tag']}` (commit `{B['commit7']}`). Copy the text by hand into the diary, in its own columns. "
         "It replaces the blue 'sample / assumed' text of the filled draft wherever the two differ. Dates come only from git; numbers come from `reports/FINAL_NUMBERS.md`.\n",
         "Where a cell needs a person (a signature or the guide's comment), it says who.\n"]

    # p.14
    L += ["## Page 14: objectives traceability matrix\n", "Req. refs are as in the filled draft. Status uses the diary's own words.\n",
          "| ID | Success criterion | Req. ref | Design ref | Build ref | Test ref | Status | Guide sign |", "|---|---|---|---|---|---|---|---|",
          f"| O1 | Per-channel modules (email, SMS, URL) trained and tested | REQ-01, REQ-02, REQ-08 | Email, SMS and URL modules (report chapter 1) | {tagline(B['tag'])}: `src/train_email.py`, `src/train_sms.py`, `src/train_url.py`, `models/` | EML, SMS and URL cases in `tests/test_final_cases.py`; TC-01, TC-02 | Achieved. Honest F1: email {g('email.honest.f1')}, SMS smishing {g('sms.honest.f1')}, URL {g('url.honest.f1')} | {GUIDE} |",
          f"| O2 | Correlation engine links events by identity and time | REQ-05, REQ-06, REQ-07, REQ-09 | Correlation engine and event store (report chapter 1) | {tagline(B['tag'])}: `src/predict.py` (`extract_ids`), `src/fusion.py`, `src/event_store.py`, `api.py` | `tests/test_window_and_ids.py`, `tests/test_event_store.py`, TC-04 to TC-08, COR and SYS cases | Partially achieved. Built and tested end to end; evaluated on simulated bundles only (engine F1 {g('corr.engine.f1')} against {g('corr.single.f1')} single-channel). Real bundles: 0 (R2-10) | {GUIDE} |",
          f"| O3 | Synthetic-voice detector flags cloned calls | REQ-03 | Voice module | Not built. No accessible voice data; calls are 'not assessed' | TC-03 shows 'not assessed' | Not started (CP2) | {GUIDE} |",
          f"| O4 | Existing deepfake detector integrated | REQ-04 | Deepfake module | Not built. The API accepts video events and marks them 'not assessed'; there is no stub module | `tests/test_defects.py::test_D13_a_call_or_video_does_not_block_or_change_the_bundle` | Not started (CP2) | {GUIDE} |",
          f"| O5 | Full-system evaluation against baselines | Evaluation | R3-09 comparison | `src/eval_comparison.py`, `reports/comparison_metrics.json` | `reports/FINAL_NUMBERS.md`, section 2 | In progress. Simulated half done; the real half waits for real bundles (R2-10) | {GUIDE} |\n"]

    # p.49
    L += ["## Page 49: data and model evidence\n", "### Datasets\n", "| Dataset / source | Size & split | Licence & provenance | Pre-processing / issues |", "|---|---|---|---|",
          f"| Email: {g('email.corpora')} | {g('email.n')} emails after cleaning and de-duplication. Honest test: leave one corpus out (train on two, test on the third). Pooled split {g('email.split.train')} / {g('email.split.val')} / {g('email.split.test')} | CEAS_08: {cell(lic['CEAS_08.csv'])} Enron: {cell(lic['enron_spam_data.zip'])} Fraud: {cell(lic['fraud_repo.zip'])} | Scripts and styles dropped, link targets kept, tags stripped, numbers masked; duplicates and conflicting labels removed. Labels are 'unwanted or fraudulent', not strictly phishing |",
          f"| SMS: phishing SMS dataset (three classes) | {g('sms.n')} messages: {g('sms.count.ham')} ham, {g('sms.count.spam')} spam, {g('sms.count.smishing')} smishing. Test split {g('sms.test_n')} | {cell(lic['smish/hcphap_lsdst.csv'], 220)} | Duplicates and conflicting labels removed. Smishing is a small class, so recall, F1 and a 95% interval are reported |",
          f"| URL: phishing and legitimate URL strings | {g('url.n')} URLs on {g('url.hosts')} hosts; split 80/20 by host ({g('url.train')} / {g('url.test')}); plus {g('url.constructed.train_login_urls')} constructed login URLs for training | {cell(lic['url_strings.csv'])} Popularity list: {cell(lic['opendns_top10k.txt'])} | The model reads raw URL text, so no feature extraction service is needed. A random split would let a model score well by checking for a path, so hosts are held out |",
          f"| Correlation: simulated bundles | {g('corr.n_train')} train, {g('corr.n_val')} tune, {g('corr.n_test')} test | Built by `src/fusion.py` (`simulate`) from real held-out messages; the links are constructed | Simulated, labelled simulated everywhere. No real bundle collected yet (R2-10) |\n",
          "### Experiments (the real figures for the 'F1 0.9x' placeholders)\n", "| Experiment / run ID | Config / model | Metric | Baseline | Result vs target |", "|---|---|---|---|---|"]
    t95 = lambda k: "not met" if float(V[k].rstrip("%")) < 95 else "met"
    L += [f"| EXP-01 | Email: TF-IDF word 1-2-grams, numbers masked, cross-corpus term filter, logistic regression | F1 on an unseen corpus (mean of {g('email.n_corpora')} runs) | Pooled random split of the same data: {g('email.flattering.f1')} (flattering, never quoted alone) | **{g('email.honest.f1')}**; draft target 0.95: {t95('email.honest.f1')} |",
          f"| EXP-02 | SMS: word and character TF-IDF, logistic regression, three classes | Smishing-vs-rest F1 with 95% CI | Spam-or-smishing vs ham on the same split: {g('sms.flattering.f1')} (flattering) | **{g('sms.honest.f1')}** (95% CI {g('sms.honest.f1_ci')}) |",
          f"| EXP-03 | URL: character n-grams of the URL text, three popularity flags, logistic regression (not XGBoost) | F1 with hosts held out | Feature benchmark, random split: {g('url.flattering.f1')} (flattering) | **{g('url.honest.f1')}** (95% CI {g('url.honest.f1_ci')}); draft target 0.95: {t95('url.honest.f1')}. Login false alarms {g('url.login_fpr.before')} to {g('url.login_fpr.after')}; popular-domain recall {g('url.popular_recall.before')} to {g('url.popular_recall.after')} |",
          f"| EXP-04 | Time window, fixed at {g('window.minutes')} minutes before the evaluation ran (`{g('window.file_line')}`) | Share of simulated linked attacks inside one window; engine F1 (simulated) | Engine with no window: F1 {g('corr.nowindow.f1')} (simulated) | {g('corr.fit60')} of simulated linked attacks fit; engine F1 {g('corr.engine.f1')} (simulated). Not swept on real scenarios: none collected |",
          f"| EXP-05 | Composite (learned window score) against single-channel, on the same simulated bundles | Precision, recall, F1, false-positive rate | Single-channel: F1 {g('corr.single.f1')}, false positives {g('corr.single.fpr')} | Engine: F1 {g('corr.engine.f1')}, false positives {g('corr.engine.fpr')} (simulated). Campaigns every single filter misses: {g('corr.hard.n')}; the engine flags {g('corr.engine.hard_flagged')} of them |",
          f"| EXP-06 | End-to-end through FastAPI: API, correlation, event store, alert, console | Steps passed; latency over real HTTP | Not applicable | {g('tests.e2e.passed')} of {g('tests.e2e.steps')} steps pass. Median {g('latency.email.median')} per email, {g('latency.case.median')} per full case |\n",
          "### Bias / fairness and data-privacy check\n",
          "- **Data.** The trained models use public research corpora only (table above). One exception was tried and not adopted: the v3 email attempt read "
          "the account owner's own legitimate mail, with the owner's consent, on this laptop only, under a written privacy specification. The export and that "
          "model were never committed or shared, and v3 failed the adoption rule and the privacy audit (`PRIVACY_AND_ETHICS.md`).",
          "- **Identities.** The event store keeps the recipient and every identity token as HMAC-SHA256 with a secret key (not a plain or salted hash). Linking "
          "uses the hash. Message text is not stored unless a setting turns it on (`docs/PRIVACY.md`).",
          "- **Bias.** The corpora are mostly English and several years old. Regional-language and current phishing are under-represented.",
          f"- **Imbalance.** Smishing is a small class ({g('sms.smishing_support')} test messages), so recall, F1 and intervals are reported, not accuracy.",
          "- **DPDP Act 2023.** Real bundles for R2-10 need written consent (`TESTCASE_FORMAT.md` asks for a basis on every real row). Old events are deleted with "
          "`POST /purge`.\n"]

    # p.50
    L += ["## Page 50: build and version control\n",
          f"Repository: a private local git repository. `git remote -v` is {'empty' if not git('remote', '-v') else 'NOT empty: check it'}; nothing is pushed until the patent is filed. "
          f"No CI server: tests run locally. The history starts at `v2-baseline`, v2 exactly as received, so earlier work is not in this git history.\n",
          "| Module / component | Owner | Repository / commit ref | CI-CD / build status |", "|---|---|---|---|"]
    merges = [l.split("|", 2) for l in git("log", "main", "--merges", "--first-parent", "--reverse", "--format=%h|%ad|%s", "--date=format:%d %b %Y").splitlines()]
    rows = [("BLD-02, BLD-03 Email and SMS modules", "Krishna", "module/email-sms"), ("BLD-04 URL module", "Viraj", "module/url"),
            ("BLD-05 to BLD-07 Event store, identity linking, time window and score", "Bala", "module/correlation"), ("BLD-08, BLD-09 FastAPI service and React console", "Viraj", "module/api-console"),
            ("BLD-10, BLD-11 Tests, test data and documents", "Manoj", "module/testing-docs")]
    status = f"Local run on `{B['tag']}`: pytest {g('tests.pytest.passed')} passed, {g('tests.pytest.xfailed')} expected failures, {g('tests.pytest.failed')} failed"
    for name, owner, br in rows:
        ms = [f"`{h}` {d}" for h, d, s in merges if f"Merge {br}" in s]
        L.append(f"| {name} | {owner} | Branch `{br}`, merged into `main` by " + ("; ".join(ms) if ms else "no merge yet") + f" | {status} |")
    L += [f"| BLD-01 Data preparation | Krishna, Viraj | `download_data.sh` and `run_all.sh`, received with {tagline('v2-baseline')} | Final run on {tagline('cp1-rc1')}: recorded, not adopted (`reports/final_run/`) |",
          "| BLD-12 Deepfake stub | Viraj | Not built. Video events are accepted and marked 'not assessed' (`src/predict.py`, `NOT_ASSESSED`) | Not applicable |\n",
          "Tags: " + "; ".join(tagline(t) for t in git("tag", "--sort=creatordate").splitlines()) + ".\n"]

    # p.53
    unit = [(cid, c) for cid, c in FC["cases"].items() if plan[cid]["Level"] == "Unit" and c["status"] not in ("N/A", "Not run")]
    unit.sort(key=lambda x: ({"High": 0, "Medium": 1, "Low": 2}.get(plan[x[0]]["Priority"], 3), x[0]))
    L += ["## Page 53: unit test execution\n", f"Run on `{FC['run']['describe']}`, {FC['run']['date'][:10]}. The page has room for about 20 rows: copy these {min(20, len(unit))} "
          f"(High priority first). All {len(unit)} executed unit-level cases are in `reports/FINAL_TEST_REPORT.md`.\n",
          "| Test-case ID | Input | Expected output | Actual output | Pass/Fail |", "|---|---|---|---|---|"]
    for cid, c in unit[:20]:
        p = plan[cid]; exp = cell(p["Expected result"], 120) if c["tag"] == "Ported" else "Same intent: " + cell(c.get("why"), 110)
        L.append(f"| {cid} | {cell(p['Input / steps'], 120)} | {exp} | {cell(c['actual'], 140)} | {c['status']} |")

    # p.54
    L += ["\n## Page 54: issue tracker\n", "The defects found by testing. Status comes from the run; accepting a defect is the team's decision.\n",
          "| Issue no. | Description | Impact | Owner | Status | Guide sign |", "|---|---|---|---|---|---|"]
    for d, s in DS["defects"].items():
        reg = REG.get(d, {}); new = reg.get("new"); wd = wbdef.get(d, {})
        mod = reg.get("module") if new else wd.get("Module", ""); sev = reg.get("severity") if new else wd.get("Severity", "")
        desc = reg.get("description") if new else wd.get("Description", "")
        fails = [k for k, v in s["cases"].items() if v != "Pass"]
        L.append(f"| {d} | {cell(desc, 160)} | {sev}; " + (f"failing: {', '.join(fails)}" if fails else "all linked cases pass") + f" | {OWNER.get(mod, 'Manoj')} | {s['status']} | {GUIDE} |")

    # task 11
    wc = git("log", "-1", "--format=%h, %ad", "--date=format:%d %b %Y", "--grep=D-04")
    L += ["\n## Page 45, task 11: the time window\n", "| Task | Owner | Start | End | % done | Depends on / evidence |", "|---|---|---|---|---|---|",
          f"| 11. Time window: fixed at {g('window.minutes')} minutes and enforced everywhere | Bala | {git('log', '-1', '--format=%ad', '--date=format:%d %b %Y', 'v2-baseline')} (value as received in v2) | "
          f"{wc.split(', ')[1] if wc else 'see git log'} (D-04 closed, commit `{wc.split(',')[0] if wc else 'none'}`) | 100% for CP1 | Set at `{g('window.file_line')}`; used at {g('window.used_at')}. "
          f"Not swept on the scenario set: no real scenarios exist yet. The simulated table in `reports/results.md` is for information only. `src/refit_fusion.py` suggests a value once real bundles exist (CP2) |\n"]

    # dated log
    L += ["## Dated log of the CP1 finish work (from git)\n", "| Date and time | Commit | What |", "|---|---|---|"]
    for line in git("log", "--reverse", "--no-merges", "--format=%ad|%h|%s", "--date=format:%d %b %Y %H:%M").splitlines():
        d, h, s = line.split("|", 2); L.append(f"| {d} | `{h}` | {cell(s, 160)} |")
    (ROOT / "docs" / "DIARY_ENTRIES.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print("wrote docs/DIARY_ENTRIES.md")


if __name__ == "__main__":
    main()
