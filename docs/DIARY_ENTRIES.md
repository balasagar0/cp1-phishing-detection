# Research diary entries (CP1)

Written by `scripts/make_diary_entries.py` from build `cp1-final` (commit `18ba1d9`). Copy the text by hand into the diary, in its own columns. It replaces the blue 'sample / assumed' text of the filled draft wherever the two differ. Dates come only from git; numbers come from `reports/FINAL_NUMBERS.md`.

Where a cell needs a person (a signature or the guide's comment), it says who.

## Page 14: objectives traceability matrix

Req. refs are as in the filled draft. Status uses the diary's own words.

| ID | Success criterion | Req. ref | Design ref | Build ref | Test ref | Status | Guide sign |
|---|---|---|---|---|---|---|---|
| O1 | Per-channel modules (email, SMS, URL) trained and tested | REQ-01, REQ-02, REQ-08 | Email, SMS and URL modules (report chapter 1) | `cp1-final` (commit `18ba1d9`, 07 Nov 2026): `src/train_email.py`, `src/train_sms.py`, `src/train_url.py`, `models/` | EML, SMS and URL cases in `tests/test_final_cases.py`; TC-01, TC-02 | Achieved. Honest F1: email 82.2%, SMS smishing 87.1%, URL 90.4% | Guide signs after review |
| O2 | Correlation engine links events by identity and time | REQ-05, REQ-06, REQ-07, REQ-09 | Correlation engine and event store (report chapter 1) | `cp1-final` (commit `18ba1d9`, 07 Nov 2026): `src/predict.py` (`extract_ids`), `src/fusion.py`, `src/event_store.py`, `api.py` | `tests/test_window_and_ids.py`, `tests/test_event_store.py`, TC-04 to TC-08, COR and SYS cases | Partially achieved. Built and tested end to end; evaluated on simulated bundles only (engine F1 92.0% against 91.0% single-channel). Real bundles: 0 (R2-10) | Guide signs after review |
| O3 | Synthetic-voice detector flags cloned calls | REQ-03 | Voice module | Not built. No accessible voice data; calls are 'not assessed' | TC-03 shows 'not assessed' | Not started (CP2) | Guide signs after review |
| O4 | Existing deepfake detector integrated | REQ-04 | Deepfake module | Not built. The API accepts video events and marks them 'not assessed'; there is no stub module | `tests/test_defects.py::test_D13_a_call_or_video_does_not_block_or_change_the_bundle` | Not started (CP2) | Guide signs after review |
| O5 | Full-system evaluation against baselines | Evaluation | R3-09 comparison | `src/eval_comparison.py`, `reports/comparison_metrics.json` | `reports/FINAL_NUMBERS.md`, section 2 | In progress. Simulated half done; the real half waits for real bundles (R2-10) | Guide signs after review |

## Page 49: data and model evidence

### Datasets

| Dataset / source | Size & split | Licence & provenance | Pre-processing / issues |
|---|---|---|---|
| Email: CEAS_08, Enron, FraudEmail | 72,428 emails after cleaning and de-duplication. Honest test: leave one corpus out (train on two, test on the third). Pooled split 57,942 / 7,243 / 7,243 | CEAS_08: Repository has no licence file. Origin: CEAS 2008 spam challenge corpus; its own terms were not found. Enron: Repository licence GPL-3.0. Origin: Enron-Spam (Metsis, Androutsopoulos, Paliouras, 2006). Fraud: Repository has no licence file. It describes the data as the Fraud Email Corpus from Kaggle; that page's terms were not checked. | Scripts and styles dropped, link targets kept, tags stripped, numbers masked; duplicates and conflicting labels removed. Labels are 'unwanted or fraudulent', not strictly phishing |
| SMS: phishing SMS dataset (three classes) | 5,789 messages: 4,829 ham, 433 spam, 527 smishing. Test split 1,158 | Repository has no licence file. Same rows and class counts (5,971: 4,844 ham, 638 smishing, 489 spam) as Mishra and Soni, 'SMS Phishing Dataset for Machine Learning and Pattern Recognition', Mendeley Data, DOI 10.17632/f | Duplicates and conflicting labels removed. Smishing is a small class, so recall, F1 and a 95% interval are reported |
| URL: phishing and legitimate URL strings | 260,000 URLs on 101,523 hosts; split 80/20 by host (204,817 / 55,183); plus 12,000 constructed login URLs for training | Repository has no licence file; terms unknown. Popularity list: Repository has no licence file; terms unknown. | The model reads raw URL text, so no feature extraction service is needed. A random split would let a model score well by checking for a path, so hosts are held out |
| Correlation: simulated bundles | 24,000 train, 8,000 tune, 12,000 test | Built by `src/fusion.py` (`simulate`) from real held-out messages; the links are constructed | Simulated, labelled simulated everywhere. No real bundle collected yet (R2-10) |

### Experiments (the real figures for the 'F1 0.9x' placeholders)

| Experiment / run ID | Config / model | Metric | Baseline | Result vs target |
|---|---|---|---|---|
| EXP-01 | Email: TF-IDF word 1-2-grams, numbers masked, cross-corpus term filter, logistic regression | F1 on an unseen corpus (mean of 3 runs) | Pooled random split of the same data: 98.8% (flattering, never quoted alone) | **82.2%**; draft target 0.95: not met |
| EXP-02 | SMS: word and character TF-IDF, logistic regression, three classes | Smishing-vs-rest F1 with 95% CI | Spam-or-smishing vs ham on the same split: 98.2% (flattering) | **87.1%** (95% CI 82.3%-91.7%) |
| EXP-03 | URL: character n-grams of the URL text, three popularity flags, logistic regression (not XGBoost) | F1 with hosts held out | Feature benchmark, random split: 95.4% (flattering) | **90.4%** (95% CI 90.0%-90.9%); draft target 0.95: not met. Login false alarms 92.2% to 0.0%; popular-domain recall 49.9% to 30.7% |
| EXP-04 | Time window, fixed at 60 minutes before the evaluation ran (`src/fusion.py:13`) | Share of simulated linked attacks inside one window; engine F1 (simulated) | Engine with no window: F1 94.8% (simulated) | 95.6% of simulated linked attacks fit; engine F1 92.0% (simulated). Not swept on real scenarios: none collected |
| EXP-05 | Composite (learned window score) against single-channel, on the same simulated bundles | Precision, recall, F1, false-positive rate | Single-channel: F1 91.0%, false positives 14.1% | Engine: F1 92.0%, false positives 11.1% (simulated). Campaigns every single filter misses: 27; the engine flags 18.5% of them |
| EXP-06 | End-to-end through FastAPI: API, correlation, event store, alert, console | Steps passed; latency over real HTTP | Not applicable | 10 of 10 steps pass. Median 23 ms per email, 67 ms per full case |

### Bias / fairness and data-privacy check

- **Data.** The trained models use public research corpora only (table above). One exception was tried and not adopted: the v3 email attempt read the account owner's own legitimate mail, with the owner's consent, on this laptop only, under a written privacy specification. The export and that model were never committed or shared, and v3 failed the adoption rule and the privacy audit (`PRIVACY_AND_ETHICS.md`).
- **Identities.** The event store keeps the recipient and every identity token as HMAC-SHA256 with a secret key (not a plain or salted hash). Linking uses the hash. Message text is not stored unless a setting turns it on (`docs/PRIVACY.md`).
- **Bias.** The corpora are mostly English and several years old. Regional-language and current phishing are under-represented.
- **Imbalance.** Smishing is a small class (105 test messages), so recall, F1 and intervals are reported, not accuracy.
- **DPDP Act 2023.** Real bundles for R2-10 need written consent (`TESTCASE_FORMAT.md` asks for a basis on every real row). Old events are deleted with `POST /purge`.

## Page 50: build and version control

Repository: a private local git repository. `git remote -v` is empty; nothing is pushed until the patent is filed. No CI server: tests run locally. The history starts at `v2-baseline`, v2 exactly as received, so earlier work is not in this git history.

| Module / component | Owner | Repository / commit ref | CI-CD / build status |
|---|---|---|---|
| BLD-02, BLD-03 Email and SMS modules | Krishna | Branch `module/email-sms`, merged into `main` by `48b8cb7` 02 Nov 2026; `51d882b` 07 Nov 2026 | Local run on `cp1-final`: pytest 180 passed, 7 expected failures, 0 failed |
| BLD-04 URL module | Viraj | Branch `module/url`, merged into `main` by `fbee576` 02 Nov 2026 | Local run on `cp1-final`: pytest 180 passed, 7 expected failures, 0 failed |
| BLD-05 to BLD-07 Event store, identity linking, time window and score | Bala | Branch `module/correlation`, merged into `main` by `33f7b49` 02 Nov 2026; `f23b2b4` 02 Nov 2026 | Local run on `cp1-final`: pytest 180 passed, 7 expected failures, 0 failed |
| BLD-08, BLD-09 FastAPI service and React console | Viraj | Branch `module/api-console`, merged into `main` by `d0b815a` 02 Nov 2026; `0303319` 02 Nov 2026 | Local run on `cp1-final`: pytest 180 passed, 7 expected failures, 0 failed |
| BLD-10, BLD-11 Tests, test data and documents | Manoj | Branch `module/testing-docs`, merged into `main` by `343ec8f` 02 Nov 2026; `869422c` 02 Nov 2026; `b3ef2d3` 02 Nov 2026; `228614d` 07 Nov 2026; `dc88d21` 07 Nov 2026; `7761903` 07 Nov 2026; `50c3228` 07 Nov 2026; `18ba1d9` 07 Nov 2026; `ae6fac1` 07 Nov 2026; `bbb67c2` 07 Nov 2026 | Local run on `cp1-final`: pytest 180 passed, 7 expected failures, 0 failed |
| BLD-01 Data preparation | Krishna, Viraj | `download_data.sh` and `run_all.sh`, received with `v2-baseline` (commit `3cc60b8`, 02 Nov 2026) | Final run on `cp1-rc1` (commit `7761903`, 07 Nov 2026): recorded, not adopted (`reports/final_run/`) |
| BLD-12 Deepfake stub | Viraj | Not built. Video events are accepted and marked 'not assessed' (`src/predict.py`, `NOT_ASSESSED`) | Not applicable |

Tags: `v2-baseline` (commit `3cc60b8`, 02 Nov 2026); `test-run-20261102-0` (commit `4bc2eb7`, 02 Nov 2026); `test-run-20261102-1` (commit `869422c`, 02 Nov 2026); `test-run-20261102-2` (commit `b3ef2d3`, 02 Nov 2026); `test-run-20261107-3` (commit `51d882b`, 07 Nov 2026); `cp1-rc1` (commit `7761903`, 07 Nov 2026); `cp1-final` (commit `18ba1d9`, 07 Nov 2026).

## Page 53: unit test execution

Run on `cp1-final`, 2026-11-07. The page has room for about 20 rows: copy these 20 (High priority first). All 59 executed unit-level cases are in `reports/FINAL_TEST_REPORT.md`.

| Test-case ID | Input | Expected output | Actual output | Pass/Fail |
|---|---|---|---|---|
| COR-01 | Email, SMS and URL all carry bit.ly/xyz. Scores 70, 65, 95, all phishing. | Same intent: v2 has no evidence strings or bonus. Same intent: the shared link is found as a shared identity token and the  | shared tokens ['dom:bit.ly']; shares_identity 1.0; risk 1.000 | Pass |
| COR-02 | Email carries the flagged URL. Email 70, SMS 10 (legitimate), URL 95. | Same intent: Same intent as COR-01: the flagged URL inside the email gives the email the URL's domain token, shared with th | email tokens ['dom:secure-bank-verify.xyz']; url tokens ['dom:secure-bank-verify.xyz']; shared ['dom:secure-bank-verify.xyz'] | Pass |
| COR-03 | SMS carries the flagged URL. Email 10 (legitimate), SMS 65, URL 95. | Same intent: Same intent as COR-02 for the SMS. Uses fixed detector scores through v2's correlation engine (Fusion.risk), a | sms tokens ['dom:secure-bank-verify.xyz']; shared ['dom:secure-bank-verify.xyz'] | Pass |
| COR-04 | Same link and brand in email, SMS and URL, but all three are legitimate. | Same intent: v2 reports a shared link as a fact whatever the scores, and the learned model decides its weight; there is no  | scores 0.10 / 0.12 / 0.05; shared ['dom:securebank.com']; bundle risk 0.030 | Pass |
| COR-10 | Email 55, SMS 52 and URL 58, all phishing, sharing bit.ly/xyz (scenario S-03). | Same intent: v2 has one alert line (0.5), so S-03's fixed scores 0.55 / 0.52 / 0.58 each alert on their own and the SUSPICI | best single 0.58 (alerts alone); bundle risk 1.000; shared ['dom:bit.ly'] | Pass |
| COR-12 | Three risky channels with timestamps 0, +3 days and +6 days. | Same intent: v2 has no evidence strings. Same intent: events 3 and 6 days apart fall in separate 60-minute windows, are not | windows 3; shared []; risk 0.800 (strongest single 0.8) | Pass |
| COR-14 | Email, SMS and URL carry secure-bank-verify.online/login. All risky. | Same intent: Same intent: the shared link on a .online host is found as a shared identity token (full public suffix list).  | shared ['dom:secure-bank-verify.online'] | Pass |
| EML-01 | Run every Data-Email row with Group = Standard and Expected = Phishing. | At least 90% are predicted phishing. | 7/11 predicted phishing (64%); wrong: E-P03 10.2, E-P06 5.2, E-P07 23.7, E-P09 20.6 | Fail |
| EML-02 | Run every Data-Email row with Group = Standard and Expected = Legitimate. | At least 90% are predicted legitimate. | 11/11 predicted legitimate (100%) | Pass |
| EML-09 | Evaluate on the held-out corpus and compare its F1 with the normal test F1. | F1 on the held-out corpus is within 10 percentage points of the normal test F1. If not, record it as a limitation. | normal (pooled random) test F1 98.8%; held-out corpus F1: CEAS_08 86.1%, Enron 74.9%, FraudEmail 85.7%; mean 82.2%. Largest gap 23.8 points  | Known limitation |
| EML-10 | Read models/email_metrics.json (accuracy, precision, recall, F1, confusion matrix). | F1 is 0.90 or higher. | reports/email_metrics.json pooled random test: F1 0.9876, precision 0.9872, recall 0.9880, confusion [[3616, 46], [43, 3538]]. Honest metric | Pass |
| PRE-05 | Extract features for U-P01 twice. | Same intent: v2 has no 30-feature URL extractor. Its URL representation is the canonical URL's character 3-5-gram hashing ( | width 1048579 (expected 1048579), identical on repeat=True, popularity flags for the IP host=[0.0, 0.0, 0.0] | Pass |
| SCO-01 | Call verdict_for() with 0, 30, 31, 60, 61 and 100. | Same intent: v2 has no SAFE / SUSPICIOUS / HIGH RISK bands (0-30-60-100). Its one line is 0.5. Same intent: the boundary is | channel labels at 0, 0.4999, 0.5, 1 -> ['benign', 'benign', 'malicious', 'malicious']; one-event bundle at 0.5 -> risk 0.5, at 0.4999 -> ris | Pass |
| SCO-02 | Analyse S-01, S-02 and S-05. | Same intent: v2's bundle risk is a learned model, not min(100, best + bonus), so the formula part is N/A. The second part i | S-01: best 1.000, bundle 1.000; S-02: best 0.999, bundle 1.000; S-05: best 0.999, bundle 0.999 | Pass |
| SCO-06 | Call analyze({}). | Same intent: v2 has no analyze({}). The empty case goes to POST /correlate. Expected: rejected with HTTP 4xx or CANNOT_ASSE | POST {} -> HTTP 422; POST {"events": []} -> HTTP 422: {"detail":"no events"} | Pass |
| SCO-08 | Analyse S-06 (phishing email with harmless SMS and URL). | Same intent: Same intent through /correlate: with S-06, the bundle risk is at least the email score. | events: email 0.999, sms 0.194, url 0.005; single-channel alert True; bundle risk 0.957 (elevated risk); windows 1; shared [] | Fail |
| SMS-01 | Run every Data-SMS row with Group = Standard and Expected = Phishing. | At least 90% are predicted phishing. | 12/12 predicted phishing (100%). SMS alert score = the score /score returns for SMS, which is 1 - P(ham), i.e. spam or smishing. | Pass |
| SMS-02 | Run every Data-SMS row with Group = Standard and Expected = Legitimate. | At least 90% are predicted legitimate. | 11/12 predicted legitimate (92%); wrong: S-L05 78.8 | Pass |
| SMS-04 | Run S-L01 and S-H06. | Both are labelled legitimate. | S-L01: benign 0.2041, S-H06: benign 0.3472 | Pass |
| SMS-08 | Read models/sms_metrics.json. | Same intent: v2's SMS model has three classes. The plan's 'spam class' (unwanted vs ham) is v2's spam-or-smishing vs ham on | reports/sms_metrics.json spam-or-smishing vs ham: F1 0.9815, precision 0.9947, recall 0.9688, confusion [[965, 1], [6, 186]]. Honest metric  | Pass |

## Page 54: issue tracker

The defects found by testing. Status comes from the run; accepting a defect is the team's decision.

| Issue no. | Description | Impact | Owner | Status | Guide sign |
|---|---|---|---|---|---|
| D-01 | The URL model flags legitimate URLs as phishing when they start with https:// or end with a slash. github.com scores 0.3 (legitimate) but https://github.com sco | High; failing: URL-07 | Viraj | Open | Guide signs after review |
| D-02 | The API accepts empty or invalid input and returns a score. POST {} to /analyze/email returns 'phishing' 73.2. POST {} to /analyze/sms returns 'legitimate' 11.2 | Medium; all linked cases pass | Viraj | Closed | Guide signs after review |
| D-03 | A case with nothing to assess is reported SAFE. POST {} to /analyze returns combined score 0 and 'LOW RISK'. A case with only a video transcript (the stub says  | Medium; all linked cases pass | Bala | Closed | Guide signs after review |
| D-04 | Time-proximity evidence has no maximum window. The engine works out the span between the email, SMS and URL timestamps but never compares it with a limit. Event | High; all linked cases pass | Bala | Closed | Guide signs after review |
| D-05 | Shared-link matching only recognises links that end in one of 12 listed endings (com, net, org, tk, xyz, top, club, info, biz, ly, click, gq, ml). The same link | Medium; all linked cases pass | Bala | Closed | Guide signs after review |
| D-06 | No CORS settings. A browser page on another origin (for example the React console on http://localhost:5173) is blocked: GET /health returns no Access-Control-Al | High; all linked cases pass | Viraj | Closed | Guide signs after review |
| D-07 | Non-numeric timestamps cause HTTP 500. timestamps is an untyped dict. When two or more channels are flagged and email, SMS and URL all have timestamps, the engi | Low; all linked cases pass | Viraj | Closed | Guide signs after review |
| D-08 | Ordinary words count as a 'claimed identity'. The engine takes the first shared word of 4 or more letters that is not in a 16-word stop list. In the demo scenar | Medium; all linked cases pass | Bala | Closed | Guide signs after review |
| D-09 | The SMS model misses most phishing-style messages. Only 1 of 12 standard phishing SMS was flagged (bank, KYC, UPI, e-challan and parcel-fee lures) and 2 of 4 ha | High; failing: SMS-03 | Krishna | Open | Guide signs after review |
| D-10 | The email model flags some legitimate consumer-style mail: payment receipt E-L08 scored 82.4, statement notice E-H06 73.5, security alert E-H04 96.0, personal p | Medium; failing: EML-03 | Krishna | Open | Guide signs after review |
| D-11 | clean_text() does not remove HTML. Tags and script text stay in what the model sees. The effect on accuracy was not measured. | Low; all linked cases pass | Krishna | Closed | Guide signs after review |
| D-12 | With the real models, correlation never changes the verdict on the test cases. Email, SMS and URL each score 88 or more on their own, so the best channel is alr | Medium; failing: SYS-14 | Bala | Open | Guide signs after review |
| D-13 | On v2, /correlate refuses the whole bundle with HTTP 501 when any one event is a call or a video. The email and SMS in the same bundle are never scored. | Medium; all linked cases pass | Bala | Closed | Guide signs after review |
| D-14 | On v2, the API does not start when one model file is missing (FileNotFoundError at import). There is no degraded mode. | Medium; all linked cases pass | Viraj | Closed | Guide signs after review |
| D-15 | clean_text(123) returns '123'. The plan expects an empty string for any input that is not text. | Low; all linked cases pass | Krishna | Closed | Guide signs after review |
| D-16 | The SMS model flags legitimate transactional bank SMS: the card-use alert S-H05 and the bill reminder S-H08 in the hard group, and the credit alert S-L05 in the | Medium; failing: SMS-03 | Krishna | Open | Guide signs after review |
| D-17 | The email model misses standard phishing emails that the old build caught: E-P03 (password expiry), E-P06 (fake invoice), E-P07 (gift-card CEO fraud) and E-P09  | High; failing: EML-01, EML-03 | Krishna | Open | Guide signs after review |
| D-18 | The learned correlation model can give a bundle less risk than its strongest event when the other events in the window are weaker: in S-06 the email alone score | Low; failing: SCO-08, UI-03 | Bala | Open | Guide signs after review |

## Page 45, task 11: the time window

| Task | Owner | Start | End | % done | Depends on / evidence |
|---|---|---|---|---|---|
| 11. Time window: fixed at 60 minutes and enforced everywhere | Bala | 02 Nov 2026 (value as received in v2) | 02 Nov 2026 (D-04 closed, commit `3d42061`) | 100% for CP1 | Set at `src/fusion.py:13`; used at `src/eval_comparison.py:40`, `src/eval_comparison.py:61`, `src/eval_window.py:39`, `src/fusion.py:59`, `src/fusion.py:71`, `src/fusion.py:143`. Not swept on the scenario set: no real scenarios exist yet. The simulated table in `reports/results.md` is for information only. `src/refit_fusion.py` suggests a value once real bundles exist (CP2) |

## Dated log of the CP1 finish work (from git)

| Date and time | Commit | What |
|---|---|---|
| 02 Nov 2026 10:29 | `3cc60b8` | R2-12: v2 baseline exactly as received (cp1_trained_detectors_v2.zip) |
| 02 Nov 2026 10:29 | `e940826` | R2-12: add files that sat next to v2 before this work started |
| 02 Nov 2026 10:39 | `054760e` | R2-12 NFR-04: lock file, model manifest and secret scan |
| 02 Nov 2026 10:39 | `c346fb9` | R2-09: codify the demo cases TC-01 to TC-08 as tests |
| 02 Nov 2026 10:39 | `ace2557` | R2-12: run_all.sh uses the project venv and stops on a failed step |
| 02 Nov 2026 10:39 | `d276f70` | R2-12: CLAUDE.md carries the CP1 rules (sections 0 to 3 of the brief) |
| 02 Nov 2026 11:06 | `4bc2eb7` | R2-12 R3-08: Phase 0 baseline check and checklist status |
| 02 Nov 2026 11:08 | `962223c` | R3-07 R2-11: port the 112 test-plan cases to v2 (tests/test_final_cases.py) |
| 02 Nov 2026 11:10 | `b151be2` | R2-08 D-11 D-15: strip scripts and HTML before tokenising, keep link targets |
| 02 Nov 2026 11:11 | `3ec9530` | R2-06 D-02: check_url() tells a URL from a malformed string |
| 02 Nov 2026 11:13 | `3d42061` | R2-07 D-03 D-13: calls and video are "not assessed"; nothing assessable is CANNOT_ASSESS |
| 02 Nov 2026 11:15 | `658d63c` | R2-04 R2-06 D-06 D-02 D-14: explicit CORS origins, refuse malformed input, degraded mode |
| 02 Nov 2026 11:19 | `44cf209` | R2-11 R3-07 R2-10: workbook filler, defect registry, refit-path test |
| 02 Nov 2026 11:25 | `3ea27f3` | R2-11 R3-07: Phase 1 run, FINAL workbook and defect log; checklist updated |
| 02 Nov 2026 11:36 | `5dca0f1` | R2-05 R3-03: event store with campaigns and alerts, grouped by v2's own window code |
| 02 Nov 2026 11:43 | `582f15d` | R2-04 R3-13 R3-03: console built with Vite and served by the API; presets from the API |
| 02 Nov 2026 11:44 | `e69e46b` | R3-06: scripts/offline_check.py proves no network at runtime |
| 02 Nov 2026 11:49 | `47dc296` | R2-04 R3-06 UI-01..UI-07: Playwright console checks and screenshots |
| 02 Nov 2026 11:50 | `d4996b0` | R2-12: store the lock file and manifest with LF (.gitattributes) |
| 02 Nov 2026 11:52 | `fc0d0f0` | R2-12: store the lock file and manifest with LF on this branch too |
| 02 Nov 2026 11:55 | `659035a` | R2-09 R2-11 R3-07: Phase 2 run, R2-09 evidence table, checklist updated |
| 02 Nov 2026 12:21 | `5a2d853` | R2-12: store the lock file and manifest with LF on this branch too |
| 02 Nov 2026 12:38 | `74407bd` | R2-01 R2-02 R2-08 (in progress): Phase 3 work so far, and scripts and docs written ahead |
| 07 Nov 2026 09:52 | `31e206e` | R2-08 R3-19: email candidate attempt 1 result; status and roadmap file |
| 07 Nov 2026 09:57 | `e396630` | R2-08: email candidate attempt 2, rule fixed before running |
| 07 Nov 2026 09:58 | `3a9edb8` | R2-14: the /events sequence diagram renders (Mermaid read ';' as a statement break) |
| 07 Nov 2026 10:09 | `09c9d07` | R2-08 D-10 D-17: email attempt 2 fails the adoption rule; v2's email model stays |
| 07 Nov 2026 10:10 | `bee2cee` | R2-11: checklist counts after R2-08 became blocked |
| 07 Nov 2026 10:28 | `4553073` | R2-08 D-10 D-17: email model v3 set up, rule fixed before running |
| 07 Nov 2026 11:10 | `f57ddc5` | R2-08: privacy-first streaming path for the owner's Gmail export; 10 privacy tests |
| 07 Nov 2026 11:12 | `56421ea` | R3-16: PRIVACY_AND_ETHICS.md and the v3 model privacy audit |
| 07 Nov 2026 11:23 | `30d2a13` | R2-08: the network guard allows loopback; v3's first run stopped on it |
| 07 Nov 2026 11:49 | `4f9b8a0` | R2-08 D-10 D-17: email v3 not adopted; it fails the adoption rule and the privacy audit |
| 07 Nov 2026 11:52 | `0e86002` | R2-12 R2-02: Phase 3 closed; the owner keeps the v3 model and the export locally |
| 07 Nov 2026 11:53 | `0d12698` | R2-12: the model manifest covers the live models only |
| 07 Nov 2026 12:36 | `a31b6ba` | PT-03 PT-04 R3-09: the patent will be written from this build |
| 07 Nov 2026 12:43 | `c417d44` | R3-02 R3-03 R2-11 R3-09: Phase 4 preparation before cp1-rc1 |
| 07 Nov 2026 16:27 | `1b2e4b5` | R3-02 R3-08 R3-09: final run on cp1-rc1, recorded and not adopted |
| 07 Nov 2026 16:49 | `4f29865` | R3-03 R3-07 R3-10 R2-11: Phase 4.2-4.4 checks before cp1-final |
| 07 Nov 2026 17:13 | `c74c4ea` | R2-11 R3-02 R3-07: ported cases, workbook and exit criteria on cp1-final |
| 07 Nov 2026 17:52 | `ff63440` | R3-12 R3-11 R3-08 R3-05 R3-20 R3-24 PT-03 PT-04 MS-03 MS-05 RD-05 RD-06 RD-07: Phase 5 documents from cp1-final |
