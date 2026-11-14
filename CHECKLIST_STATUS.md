# CP1 checklist status

All 69 items from section 9 of `CP1_FINISH_TASK.md`. Updated at the end of every phase. Nothing is marked done without evidence (a file, a test or a commit).

**Last update:** end of Phase 6 (wrap-up), 14 Nov 2026. All six phases done. Build `cp1-final` (commit `18ba1d9`); documents generated from it.

**Status words:** done (finished, with evidence) · partial (some of it is done; the rest is named) · open (not started) · blocked (waiting on something named) · people (a person does it; tracked here).

**Owners:** B = Bala, V = Viraj, K = Krishna, M = Manoj, T = the team.

## Phase progress

| Phase | State | Evidence |
|---|---|---|
| 0. Baseline and audit | done | `reports/baseline_check.md`, `reports/model_manifest.json`, `tests/test_demo_cases.py`, tags `v2-baseline` and `test-run-20261102-0` |
| 1. Port the test suite, re-test defects, code fixes | done | `tests/test_final_cases.py` (112 cases), `reports/final_cases_results.json`, `reports/Test_Cases_and_Test_Data_FINAL.xlsx`, `reports/defect_log.md`, `tests/test_defects.py`; merges of `module/testing-docs`, `module/email-sms`, `module/url`, `module/correlation`, `module/api-console`; tag `test-run-20261102-1` |
| 2. Event store, live flow, console | done | `src/event_store.py` and its routes, `tests/test_event_store.py`; console in `console/` served at `/`; `scripts/offline_check.py` (`reports/offline_check.md`); `scripts/ui_checks.py` (`reports/ui_checks.json`, `reports/screenshots/`); `reports/r2_09_evidence.md`; tag `test-run-20261102-2` |
| 3. Models | done | No model adopted. Email: three attempts, none passed the adoption rule (`reports/candidates/email_candidates*.md`), v3 privacy record in `PRIVACY_AND_ETHICS.md`; URL: no retrain needed (`reports/candidates/url_d01.md`); SMS: no licensed data (`reports/candidates/sms_d09.md`); tag `test-run-20261107-3` |
| 4. Freeze and final run | done | Tags `cp1-rc1` and `cp1-final`. Final run on `cp1-rc1` recorded and not adopted (`reports/final_run/README.md`, `reports/final_run_check.md`); R3-09 comparison on the live models (`reports/comparison_metrics.json`); every check on `cp1-final`: `reports/final_cases_results.json`, `reports/e2e_check.md`, `reports/ui_checks.json`, `reports/offline_check.md`, `reports/benchmark.md`, `reports/nfr05_fresh_clone.json`, `reports/exit_criteria.md`, the FINAL workbook |
| 5. Documents | done | All generated from `cp1-final` by `scripts/make_documents.py` (no number typed): `reports/FINAL_NUMBERS.md`, `reports/FINAL_TEST_REPORT.md`, `reports/figures/`, `docs/DEMO_SCRIPT.md`, `docs/PATENT_BASIS.md`, `docs/MANUSCRIPT_METHOD_RESULTS.md`, `docs/VIVA_BY_MODULE.md`, `docs/DIARY_ENTRIES.md`, `docs/report/`; templates in `docs/templates/`; checked by `tests/test_documents.py`. Also `README.md`, `docs/USER_MANUAL.md`, `docs/PRIVACY.md`, `docs/CP2_BACKLOG.md`, `docs/diagrams/` |
| 6. Wrap up | done | `docs/PHASE6_SUMMARY.md` (generated from `cp1-final`): what is done, the Review-3 figures against this build, people tasks by owner, decisions for the owner; this checklist finished |

## Things found in Phase 0 that a person should know

