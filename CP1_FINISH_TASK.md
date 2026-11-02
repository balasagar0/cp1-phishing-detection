# CP1 — finish the checklist work in this folder

*For S: save this file in the project folder (the one with `api.py` and `PROJECT_STATE.md`). Unzip `cp1_inputs.zip` into `docs/inputs/` in that folder and add your patent spec (.docx or .md) there too. Then open Claude Code in the project folder and send:* **Read CP1_FINISH_TASK.md and carry it out, starting at Phase 0.**

---

You're working on our capstone prototype, **AI-Based Multi-Channel Phishing Detection System** (team Y23-HTE-PROJECT-88, B.Tech CSE, KL University). Review-3 is done. Still ahead: the Final External Review (live demo, final report, user manual, code), SAMYAK-2026 (poster, paper, project expo with a working prototype), the patent filing and a journal manuscript. Our checklist has 69 items. This file says which ones need this code, in what order, and under what rules.

## 0. Decisions already made

| Setting | Value | What it means for you |
|---|---|---|
| `VOICE_IN_CP1` | `no` | Calls stay "not assessed" (`/score` answers HTTP 501). If I change this to `yes`, follow Appendix A. |
| Video | not in CP1 | Always "not assessed", never SAFE. |
| Live correlation scorer | v2's learned fusion model | Don't replace it. |
| Time window | 60 minutes | What v2 ships. Don't re-derive it from the simulation; `src/refit_fusion.py` suggests one once real bundles exist. |
| Git | local only | No remote, no push. The patent is not filed. |

## 1. What you're working with

### 1.1 The build

This folder holds `cp1_trained_detectors_v2`, the only build that runs. Trust order: the code, then `reports/results.md`, then `PROJECT_STATE.md` (15 Oct). If code and a document disagree, the code wins and the document gets fixed.

What v2 should contain (check each):

- **Email detector**: TF-IDF word 1–2-grams (numbers masked) and logistic regression, trained on 72,428 emails from CEAS_08, Enron and a fraud-email corpus.
- **SMS detector**: three classes (ham, spam, smishing), word and character TF-IDF with logistic regression, 5,789 messages.
- **URL detector**: character n-grams on the raw URL, 3 domain-popularity flags and logistic regression, 260,000 URLs plus 12,000 constructed login URLs.
- **Correlation**: a gradient-boosting model over per-channel scores, how many events share an identity token, and the time span. It is trained on simulated bundles built from real held-out messages. Identity tokens are domains, phone numbers and an optional `identity` field. Events more than 60 minutes apart are not combined. Each window is scored and the bundle takes the highest. A window with one event gets that event's detector score.
- **API** in `api.py`: `/health`, `/score`, `/score/batch`, `/correlate`. **Console** in `console/` (React).
- `download_data.sh`, `run_all.sh` (retrains everything and rewrites `reports/`), `src/refit_fusion.py`, `testcases/review2_testcase_workbook.xlsx` (empty), `TESTCASE_FORMAT.md`.
- **Tests**: 17 in `tests/test_window_and_ids.py` and 24 checks in `tests/smoke_test.py`.