1. **The patent spec is not in `docs/inputs/`, and is no longer needed** (decision of 7 Nov 2026: the patent will be written from this build). `Patent_Complete_Specification_Form2` (.docx or .md) was not added. PT-03, PT-04 and the patent row of R3-09 (Phase 4.3) need it. A different file, `D:\Capstone_HTE Project\cla\Patent_Disclosure_Draft.docx`, exists; it was not used, because it is not the document the brief names. S should add the complete specification to `docs/inputs/`.
2. **The inputs sit in `docs/inputs/cp1_inputs/`**, one folder deeper than the brief says. Everything reads them from there.
3. **The optional inputs are not in `docs/inputs/`.** `Test_Plan_Phishing_Detection.docx` exists at `D:\Capstone_HTE Project\Claude files\` and the SRS was not found. The workbook carries the targets and exit criteria that Phase 1 needs, so neither blocks work.
4. **Files from section 1.4 (wrong material).** None is inside this project folder. Elsewhere under `D:\Capstone_HTE Project` there are `Claude files\CP1_Team_Study_Guide.md`, `Claude files\TRAINING_REPORT.md`, `Claude files\AI-Based-Multi-Channel-Phishing-Detection-System_Review2.pptx` and `AI-Based-Multi-Channel-Phishing-Detection-System [Autosaved].pptx`. They were not opened, used, edited or deleted.
5. **Five files sat next to v2 before this work.** `CLAUDE.md`, `console.html`, `RUN_DEMO.bat` and `RUN_TESTS.bat` (30 Oct) and `CP1_FINISH_TASK.md` (2 Nov). They are committed unchanged in the second commit, apart from `CLAUDE.md`, which gained sections 0 to 3 of the brief (0.5).
6. **The smoke test passes 11 checks, skips 1 and then stops**, as documented: its synthetic generator needs `data/processed/pool_*.csv`, which only `run_all.sh` makes. The skipped check needs a spreadsheet program to recalculate formulas. `CLAUDE.md` said "the first 12 pass"; the true count is 11 passed and 1 skipped.
7. **On Windows the smoke test stopped even with the data.** `tests/make_synthetic_testcases.py` writes its CSV in the system code page. With a one-line UTF-8 fix (scratch worktree only), the smoke test passed all its checks apart from the spreadsheet one it skips (`reports/baseline_check.md`, finding 6). Fixed in Phase 1 (commit 962223c); in this folder the smoke test now passes 24 checks and skips 1.
8. **v2 reproduces from scratch.** A fresh `download_data.sh` and `run_all.sh` on `v2-baseline` gave the same Review-3 figures; every data source still downloads; the URL benchmark, which never finished before, finished here. Small changes in two non-deployed baselines and five probe scores are listed in `reports/baseline_check.md`. The downloaded data is kept in `data/` (gitignored).

## Found in Phase 1

1. **Six new defects on v2 (D-13 to D-18)**, all in `reports/defect_log.md` and the FINAL workbook. Fixed in Phase 1: D-13 (a call or video blocked the whole bundle), D-14 (no degraded mode), D-15 (`clean_text(123)`). Open: D-16 (legitimate bank SMS flagged), D-17 (4 of 11 standard phishing emails missed), D-18 (the bundle can score below its strongest event; proposed for acceptance).
2. **Defects closed:** D-02, D-03, D-04, D-05, D-06, D-07, D-08, D-11, D-13, D-14, D-15. **Open:** D-01, D-09, D-10, D-12, D-16, D-17, D-18. Proposals (never acceptances) are written for D-12 and D-18.
3. **Behaviour changed on purpose.** TC-03 through `/correlate` now answers CANNOT_ASSESS instead of HTTP 501 (R2-07); its `/score` answer is still HTTP 501. CORS no longer answers '*'. The URL endpoint refuses strings that are not URLs.
4. **Not changed:** no model was retrained. The email cleaner changed, but none of the 28 workbook emails, the demo-case emails or the 9,000 pooled emails changes, so the live email model's inputs are the same for them. The retrain is Phase 3.
5. **Run order:** `pytest tests/` now runs everything except the script-style smoke test (`tests/conftest.py`); `RUN_TESTS.bat` uses the venv.

## Found in Phase 2

1. **The event store gives the same answer as `/correlate`.** It calls v2's own window scorer (`fusion.window_risks`; `windowed_risk` now takes the highest of it, identical on 3,000 simulated bundles). TC-04, TC-06 and TC-07 match to 3 decimals; TC-07 gives three one-event campaigns.
2. **UI-03 fails, on D-18.** In TC-04 the bundle shows 99.99% beside an SMS at 100.00%; the plan wants the correlated score at or above every single score. Linked to D-18 (proposed for acceptance, not accepted).
3. **Privacy detail found:** uvicorn's access log prints request paths, which would carry `?recipient=` in clear. `RUN_DEMO.bat` now starts uvicorn with `--no-access-log`; `start_demo.bat` will too.
4. **`/docs` and `/redoc` are off.** Their pages load Swagger UI from a CDN, which breaks the offline rule. `/openapi.json` stays; the console replaces them for the demo.
5. **`console.html` is served at `/lite`.** Opened as a file it can no longer reach the API, because CORS no longer answers '*'.
6. **The four Indian stories, run once:** IN-01 to IN-03 alert; IN-04, the legitimate order, stays quiet. Nothing was tuned.

## All 69 items

| ID | Item | Owner | Who does it | Status | Evidence | Next step |
|---|---|---|---|---|---|---|
| R2-01 | URL false alarms on `https://` and a trailing slash (D-01) | V | Code | partial | D-01 Open (`reports/defect_log.md`): the scheme and trailing-slash flips are gone (URL-05, URL-06, URL-02, SYS-13 pass, because `canon()` normalises in training and serving); URL-07 fails on U-H06, a real Google sign-in URL with a long query | Phase 3.2: no retrain for the scheme (it no longer flips). Record U-H06 as the login-page trade-off; the team decides on D-01 |
| R2-02 | The SMS model catches smishing (D-09) | K | Code; may end as a proposed acceptance | blocked | SMS-01 passes; SMS-03 fails on bank alerts (D-16). No real SMS data with a checkable licence exists, so no retrain (`reports/candidates/sms_d09.md`). D-09 has a written proposal; D-16 stays open | The team decides on the D-09 proposal; D-16 needs licensed or consented legitimate transactional SMS (CP2) |
| R2-03 | A fixed time window (D-04) | B | Code | done | One line sets the window: `src/fusion.py` line 13 `DEFAULT_WINDOW_MIN = 60.0`. `/correlate` and the event store read it through `Fusion.window` (`api.py` line 42, `src/event_store.py`), `refit_fusion.py` and `eval_window.py` read the same constant, the console takes it from `/health`. Tests: COR-12, SYS-09, `test_D04_*`, `test_window_edges_59_and_61_minutes` | Nothing for code. A refit on real bundles may store its own window (R2-10) |
| R2-04 | The console calls the API (D-06) | V | Code | done | The console calls the live API on every view (`/health`, `/presets`, `/correlate`, `/events`, `/campaigns`, `/alerts`) and is served by FastAPI at `/` (built files in `console/dist`). CORS names explicit origins. UI-01, UI-02, UI-04 to UI-07 pass in Chrome and Edge (`reports/ui_checks.json`); UI-03 fails on D-18 | Nothing for code. The team decides on D-18 |
| R2-05 | Event store, identity linking, composite score and alert | B | Code | done | `src/event_store.py` (SQLite, HMAC-hashed recipient and tokens, text only with `CP1_STORE_CONTENT=1`), routes `POST /events`, `GET /campaigns`, `GET /campaigns/{id}`, `GET /alerts`, `POST /alerts/{id}/ack`, `POST /purge`. `tests/test_event_store.py` (12 tests): equal to `/correlate` on TC-04, TC-06, TC-07; linking; 59/61-minute edges; two recipients; one alert; calls in the timeline; purge; restart; privacy | Phase 4.2 end-to-end check on the frozen build |
| R2-06 | The API rejects bad input (D-02, D-07) | V | Code | done | D-02 and D-07 Closed: empty text, unknown channels and malformed URLs give HTTP 422 with a reason (`check_url`, commits 3ec9530, 658d63c); EML-07, SMS-07, URL-08, API-08 pass; `test_D02_*`, `test_D07_*` | Nothing for code. Re-run in Phase 4 |
| R2-07 | The remaining correlation defects (D-03, D-05, D-08) | B | Code | done | D-03, D-05, D-08 Closed, and D-13 (found on v2) Closed: calls and video are 'not assessed', nothing assessable is CANNOT_ASSESS (commit 3d42061); SCO-06, VV-03 to VV-05, COR-07, COR-09, COR-14, SYS-07, SYS-08, SYS-11, SYS-12 pass; `test_D03_*`, `test_D05_*`, `test_D08_*`, `test_D13_*` | Nothing for code. Re-run in Phase 4 |
| R2-08 | The email defects (D-10, D-11) | K | Code | blocked | D-11 Closed (cleaner fix, commit b151be2, PRE-01). D-10 and D-17 Open. Three email retrain attempts (`reports/candidates/email_candidates.md`, `email_candidates_attempt2.md`, `email_candidates_v3.md`) all failed the adoption rule on (b) and (c); v3 also failed the privacy audit. v2's email model stays live | The team decides how to proceed after three attempts (keep v2 for CP1; real-mail false alarms are a CP2 item) |
| R2-09 | Correlation changes a verdict with real scores (D-12, SYS-14) | B, M | Code | partial | `reports/r2_09_evidence.md`: S-03 on the old build (fixed scores), S-03 on v2's engine, TC-06 against its control TC-07, TC-05, and the simulated weak campaigns, each labelled. SYS-14 as written still fails (D-12 open, proposal written) | The team decides on the D-12 proposal; real bundles (R2-10) settle the claim |
| R2-10 | Collect 40 + 40 real bundles (150 to refit) | T | People | people | `testcases/review2_testcase_workbook.xlsx` holds 0 real bundles. The path workbook -> `refit_fusion.py` -> `reports/real_bundles_report.md` works on the example rows (`tests/test_refit_path.py`; smoke test 24 checks pass with the data present) | The team collects 40 coordinated and 40 benign bundles (150 to refit). No bundle is ever generated |
| R2-11 | Meet the test plan's exit criteria | M | Code | partial | Judged on `cp1-final` against the plan's own targets (`reports/exit_criteria.md`, `scripts/exit_criteria.py`). Met: 1, 2, 4a, 6. Not met: 3 (sample groups), 4b (honest measures), 5 (SYS-14), 7 (open High defects D-01, D-09, D-17). FINAL workbook filled (`reports/Test_Cases_and_Test_Data_FINAL.xlsx`, run record names `cp1-final`) | The team decides on the open defects and the written proposals in `reports/defect_log.md`. Criterion 5 needs real bundles (R2-10); 3 and 4b need better models (CP2) |
| R2-12 | A private git repo with real history | M | Code | done | Local repo with real history: `v2-baseline` is v2 byte for byte; every commit uses the configured identity and the Claude co-author line; module branches merged into `main` with `--no-ff`; tags per phase; `git remote -v` is empty | Keep committing at each phase end; never push |
| R2-13 | Literature survey of at least 10 papers | T | People | people | Not a code item | The team writes it |
| R2-14 | SRS, ER and UML diagrams | M, B | Inputs: as-built diagrams | partial | As-built Mermaid diagrams, rendered to SVG and PNG: components, the `/correlate` sequence, the `/events` sequence, the event-store ER diagram (`docs/diagrams/`) | The guide signs off the diagrams (Manoj and Bala take them to the guide) |
| R2-15 | Record the Review-2 feedback and the fixes | B | People | people | Not a code item | Bala records it |
| R3-01 | Agree the CP1 scope with the guide | B | People | people | Not a code item | Bala meets the guide; `docs/BUILT_VS_DESCRIBED.md` (Phase 5) supports it |
| R3-02 | Freeze one final build | M | Code | done | Tags `cp1-rc1` (commit `7761903`) and `cp1-final` (commit `18ba1d9`). The final run on `cp1-rc1` is recorded in `reports/final_run/`; its models were not adopted (owner, 7 Nov 2026), so `cp1-final` ships v2's models | None. Every later number comes from `cp1-final` |
| R3-03 | Run the whole flow live | V, B | Code | done | `scripts/e2e_check.py` walks API -> correlation -> event store -> alert -> console over real HTTP: every step passes (`reports/e2e_check.md`). The console's screens are checked in Chrome and Edge (`reports/ui_checks.json`, `reports/screenshots/`) | Viraj and Bala show it live in the review (R3-05) |
| R3-04 | The voice module, if it stays in CP1 | K | Code only if `VOICE_IN_CP1` is `yes` | people | `VOICE_IN_CP1` is `no`. Calls answer HTTP 501 on `/score` (`tests/test_demo_cases.py::test_tc03_voice_call_is_not_assessed`) | S and the team confirm voice scope. If it becomes `yes`, Appendix A |
| R3-05 | Script and rehearse the demo | V, B | Inputs; the rehearsal is People | partial | `docs/DEMO_SCRIPT.md` (generated from `cp1-final` by `scripts/make_documents.py`; `tests/test_documents.py` checks it is current and carries no typed or retired number): order TC-06, TC-07, TC-05, then the rest, expected values, what to say at TC-03, fallbacks; `scripts/preflight.py` and `start_demo.bat` give GO or NO-GO | Viraj and Bala rehearse it twice on the demo laptop |
| R3-06 | A review-proof demo laptop | V | Code, plus one real Wi-Fi-off run by a person | partial | `scripts/offline_check.py` passes on `cp1-final`; `start_demo.bat` runs `scripts/preflight.py` (packages, model hashes, console, API, the eight demo cases, offline) and opens the console | Viraj does one real Wi-Fi-off run on the demo laptop with `start_demo.bat` |
| R3-07 | Re-run every test case on the final build | M | Code | done | Every ported case re-run on `cp1-final`: `reports/final_cases_results.json` is stamped `cp1-final 18ba1d9`; no unexpected failure, every failure is linked to an open defect. Also pytest, the smoke test, the offline check, the UI checks and the end-to-end check (Phase 4.2) | None |
| R3-08 | Final metrics for each channel | K, V | Code | done | `reports/FINAL_NUMBERS.md` section 1: per channel the honest and the flattering measure with precision, recall, F1, false-positive rate, ROC-AUC and the confusion matrix (generated from `cp1-final` by `scripts/make_documents.py`; `tests/test_documents.py` checks it is current and carries no typed or retired number) | None |
| R3-09 | Correlation against the baselines | B, M | Code for the simulated half; the real half is blocked on R2-10 | partial | Simulated half done on the live models: `reports/comparison_metrics.json` and the R3-09 table in `reports/results.md` (single-channel, parallel multi-channel, whole bundle, the deployed 60-minute engine; titled simulated, with 95% intervals). The noisy-OR patent row is not evaluated (owner, 7 Nov 2026). The real half is blocked on R2-10 | Run `src/refit_fusion.py` on real bundles once R2-10 has them |
| R3-10 | Timing on the demo laptop | M | Code | partial | `scripts/benchmark.py` over real HTTP on this laptop: both targets met (`reports/benchmark.md`, with CPU, RAM and OS). This laptop is not confirmed as the demo laptop | Viraj confirms this is the demo laptop, or runs `python scripts/benchmark.py` on the demo laptop |
| R3-11 | The final test report | M | Code | done | `reports/FINAL_TEST_REPORT.md` (written by `scripts/make_final_test_report.py` from the run on `cp1-final`): why the suite was ported, every case with its porting and result, results by module, sample groups, exit criteria, defect log, what was not tested | None |
| R3-12 | One set of numbers everywhere | T | Code for FINAL_NUMBERS; restating it is People | partial | `reports/FINAL_NUMBERS.md` and `reports/final_numbers.json` (generated from `cp1-final` by `scripts/make_documents.py`; `tests/test_documents.py` checks it is current and carries no typed or retired number), with the retired numbers and a repository search for them | The team restates these numbers in the deck, the report, the patent and the paper, and nowhere else |
| R3-13 | Indian attack stories | B | Inputs: console presets | done | Four Indian stories in `src/demo_cases.py` (KYC freeze, courier customs fee, work-from-home task scam, legitimate order), served by `/presets` as one-click console presets, hand-written and run once. The legitimate order stays below the line (`reports/screenshots/demo_IN-04.png`) | Nothing for code |
| R3-14 | Results on real or lab-made bundles | M | Blocked on R2-10 | blocked | 0 real bundles. When they exist, `refit_fusion.py` writes `reports/real_bundles_report.md` and `reports/real_bundles_metrics.json` by default (checked by `tests/test_refit_path.py`) | Blocked on R2-10 |
| R3-15 | Who would use it | B | People | people | Not a code item | Bala writes it |
| R3-16 | Privacy and ethics | M | Inputs: PRIVACY.md | done | `docs/PRIVACY.md` (what is stored, hashed, logged and deleted, with tests), `PRIVACY_AND_ETHICS.md` (the private-mail pipeline), `DATA_SOURCES.md` (every dataset with its source, licence as checked and hash) | None |
| R3-17 | The limitations slide | M | Inputs: the measured list in FINAL_NUMBERS | partial | The measured list: `reports/FINAL_NUMBERS.md` section 8 and `docs/report/05_limitations.md` | Manoj puts it on the limitations slide |
| R3-18 | Each member's lessons learned | T | People | people | Not a code item | Each member writes theirs |
| R3-19 | The Capstone-2 plan | B | Inputs: CP2_BACKLOG | partial | `docs/CP2_BACKLOG.md` (what is not built, where it plugs in, the data it needs, how we would know it works) and `docs/report/06_future_work.md` | Bala presents the CP2 plan from it |
| R3-20 | The near-final project report | T | Inputs: `docs/report/` | partial | `docs/report/` chapters 1 to 6 as built (generated from `cp1-final` by `scripts/make_documents.py`; `tests/test_documents.py` checks it is current and carries no typed or retired number) | The team adds the department's formatting, front matter, literature survey and references |
| R3-21 | README and user manual | V | Code | done | `README.md` (install, run, routes, tests, retrain, documents, troubleshooting) and `docs/USER_MANUAL.md` (the console view by view, with screenshots from `scripts/ui_checks.py`). NFR-05 passes from the README alone (`reports/nfr05_fresh_clone.json`) | None |
| R3-22 | Plagiarism check on the report | M | People | people | Not a code item | Manoj runs it |
| R3-23 | The deck in the KLEF template | B | People; the figures come from you | people | `reports/figures/`: five figures as PNG at 300 dpi and SVG, readable in grayscale, with their data named in `reports/figures/README.md` | Bala builds the deck in the KLEF template with these figures |
| R3-24 | Practise the Q&A | T | Inputs: VIVA_BY_MODULE. The mock viva is People | partial | `docs/VIVA_BY_MODULE.md` (generated from `cp1-final` by `scripts/make_documents.py`; `tests/test_documents.py` checks it is current and carries no typed or retired number): per module and owner, how it works and five hard questions with answers citing files and numbers | The team holds a mock viva |
| R3-25 | Submit the abstract, slides, report and code 2 days early | B | People | people | Not a code item | Bala submits |
| R3-26 | Confirm the guide will attend | B | People | people | Not a code item | Bala confirms |
| R3-27 | All four present, in formal attire, with the signed diary | T | People | people | Not a code item | The team |
| PT-01 | Choose the filing route with KL IPFC | B | People | people | Not a code item | Bala |
| PT-02 | Confirm the applicant and the inventors | B | People | people | Not a code item | Bala |
| PT-03 | Match every measured number to the final run | B, M | Inputs: PATENT_NUMBERS | partial | `docs/PATENT_BASIS.md` section 3: every measured number with its source file (generated from `cp1-final` by `scripts/make_documents.py`; `tests/test_documents.py` checks it is current and carries no typed or retired number). The old spec is not used (owner, 7 Nov 2026) | Bala and KL IPFC write the patent from it |
| PT-04 | Know what is built and what is only described | T | Inputs: BUILT_VS_DESCRIBED | partial | `docs/PATENT_BASIS.md` sections 2 and 5: every built feature with its file, function and test, and what is not built (generated from `cp1-final` by `scripts/make_documents.py`; `tests/test_documents.py` checks it is current and carries no typed or retired number) | Bala and KL IPFC decide what to claim (section 6 lists the questions) |
| PT-05 | Go over prior art with KL IPFC | B | People | people | Not a code item | Bala |
| PT-06 | Check the fees | B | People | people | Not a code item | Bala |
| PT-07 | Finish the formatting | M | People | people | Not a code item | Manoj |
| PT-08 | Prepare the forms | B | People | people | Not a code item | Bala |
| PT-09 | File it and keep the proof | B | People | people | Not a code item | Bala |
| PT-10 | Keep everything private until it is filed | T | Rule 8, in force now | done | `git remote -v` is empty; `.gitignore` keeps `docs/inputs/`, data and keys out of git; nothing has been uploaded | Keep it this way until the filing receipt exists |
| MS-01 | Choose the journal with the guide | B | People | people | Not a code item | Bala and the guide |
| MS-02 | Move the draft into the journal's template | B | People | people | Not a code item | Bala |
| MS-03 | Rewrite the method and results from the final build | B, M | Inputs | partial | `docs/MANUSCRIPT_METHOD_RESULTS.md` (generated from `cp1-final` by `scripts/make_documents.py`; `tests/test_documents.py` checks it is current and carries no typed or retired number) | Bala edits the wording into the journal's template; the numbers stay as generated |
| MS-04 | Write related work and check every reference | K | People | people | Not a code item | Krishna |
| MS-05 | Redraw the figures for print | V | Inputs: `reports/figures/` | done | `reports/figures/` (PNG at 300 dpi and SVG, readable in grayscale), drawn by `scripts/make_figures.py` from the reports of `cp1-final` | None |
| MS-06 | Agree the author list | B | People | people | Not a code item | Bala and the team |
| MS-07 | Add the declarations the journal asks for | M | People | people | Not a code item | Manoj |
| MS-08 | Run a similarity check | M | People | people | Not a code item | Manoj |
| MS-09 | Write the cover letter | B | People | people | Not a code item | Bala |
| MS-10 | Submit after the patent is filed | B | People | people | Not a code item | Bala, after PT-09 |
| RD-01 | Check each drafted entry against what really happened | T | Inputs (dated facts) and People | partial | `docs/DIARY_ENTRIES.md` gives the dated facts from git and replaces the draft's sample text where it differs (see Found in Phase 5) | The team checks each drafted entry against it |
| RD-02 | Hand-copy the drafted pages | T | People | people | Not a code item | The team |
| RD-03 | Record the guide's feedback each week | B | People | people | Not a code item | Bala |
| RD-04 | Collect the signatures | B | People | people | Not a code item | Bala |
| RD-05 | Update the traceability matrix (p.14) | M | Inputs | partial | `docs/DIARY_ENTRIES.md`, page 14: rows O1 to O5 in the diary's columns, with build and test references and status | The team copies it by hand; the guide signs |
| RD-06 | Update the evidence pages (p.49, p.50, p.53, p.54) | M | Inputs | partial | `docs/DIARY_ENTRIES.md`, pages 49, 50, 53 and 54, and task 11 on page 45, in the diary's columns | The team copies it by hand; the guide signs the issue tracker |
| RD-07 | Write the weeks after Review-2 | T | Inputs (dated log) and People | partial | `docs/DIARY_ENTRIES.md`: a dated log of every commit, with dates from git only | The team writes the weekly entries from it |