Not in v2: a voice or video detector, an event store, any result on real multi-channel bundles, and a calibrated probability (the 0.5 alert line is tied to the simulation's half-malicious mix).

### 1.2 Review-3 baseline: what v2's reports should show

| Channel | Honest measure (the one we quote) | Flattering measure (never quoted alone) |
|---|---|---|
| Email | F1 82.2%, mean of three leave-one-corpus-out runs | F1 98.8% on a pooled random split |
| SMS | Smishing-vs-rest F1 87.1% (95% CI 82.3–91.7) | Spam-or-smishing F1 98.2% |
| URL | F1 90.4% host-grouped. 0.0% false alarms on login URLs of 1,000 held-out popular domains, at the cost of recall on bad URLs hosted on popular domains (49.9% → 30.7%) | F1 95.4% on the offline feature benchmark |
| Voice, video | Not trained | — |

Correlation on 12,000 **simulated** test bundles, alert line 0.5:

| Method | Precision | Recall | F1 | False-positive rate |
|---|---|---|---|---|
| Single-channel (alert if any event ≥ 0.5) | 87.0% | 95.3% | 91.0% | 14.1% |
| Model on the whole bundle (pools up to 72 h) | 97.0% | 92.9% | 94.9% | 2.8% |
| Engine without a window | 96.8% | 93.0% | 94.8% | 3.0% |
| Engine with the 60-minute window (what the API does) | 89.4% | 94.9% | 92.0% | 11.1% |

27 simulated linked attacks (0.8%) have every event below 0.5, and the windowed engine flags 5 of them. 95.6% of simulated linked attack bundles fit inside 60 minutes.

### 1.3 The eight demo cases (hand-written, not a test set)

| Case | What it is | Event scores | Alerts alone? | Bundle risk |
|---|---|---|---|---|
| TC-01 | Phishing email alone | 0.998 | yes | 0.998 |
| TC-02 | Smishing SMS alone | 1.000 | yes | 1.000 |
| TC-03 | Voice call | — | — | HTTP 501 |
| TC-04 | SMS + URL + email on one domain (`sbi-kyc-update.top`), 12 min | 1.000 / 0.995 / 0.998 | yes | 1.000 |
| TC-05 | A colleague shares an article (`wikipedia.org`), 10 min | 0.002 / 0.000 / 0.000 | no | 0.000 |
| TC-06 | Weak parcel campaign, 15 min | 0.421 / 0.451 / 0.204 | no | 0.595 |
| TC-07 | TC-06's messages, 3 days apart | 0.421 / 0.451 / 0.204 | no | 0.451 |
| TC-08 | Courier SMS + email sharing a tracking number | 0.970 / 0.031 | yes | 1.000 |

### 1.4 Material that is wrong: don't use it

These files describe a build that was never written (a trained voice detector, a noisy-OR engine with time decay, a 30-minute window, a watch list, a hash-chained audit log, 19 routes, a 142-case suite): `CP1_Team_Study_Guide.md`, `Review3_Results_Pack.md`, `Manuscript_Draft_v1.0.md`, `SAMYAK_2026_Day_Plan.md`, `Numbers_Register.md`, `Review3_Content_Pack.md`, `Review2_Defect_Fix_Pack.md`, `TRAINING_REPORT.md`, the Review-2 deck, and the Review-3 posters, paper and deck. Don't take numbers or features from them, don't build toward them, and don't delete them. If you find any in this folder, list them in `CHECKLIST_STATUS.md`.

### 1.5 `docs/inputs/` (read-only, gitignored)

| File | Use |
|---|---|
| `Test_Cases_and_Test_Data.xlsx` | 112 test cases, 96 hand-written samples (28 email, 32 SMS, 36 URL), scenarios S-01–S-13, media specs, defect log D-01–D-12, and a Summary sheet with 7 exit criteria |
| `review2_testcase_workbook.xlsx` | The real-bundle collection workbook (still 0 bundles) |
| `Research_Diary_Pages_26-59_Filled.pdf` | The diary draft, for the p.14, p.49, p.50, p.53 and p.54 entries |
| Patent spec (`Patent_Complete_Specification_Form2`, .docx or .md) | For PT-03 and PT-04 only |
| Optional: `Test_Plan_Phishing_Detection.docx`, `SRS_Phishing_Detection_v1.0.md` | Test plan v1.1 (29 Sep) and the requirements REQ-01–REQ-12 |

Two warnings about these inputs:

1. **The test plan and its 112 cases were written for an older codebase** (`phishing-detection-system.zip`): `/analyze` routes, scores from 0 to 100, a rule bonus capped at 25 that counts only channels scoring 20 or more, and verdicts SAFE ≤ 30 / SUSPICIOUS ≤ 60 / HIGH RISK. v2 works differently. Port the cases (Phase 1); don't run them as written. The SRS was written against the same older codebase.
2. **The patent spec describes the build that was never written.** It says the noisy-OR formula, a 30-minute window, keyed hashing, a watch list, an audit log and a voice module are built. Its Tables 2 and 3 and paragraphs [0078]–[0083] report results that no code produced. Your job is to measure what exists and report the gap (Phase 5), not to build the patent's features so the text comes true. The one exception is the campaign formula: Phase 4.3 implements it as an evaluated alternative, so the patent's core method gets a real measured number.

## 2. Rules

1. **Numbers flow from code to documents, never back.** Every metric comes from a script run on the tagged build and is written into `reports/` by code. Never type a metric by hand. Never change code or data to reach a number from a document.
2. **No made-up evaluation data.** Don't generate bundles, messages or labels for evaluation, and never present generated data as real. Hand-written cases are demos: label them "hand-written, not a test set" and never compute a rate from them. Write them the way a real sender would, run them once, and keep whatever they score.
3. **Never train on evaluation material**: the workbook samples, the scenarios, TC-01–TC-08, or anything under `tests/`.
4. **Simulated is always labelled simulated**, in tables, charts, captions and sentences.
5. **Not built is never SAFE.** Voice, video and anything that can't be assessed shows "not assessed" or `CANNOT_ASSESS`.
6. **A feature exists only when its code and a passing test exist.** Everything else is "planned".
7. **Real git history.** Commit with the identity already configured on this machine (ask me if there isn't one). No backdating, no teammate as author, no rewriting history once it exists. Keep Claude Code's co-author line: it's our honest record of AI help.
8. **Patent privacy.** No git remote, no push, and no uploading code, data, models or reports anywhere (gists, pastebins, online notebooks, package indexes). The internet is fine for installing packages and downloading public datasets.
9. **Don't destroy what you didn't make.** Back up the v2 models and reports before anything can overwrite them. Never delete datasets.
10. **Writing style** for every doc you write: short, plain sentences. No "TBD" and no empty cells. If something needs a person (a signature, a date, the guide's comment), write one line saying who and what.
11. **Accepting a defect is the team's call.** You may write "Proposed: accept because …" in the defect log. Never mark a defect accepted yourself.

## 3. When to stop and ask me

Only when:

- the folder doesn't match §1 in a way that changes the plan (for example, TC-01–TC-08 don't reproduce, or the routes differ);
- you'd have to overwrite or delete models, data or files you didn't create;
- you need a login, an API key, a payment, system software I must install (Node.js, Git, a browser), or a single download over 2 GB;
- a retrain fails the adoption rule twice (Phase 3).

Otherwise keep going. Keep a todo list. At the end of each phase, and before any session ends, update `CHECKLIST_STATUS.md` and commit.

**Resuming:** if `CHECKLIST_STATUS.md` already exists, read it and `git log --oneline -30` first, then continue from the first unfinished step.

---

## Phase 0. Baseline and audit (no behaviour changes)

**0.1** Read the code, `reports/results.md` and `PROJECT_STATE.md`. Note the OS and the Python, Node/npm and git versions. On Windows, run the `.sh` scripts in Git Bash and make them call the venv's Python. The folder path contains a space (`Capstone_HTE Project`), so quote paths in every script and command.

**0.2** Create `.venv`, install `requirements.txt`, and save `pip freeze` as `requirements.lock.txt`. If the models load with a scikit-learn version warning, install the version they were saved with.

**0.3** Copy `models/` and `reports/` to `_baseline_v2/`. Write `reports/model_manifest.json` (file, bytes, SHA-256).

**0.4** Run `git init` if there's no repo. `.gitignore`: `.venv/`, raw data, `_baseline_v2/`, `docs/inputs/`, `node_modules/`, caches, the event database and any key file. Scan for secrets before the first commit (NFR-04). Commit the models if they total under 300 MB; otherwise leave them out and rely on the manifest. The first commit is v2 exactly as received. Tag it `v2-baseline`.

**0.5** Write `CLAUDE.md` containing §0–§3 of this file, so the rules load in every later session.

**0.6** Run the existing tests. Start the API and run TC-01–TC-08. Find where these cases are defined; if they exist only in a document, codify them as `tests/test_demo_cases.py`. Results must match §1.3 to 3 decimals. If any differs by more than 0.005, stop and tell me.

**0.7** Reproducibility check: in a scratch git worktree (not this folder), run `download_data.sh` and `run_all.sh` and compare the new reports with §1.2. Record every difference, and any data source that no longer downloads, in `reports/baseline_check.md`. A dead source is a finding, not a reason to stop.

**0.8** Create `CHECKLIST_STATUS.md` with all 69 items from §9: owner, who does it, status (done, partial, open, blocked or people), evidence (file, test or commit) and the next step. Nothing counts as done without evidence.

Commit, and tag `test-run-<yyyymmdd>-0`.

## Phase 1. Port the test suite, re-test the defects, fix what code alone can fix

**1.1 Port the 112 cases** into `tests/test_final_cases.py`, one test per ID (PRE-01 to NFR-07). Tag each one:

- **Ported**: the same check against v2.
- **Replaced**: the same intent with v2's expectation. "HIGH RISK" becomes an alert (risk ≥ 0.5), "SAFE" becomes no alert, "Rejected" becomes HTTP 4xx.
- **N/A**: the feature doesn't exist in v2 (the rule bonus, the risk threshold of 20, the 30/60 verdict bands). Give the reason.

Keep the IDs. Never weaken an expectation so a case passes; if v2 behaves wrongly, that's a defect. Run the 96 samples as the plan's 12 sample groups at the 0.5 line, with its targets (standard ≥ 90%, hard ≥ 70%). For SMS, use the score v2's API treats as the SMS alert score and say which one it is. Run the plan's smoke set first: API-01, API-02, SCO-01 and SYS-01, or their v2 equivalents.

**1.2 Workbook filler.** Write `scripts/fill_final_workbook.py`. It copies `docs/inputs/Test_Cases_and_Test_Data.xlsx` to `reports/Test_Cases_and_Test_Data_FINAL.xlsx`, then fills Actual result, Status, Executed by, Date, the Run record (git tag, and this laptop's CPU, RAM and OS) and the Defect Log. Keep sheet names, headers and formulas. If LibreOffice is installed, use it to recalculate the Summary sheet; otherwise note that Excel recalculates on opening. "Executed by" is "automated run, started by <git user>", never a teammate's name.

**1.3 Re-test the 12 defects on v2.** Their status at Review-3 is below. Verify each one; don't trust the table.

| Defect | Severity | Problem found on the old build (29 Sep) | Status claimed for v2 | Cases |
|---|---|---|---|---|
| D-01 | High | `https://` or a trailing slash flips a legitimate URL to phishing | Not re-tested | URL-02, URL-03, URL-05, URL-06, URL-07, SYS-13 |
| D-02 | Medium | Empty or invalid input still gets a score | Fixed (HTTP 422) | EML-07, SMS-07, URL-08 |
| D-03 | Medium | A case with nothing to assess is reported SAFE | Not re-tested | SCO-06, VV-05, SYS-08, SYS-12 |
| D-04 | High | No maximum time window | Fixed (60 min) | COR-12, SYS-09 |
| D-05 | Medium | Shared links matched on 12 domain endings only | Fixed (public suffix list) | COR-14, SYS-11 |
| D-06 | High | No CORS | Open | API-12 |
| D-07 | Low | A non-numeric timestamp gives HTTP 500 | Fixed (HTTP 422) | API-08 |
| D-08 | Medium | Ordinary words count as a claimed identity | Fixed (domains, phones and `identity` only) | COR-07 |
| D-09 | High | The SMS model misses phishing-style SMS (1 of 12 standard ones caught) | Not re-tested | SMS-01, SMS-03 |
| D-10 | Medium | Legitimate consumer mail flagged (E-L08, E-H06, E-H04, E-L06) | Not re-tested | EML-02, EML-03 |
| D-11 | Low | `clean_text()` keeps HTML | Not re-tested | PRE-01 |
| D-12 | Medium | Correlation never changes a verdict with the real models | TC-06 does, in one hand-made case | SYS-14 |

**1.4 Fix in code** (no retraining in this phase). Each fix gets a regression test named after its defect. In the Defect Log a defect moves Open → Fixed → Retest → Closed, and it closes only after its failing case passes.

- **R2-06 (D-02, D-07):** confirm the 422s. Also refuse malformed URLs with a clear message.
- **R2-07 (D-03):** when no event can be assessed, return `CANNOT_ASSESS`, never SAFE or a low score. Call and video events come back as "not assessed", stay out of the fusion features, and the response says so. Confirm D-05 and D-08 stay fixed.
- **R2-04 (D-06):** CORS with explicit origins (the console's dev address), never `*`.
- **R2-08 (D-11):** strip HTML and scripts before tokenising, and keep `href` targets as URLs. If that changes the email model's input, the retrain belongs to Phase 3.
- **D-01, D-09, D-10:** measure and record them here. Their fixes need retraining (Phase 3).

**1.5 Branches:** `module/url` (Viraj), `module/email-sms` (Krishna), `module/correlation` (Bala), `module/api-console` (Viraj) and `module/testing-docs` (Manoj). Merge into `main` with `--no-ff`. Start commit messages with the item and defect IDs, for example `R2-07 D-03: return CANNOT_ASSESS when nothing is assessable`. The names say who should review each module, not who wrote the commit.

## Phase 2. Event store, live flow and console (R2-05, R2-04, R3-03, R2-09, R3-13, R3-06)

**2.1 Event store**, the missing half of objective O2. Use SQLite from the standard library.

- Every event belongs to a recipient. Nothing links across recipients.
- Group a recipient's events exactly as v2's engine does, by calling v2's correlation and window code. Don't write a second scorer. Each group is a campaign.
- Routes: `POST /events` (one or many), `GET /campaigns`, `GET /campaigns/{id}`, `GET /alerts`, `POST /alerts/{id}/ack`, and a retention purge.
- For the same events, a recipient's highest campaign risk must equal the bundle risk `/correlate` returns. Test this on TC-04, TC-06 and TC-07 (TC-07 gives three one-event campaigns), to 3 decimals.
- Raise one alert when a campaign first reaches 0.5, and record why: which events, and which shared tokens.
- Calls and video are stored and shown in the campaign timeline. They never change the score.
- Privacy by default. Identity tokens and the recipient are stored as HMAC-SHA256, with the key taken from an environment variable or, failing that, generated once into a gitignored file. No message text is stored unless `CP1_STORE_CONTENT=1`. Store the channel, time, score and model version. No message content goes into logs (NFR-06).
- Tests: linking, window edges at 59 and 61 minutes, two recipients never mixing, the purge, and data surviving a restart.

**2.2 Console.** Find out how `console/` reaches the API today, then wire every view to the live API so no scoring is left in the browser. Build it and serve the built files from FastAPI, so the demo is one command on one address (keep CORS for development). For each case, show side by side: each event's score, whether it alerts on its own, and the bundle risk. Voice and video read "not assessed". Add one-click presets for TC-01–TC-08, and a "replay into event store" mode that sends a preset to `/events` so the campaign and its alert appear. If they aren't there yet, add presets for four Indian stories: a KYC freeze, a courier customs fee, a work-from-home task scam, and a legitimate order that must stay quiet. Rule 2 applies to all four.

**2.3 No network at runtime.** Nothing may reach the internet while the API or the console runs. Check the public-suffix list (if `tldextract` is used, force its bundled snapshot, because by default it fetches a fresh list), web fonts or CDN scripts in the console, and model downloads. Write `scripts/offline_check.py`: it blocks outbound sockets in-process, runs every demo case through the app, and scans the built console for external URLs.

**2.4 UI-01 to UI-07.** Automate them with Playwright if it installs, and save screenshots to `reports/screenshots/` (the report and the poster need them). If it won't install, write the manual steps in `docs/UI_CHECKS.md`.

**2.5 Evidence for R2-09 (D-12).** One table: the old fixed-score S-03 result, real-score TC-06 with its control TC-07, TC-05 (linked but harmless), and the simulated weak-campaign numbers from the reports. Label each row hand-written, fixed scores or simulated.

## Phase 3. Models (R2-01, R2-02, R2-08), at most two attempts each

Train candidates into `models/candidates/`. Leave the live models alone until a candidate is adopted. Compare pipelines under the same protocol on the same splits.

**Adopt a candidate only if all four hold:**

- (a) its honest metric is not worse than v2's beyond the 95% interval. Email: mean leave-one-corpus-out F1. SMS: smishing-vs-rest F1. URL: host-grouped F1 and the login-page false-alarm rate;
- (b) the target defect's cases improve;
- (c) TC-01–TC-08 keep their alert or no-alert outcome (scores may move; report the new ones);
- (d) every test passes.

Otherwise keep v2's model and report the candidate as a negative result.

**3.1 Email.** `results.md` gives "no real phishing corpus" as limitation 1: Nazario, SpamAssassin and Ling weren't reachable when v2 was built. Download them from their original public sources. Record each one in `DATA_SOURCES.md` (URL, licence or terms, date, SHA-256). Re-run leave-one-corpus-out over all corpora with the D-11 fix in. For a corpus with only one class, report only the measure that makes sense (recall for all-phishing, false-positive rate for all-legitimate). Measure D-10 on E-L08, E-H06, E-H04 and E-L06.

**3.2 URL (D-01).** If Phase 1 showed the scheme or a trailing slash flipping labels, normalise identically in training and serving, retrain, and re-run URL-02–URL-07 and SYS-13. Report both the login-page false alarms and the recall on bad URLs hosted on popular domains.

**3.3 SMS (D-09).** Retrain only with real smishing data whose source and licence you can verify. If there is none, D-09 stays open with the measured miss rate per lure type on the workbook samples (labelled hand-written) and a proposed acceptance (rule 11).

**3.4 Voice.** Skip unless `VOICE_IN_CP1` is `yes` (Appendix A).

Update `download_data.sh` so it fetches every dataset the adopted models use.

## Phase 4. Freeze and final run (R3-02, R3-07 to R3-10, R2-11, R2-12)

**4.1** Tag `cp1-rc1`. On that commit, run `download_data.sh` and `run_all.sh`, then commit the regenerated models and reports as "final run".

**4.2** Run everything against it: all tests, `tests/test_final_cases.py`, `scripts/offline_check.py`, an end-to-end check (API → correlation → event store → alert → console), and `scripts/benchmark.py` over real HTTP with uvicorn running. The benchmark sends 100 requests per channel and 100 full cases and records the median and p95, with the CPU, RAM and OS. Targets: NFR-01, a median of 2 s or less per channel; NFR-02, 5 s or less per full case. If this laptop isn't the demo laptop, say so in the report.

**4.3 Comparison for R3-09**, on the same simulated test bundles: single-channel; parallel multi-channel (the fusion model without link and timing features); the model on the whole bundle; and the deployed engine with the 60-minute window. Add one row for the patent: the noisy-OR campaign score from section 7 of the patent spec, S = min(1, F · [1 − Π(1 − w_c · s_i · e^(−λ·age_i))]), with its cross-channel and sequence factors. Implement it in `src/campaign_formula.py` as an **evaluated alternative**, not wired into the API. Apply it to the same event groups the deployed engine scores, so only the scoring rule differs, and choose λ, the factors and its threshold on validation bundles only. Add a unit test that reproduces the arithmetic of the patent's worked example (section 16: S ≈ 0.35, then 0.60, then 0.77, and 0.84 after the sequence factor). Title the table "simulated". The real-bundle half stays blocked on R2-10.

**4.4 Exit criteria for R2-11.** Run NFR-05 (clone the repo to a temp folder, make a new venv, follow only the README, run the tests and the demo) and NFR-07 (the final regression). Fill the FINAL workbook. Judge each criterion against the target the plan wrote, and never move a target after seeing a result. For criterion 4, report both the plan's held-out split and the honest metric, each marked met or not met.

**4.5** Tag `cp1-final`. Write the tag and commit hash into the workbook's "Git commit or tag tested" cell, into `FINAL_NUMBERS.md` and into the README. From here on, every number, screenshot and demo comes from `cp1-final`.

## Phase 5. Documents, all generated from `cp1-final`

| File | Items | Contents |
|---|---|---|
| `reports/FINAL_NUMBERS.md`, written by `scripts/make_final_numbers.py` | R3-12, R3-08, R3-17 | Tag and commit at the top. Per channel: the honest number and the flattering one (labelled), with precision, recall, F1, false-positive rate, ROC-AUC and the confusion matrix. The R3-09 table. The demo-case table. Test counts, latency and defect status. The time window, with the file and line that set it (diary task 11). What isn't built. Measured limitations. The retired numbers (below) and the result of a repo-wide search for them. |
| `reports/FINAL_TEST_REPORT.md` | R3-11, R3-07, R2-11 | Why the suite was ported (the codebase changed after 29 Sep), the porting table (Ported, Replaced or N/A per ID), results by module, sample groups, the 7 exit criteria, the defect log, and what wasn't tested and why. |
| `reports/figures/` | MS-05, R3-23, poster | PNG at 300 dpi plus SVG, readable in grayscale: honest vs flattering metric per channel, the R3-09 comparison (titled "simulated"), confusion matrices, the URL login-page trade-off, and latency. A `README.md` names each figure's source data. |
| `docs/diagrams/` | R2-14 | As built, in Mermaid, rendered to SVG and PNG if `mmdc` works: components, the `/correlate` sequence, the `/events` sequence, and the event-store ER diagram. |
| `README.md`, `docs/USER_MANUAL.md` | R3-21 | Install and run on a fresh Windows machine (and Linux), start the demo, the API routes with examples, and troubleshooting. The manual walks through the console with screenshots. NFR-05 must pass using the README alone. |
| `docs/DEMO_SCRIPT.md`, `scripts/preflight.py`, `start_demo.bat` | R3-05, R3-06 | Order: TC-06 → TC-07 → TC-05, then the rest, with expected values from FINAL_NUMBERS and what to say at TC-03. Fallbacks for an API that won't start, a port that's taken, or a blank page. `preflight.py` checks Python, packages and model hashes, starts the API, runs the eight cases and prints GO or NO-GO. `start_demo.bat` runs preflight, starts the server and opens the browser in one double-click. |
| `docs/PRIVACY.md`, `DATA_SOURCES.md` | R3-16 | Exactly what the code stores, hashes, logs and deletes, and for how long. Every dataset with its source and licence. |
| `docs/BUILT_VS_DESCRIBED.md` | PT-04, R3-01 | Every feature named in the patent spec (and the SRS, if present): built (file and function), tested (test name), or described only. Quote each patent sentence that calls something built, deployed or measured when it isn't. |
| `docs/PATENT_NUMBERS.md` | PT-03 | Every measured number in the patent (Tables 2 and 3, paragraphs [0078]–[0083], window values and thresholds): its current text, the `cp1-final` figure, and the source file. Where the patent measures something this build doesn't do, write "not measured: not built" instead of a replacement. |
| `docs/MANUSCRIPT_METHOD_RESULTS.md` | MS-03 | Method and results for the paper, about 1,500 words, from `cp1-final`: data, models, honest evaluation, correlation against baselines (simulated, labelled) and limits. |
| `docs/DIARY_ENTRIES.md` | RD-05, RD-06, RD-01, RD-07 | Text to hand-copy into the diary, in the diary's own columns: the p.14 traceability rows (O1–O5 status, build tag, test IDs); p.50 build and version control (repo, branches, tags, and commit hashes with their real dates); p.53 unit test execution; p.54 issue tracker; the real figures for the "F1 0.9x" placeholders on p.49; the window entry for task 11; and a dated log of this work from git. Dates come only from git or file timestamps. |
| `docs/report/` | R3-20 | Report chapters as built: system design, implementation per module, testing and validation, results and discussion, limitations, and future work. Department formatting is done later. |
| `docs/VIVA_BY_MODULE.md` | R3-24 | For each module and its owner: how it works in this code, the five hardest questions a panel could ask, and short answers that cite files and numbers. |
| `docs/CP2_BACKLOG.md` | R3-19 | What isn't built, where it would plug in (file and function), what data it needs, and how we'd know it works. |

**Retired numbers.** These must not appear in anything you write, except where you quote them as wrong (the retired list and `PATENT_NUMBERS.md`): email F1 0.947, SMS F1 0.926 and URL F1 0.960 (the Review-2 deck); F1 0.991 and "linear SVM" (`TRAINING_REPORT.md`); "460 campaigns", "80.0% → 84.5%", "22 of 60", "32 of 60", "142 cases", "30-minute window", "50-minute window", the quiet-attack demo scores "87.8" and "85.6", voice "ROC-AUC 0.952" and "19 routes"; and every figure in the patent's Tables 2 and 3. List any hit in a file you didn't create, and don't edit those files.

## Phase 6. Wrap up

Finish `CHECKLIST_STATUS.md`. Then send me one message with:

1. what's done, with file paths;
2. every number that changed since Review-3: old, new, and why;
3. what's left for people, grouped by owner;
4. the decisions I need to make. At least: which defects to accept in writing, voice scope for CP1, and what to do about the patent describing a different build (rewrite it around this build, or build what it claims).

## 9. Checklist map: all 69 items

**Code** means you do it. **Inputs** means you produce the material and a person finishes it. **People** means it's not for you; track it with its owner.
Owners: B = Bala (correlation, event store, patent), V = Viraj (URL, API, console), K = Krishna (email, SMS, voice), M = Manoj (testing, documentation), T = the team.

| ID | Item | Owner | Who does it |
|---|---|---|---|
| R2-01 | URL false alarms on `https://` and a trailing slash (D-01) | V | Code |
| R2-02 | The SMS model catches smishing (D-09) | K | Code; may end as a proposed acceptance |
| R2-03 | A fixed time window (D-04) | B | Code: check 60 min is enforced everywhere and record where it's set |
| R2-04 | The console calls the API (D-06) | V | Code |
| R2-05 | Event store, identity linking, composite score and alert | B | Code |
| R2-06 | The API rejects bad input (D-02, D-07) | V | Code |
| R2-07 | The remaining correlation defects (D-03, D-05, D-08) | B | Code |
| R2-08 | The email defects (D-10, D-11) | K | Code |
| R2-09 | Correlation changes a verdict with real scores (D-12, SYS-14) | B, M | Code |
| R2-10 | Collect 40 + 40 real bundles (150 to refit) | T | People. You only check that the workbook → `refit_fusion.py` path works on the example rows. Never create bundles. |
| R2-11 | Meet the test plan's exit criteria | M | Code |
| R2-12 | A private git repo with real history | M | Code |
| R2-13 | Literature survey of at least 10 papers | T | People |
| R2-14 | SRS, ER and UML diagrams | M, B | Inputs: as-built diagrams. The guide's sign-off is People. |
| R2-15 | Record the Review-2 feedback and the fixes | B | People |
| R3-01 | Agree the CP1 scope with the guide | B | People; BUILT_VS_DESCRIBED helps |
| R3-02 | Freeze one final build | M | Code |
| R3-03 | Run the whole flow live | V, B | Code |
| R3-04 | The voice module, if it stays in CP1 | K | Code only if `VOICE_IN_CP1` is `yes` |
| R3-05 | Script and rehearse the demo | V, B | Inputs; the rehearsal is People |
| R3-06 | A review-proof demo laptop | V | Code, plus one real Wi-Fi-off run by a person |
| R3-07 | Re-run every test case on the final build | M | Code |
| R3-08 | Final metrics for each channel | K, V | Code |
| R3-09 | Correlation against the baselines | B, M | Code for the simulated half; the real half is blocked on R2-10 |
| R3-10 | Timing on the demo laptop | M | Code |
| R3-11 | The final test report | M | Code |
| R3-12 | One set of numbers everywhere | T | Code for FINAL_NUMBERS; restating it in the deck, report, patent and paper is People |
| R3-13 | Indian attack stories | B | Inputs: console presets |
| R3-14 | Results on real or lab-made bundles | M | Blocked on R2-10. Make sure `refit_fusion.py` output lands in `reports/` once bundles exist. |
| R3-15 | Who would use it | B | People |
| R3-16 | Privacy and ethics | M | Inputs: PRIVACY.md |
| R3-17 | The limitations slide | M | Inputs: the measured list in FINAL_NUMBERS |
| R3-18 | Each member's lessons learned | T | People |
| R3-19 | The Capstone-2 plan | B | Inputs: CP2_BACKLOG |
| R3-20 | The near-final project report | T | Inputs: `docs/report/` |
| R3-21 | README and user manual | V | Code |
| R3-22 | Plagiarism check on the report | M | People |
| R3-23 | The deck in the KLEF template | B | People; the figures come from you |
| R3-24 | Practise the Q&A | T | Inputs: VIVA_BY_MODULE. The mock viva is People. |
| R3-25 | Submit the abstract, slides, report and code 2 days early | B | People |
| R3-26 | Confirm the guide will attend | B | People |
| R3-27 | All four present, in formal attire, with the signed diary | T | People |
| PT-01 | Choose the filing route with KL IPFC | B | People |
| PT-02 | Confirm the applicant and the inventors | B | People |
| PT-03 | Match every measured number to the final run | B, M | Inputs: PATENT_NUMBERS |
| PT-04 | Know what is built and what is only described | T | Inputs: BUILT_VS_DESCRIBED |
| PT-05 | Go over prior art with KL IPFC | B | People |
| PT-06 | Check the fees | B | People |
| PT-07 | Finish the formatting | M | People |
| PT-08 | Prepare the forms | B | People |
| PT-09 | File it and keep the proof | B | People |
| PT-10 | Keep everything private until it is filed | T | Rule 8, in force now |
| MS-01 | Choose the journal with the guide | B | People |
| MS-02 | Move the draft into the journal's template | B | People |
| MS-03 | Rewrite the method and results from the final build | B, M | Inputs |
| MS-04 | Write related work and check every reference | K | People |
| MS-05 | Redraw the figures for print | V | Inputs: `reports/figures/` |
| MS-06 | Agree the author list | B | People |
| MS-07 | Add the declarations the journal asks for | M | People |
| MS-08 | Run a similarity check | M | People |
| MS-09 | Write the cover letter | B | People |
| MS-10 | Submit after the patent is filed | B | People |
| RD-01 | Check each drafted entry against what really happened | T | Inputs (dated facts) and People |
| RD-02 | Hand-copy the drafted pages | T | People |
| RD-03 | Record the guide's feedback each week | B | People |
| RD-04 | Collect the signatures | B | People |
| RD-05 | Update the traceability matrix (p.14) | M | Inputs |
| RD-06 | Update the evidence pages (p.49, p.50, p.53, p.54) | M | Inputs |
| RD-07 | Write the weeks after Review-2 | T | Inputs (dated log) and People |

## Appendix A. Voice (only if `VOICE_IN_CP1` is `yes`)

- **Data:** a public synthetic-speech benchmark with an official train, dev and eval split (ASVspoof 2019 LA is the usual one). Record its source and licence. Ask me before any download over 2 GB.
- **Model:** something that trains on this laptop's CPU in about an hour, such as cepstral features with a linear or tree model.
- **Honest number:** the equal error rate, overall and per attack, on the official evaluation split, whose attacks are unseen in training. Add a cross-dataset check if a second public set is available.
- **API:** `/score` accepts an audio file for `channel=call` and returns a synthetic-voice likelihood. Show it beside the bundle risk, not inside it, because the fusion model has never seen voice. TC-03 then changes from HTTP 501, so update the tests and the demo script.
- **Media cases** M-A01–M-A07 and M-X01–M-X05: team recordings only with the speaker's consent, kept out of git. Video (M-V01–M-V05) stays in Capstone-2.