## Found in Phase 4

1. **The final run was not adopted.** `run_all.sh` on `cp1-rc1` retrains every model. SMS and URL come out the same as v2. The email cleaner fix (D-11, D-15) shifts the email pool a little, and the correlation model retrained on it drops the hand-written TC-06 below the alert line. That fails adoption rule (c), so the owner kept v2's models (7 Nov 2026). The drop comes from the correlation model, not the detectors (`reports/final_run/README.md`).
2. **The correlation model is not stable on borderline bundles.** The simulated metrics barely move between the two models, but TC-06 does. `reports/results.md` now says so (limitation 8). Real bundles (R2-10) are what settles it.
3. **A run can pause when the laptop sleeps.** The first final run stood still for about 70 minutes while the machine slept; the cleaner itself takes under a minute on all emails. Keep the lid open, or set the lid to do nothing while plugged in, during long runs.
4. **Two encoding faults fixed in reporting code.** `make_report.py` wrote `results.md` in the Windows code page, and several scripts read JSON the same way. Both now use UTF-8. Training code was not touched.
5. **The private mail export is kept out of reports.** `scripts/compare_reports.py` used to list every file under `data/raw/`, which would have named the owner's export with its size and hash. It now skips `email_own/` and says so.

## Found in Phase 5

1. **The diary's filled draft describes a different build in its blue sample text.** It names six email corpora, about 77k emails, the UCI SMS set, XGBoost on 37k URL feature rows, a window sweep on scenarios, a deepfake stub, and sample unit-test results UT-01 to UT-20. None of that matches `cp1-final`. `docs/DIARY_ENTRIES.md` gives the real text for each column; the draft itself was not edited.
2. **The retired numbers do not appear as claims anywhere we wrote.** The repository search (`reports/FINAL_NUMBERS.md`, section 9) finds hits only where they are quoted as wrong, in files received with v2 or given as team input, or as other measured values with the same digits in code-written reports. To avoid confusion, `FINAL_NUMBERS.md` prints ROC-AUC to four decimals.
3. **Running pytest rewrites `reports/final_cases_results.json`.** `tests/test_final_cases.py` writes its results at the end of the module. `scripts/make_final_numbers.py` now restores every report file after its own pytest run, so the committed record of the run on `cp1-final` stays.
4. **The real-mail false-alarm rate is now in the final numbers.** The live email model flags a large share of the account owner's legitimate mail (the rate is in `reports/FINAL_NUMBERS.md`, limitation 2). It is the clearest sign that email needs better legitimate data before real use.

## Count by status

| Status | Items |
|---|---|
| done | 16 |
| partial | 20 |
| open | 0 |
| blocked | 3 |
| people | 30 |
| **total** | **69** |

## Resume here (end of Phase 6, 14 Nov 2026)

- **All six phases are done.** Build `cp1-final` (commit `18ba1d9`), v2's models. The owner's summary is `docs/PHASE6_SUMMARY.md`.
- **Documents:** rebuild them all with `.venv/Scripts/python.exe scripts/make_documents.py`. Edit prose in `docs/templates/`, never a generated file.
- **What is left:** people tasks and decisions only (`docs/PHASE6_SUMMARY.md`, sections 3 and 4), and real bundles (R2-10) for the correlation claim.
- **The consultancy app** is built in a separate folder (`../app`), from a pinned copy of `cp1-final`; this project is not changed by it.
