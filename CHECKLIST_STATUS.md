# CP1 checklist status

All 69 items from section 9 of `CP1_FINISH_TASK.md`. Updated at the end of every phase. Nothing is marked done without evidence (a file, a test or a commit).

**Last update:** end of Phase 1 (test port, defect re-test, code fixes), 2 Nov 2026. Tag `test-run-20261102-1`.

**Status words:** done (finished, with evidence) · partial (some of it is done; the rest is named) · open (not started) · blocked (waiting on something named) · people (a person does it; tracked here).

**Owners:** B = Bala, V = Viraj, K = Krishna, M = Manoj, T = the team.

## Phase progress

| Phase | State | Evidence |
|---|---|---|
| 0. Baseline and audit | done | `reports/baseline_check.md`, `reports/model_manifest.json`, `tests/test_demo_cases.py`, tags `v2-baseline` and `test-run-20261102-0` |
| 1. Port the test suite, re-test defects, code fixes | done | `tests/test_final_cases.py` (112 cases), `reports/final_cases_results.json`, `reports/Test_Cases_and_Test_Data_FINAL.xlsx`, `reports/defect_log.md`, `tests/test_defects.py`; merges of `module/testing-docs`, `module/email-sms`, `module/url`, `module/correlation`, `module/api-console`; tag `test-run-20261102-1` |
| 2. Event store, live flow, console | open | Starts next |
| 3. Models | open | Needs Phase 1 measurements |
| 4. Freeze and final run | open | Needs Phases 1 to 3 |
| 5. Documents | open | Needs `cp1-final`. PT-03 and PT-04 also need the patent spec |
| 6. Wrap up | open | Last |

## Things found in Phase 0 that a person should know

1. **The patent spec is not in `docs/inputs/`.** `Patent_Complete_Specification_Form2` (.docx or .md) was not added. PT-03, PT-04 and the patent row of R3-09 (Phase 4.3) need it. A different file, `D:\Capstone_HTE Project\cla\Patent_Disclosure_Draft.docx`, exists; it was not used, because it is not the document the brief names. S should add the complete specification to `docs/inputs/`.
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

## All 69 items

| ID | Item | Owner | Who does it | Status | Evidence | Next step |
|---|---|---|---|---|---|---|
| R2-01 | URL false alarms on `https://` and a trailing slash (D-01) | V | Code | partial | D-01 Open (`reports/defect_log.md`): the scheme and trailing-slash flips are gone (URL-05, URL-06, URL-02, SYS-13 pass, because `canon()` normalises in training and serving); URL-07 fails on U-H06, a real Google sign-in URL with a long query | Phase 3.2: no retrain for the scheme (it no longer flips). Record U-H06 as the login-page trade-off; the team decides on D-01 |
| R2-02 | The SMS model catches smishing (D-09) | K | Code; may end as a proposed acceptance | partial | SMS-01 passes (every standard phishing SMS caught); SMS-03 fails on its legitimate half (bank alerts flagged, new defect D-16). `reports/defect_log.md` | Phase 3.3: retrain only with real SMS data whose licence can be checked; otherwise D-09 and D-16 stay open with a proposal |
| R2-03 | A fixed time window (D-04) | B | Code | partial | `src/fusion.py` line 13 `DEFAULT_WINDOW_MIN = 60.0` is the one place; the API and `refit_fusion.py` read it through `Fusion.window`. COR-12, SYS-09 and `tests/test_defects.py::test_D04_events_days_apart_are_not_combined` pass | Phase 2: the event store and console take the window from the same line |
| R2-04 | The console calls the API (D-06) | V | Code | partial | D-06 Closed: CORS names the console's dev origins, never '*' (`api.py`, API-12, `test_D06_cors_names_explicit_origins_never_star`). The console already calls `/correlate` | Phase 2.2: build the console and serve it from FastAPI |
| R2-05 | Event store, identity linking, composite score and alert | B | Code | open | Not built | Phase 2.1 |
| R2-06 | The API rejects bad input (D-02, D-07) | V | Code | done | D-02 and D-07 Closed: empty text, unknown channels and malformed URLs give HTTP 422 with a reason (`check_url`, commits 3ec9530, 658d63c); EML-07, SMS-07, URL-08, API-08 pass; `test_D02_*`, `test_D07_*` | Nothing for code. Re-run in Phase 4 |
| R2-07 | The remaining correlation defects (D-03, D-05, D-08) | B | Code | done | D-03, D-05, D-08 Closed, and D-13 (found on v2) Closed: calls and video are 'not assessed', nothing assessable is CANNOT_ASSESS (commit 3d42061); SCO-06, VV-03 to VV-05, COR-07, COR-09, COR-14, SYS-07, SYS-08, SYS-11, SYS-12 pass; `test_D03_*`, `test_D05_*`, `test_D08_*`, `test_D13_*` | Nothing for code. Re-run in Phase 4 |
| R2-08 | The email defects (D-10, D-11) | K | Code | partial | D-11 Closed (cleaner strips scripts and HTML, keeps link targets; commit b151be2; PRE-01). D-10 Open: EML-03 fails on E-H04. New D-17: EML-01 misses 4 of 11 standard phishing emails | Phase 3.1: add Nazario, SpamAssassin and Ling, retrain with the new cleaner, apply the adoption rule |
| R2-09 | Correlation changes a verdict with real scores (D-12, SYS-14) | B, M | Code | partial | TC-06 alerts only as a bundle (0.595) and its control TC-07 does not (0.451): `tests/test_demo_cases.py`. Hand-written, not a test set | Phase 2.5: the evidence table (S-03, TC-06, TC-07, TC-05, simulated weak campaigns) |
| R2-10 | Collect 40 + 40 real bundles (150 to refit) | T | People | people | `testcases/review2_testcase_workbook.xlsx` holds 0 real bundles. The path workbook -> `refit_fusion.py` -> `reports/real_bundles_report.md` works on the example rows (`tests/test_refit_path.py`; smoke test 24 checks pass with the data present) | The team collects 40 coordinated and 40 benign bundles (150 to refit). No bundle is ever generated |
| R2-11 | Meet the test plan's exit criteria | M | Code | partial | The 112 cases are ported and run (`reports/final_cases_results.json`): 84 Pass, 6 Fail, 1 Known limitation, 12 N/A, 9 Not run; every failure is linked to an open defect. The FINAL workbook is filled by `scripts/fill_final_workbook.py` | Phase 4.4: judge the 7 exit criteria on the frozen build |
| R2-12 | A private git repo with real history | M | Code | done | Local repo with real history: `v2-baseline` is v2 byte for byte; every commit uses the configured identity and the Claude co-author line; module branches merged into `main` with `--no-ff`; tags per phase; `git remote -v` is empty | Keep committing at each phase end; never push |
| R2-13 | Literature survey of at least 10 papers | T | People | people | Not a code item | The team writes it |
| R2-14 | SRS, ER and UML diagrams | M, B | Inputs: as-built diagrams | open | No as-built diagrams yet | Phase 5: Mermaid diagrams in `docs/diagrams/`. The guide signs off |
| R2-15 | Record the Review-2 feedback and the fixes | B | People | people | Not a code item | Bala records it |
| R3-01 | Agree the CP1 scope with the guide | B | People | people | Not a code item | Bala meets the guide; `docs/BUILT_VS_DESCRIBED.md` (Phase 5) supports it |
| R3-02 | Freeze one final build | M | Code | open | Not frozen | Phase 4: tags `cp1-rc1` and `cp1-final` |
| R3-03 | Run the whole flow live | V, B | Code | open | Only `/correlate` exists; no event store | Phase 2 and the end-to-end check in Phase 4.2 |
| R3-04 | The voice module, if it stays in CP1 | K | Code only if `VOICE_IN_CP1` is `yes` | people | `VOICE_IN_CP1` is `no`. Calls answer HTTP 501 on `/score` (`tests/test_demo_cases.py::test_tc03_voice_call_is_not_assessed`) | S and the team confirm voice scope. If it becomes `yes`, Appendix A |
| R3-05 | Script and rehearse the demo | V, B | Inputs; the rehearsal is People | open | No script yet | Phase 5: `docs/DEMO_SCRIPT.md`. Viraj and Bala rehearse |
| R3-06 | A review-proof demo laptop | V | Code, plus one real Wi-Fi-off run by a person | open | No preflight or offline check yet | Phases 2.3 and 5: `scripts/offline_check.py`, `scripts/preflight.py`, `start_demo.bat`. Viraj does one Wi-Fi-off run |
| R3-07 | Re-run every test case on the final build | M | Code | partial | Every ported case runs on this build (`tests/test_final_cases.py`, `reports/final_cases_results.json`) | Phase 4.2: re-run everything on `cp1-rc1` / `cp1-final` |
| R3-08 | Final metrics for each channel | K, V | Code | open | v2 figures reproduce (`reports/baseline_check.md`); final figures come from `cp1-final` | Phase 4.1 and `reports/FINAL_NUMBERS.md` |
| R3-09 | Correlation against the baselines | B, M | Code for the simulated half; the real half is blocked on R2-10 | partial | v2's window table on 12,000 simulated bundles (`reports/results.md`, `reports/window_metrics.json`) | Phase 4.3: add parallel multi-channel and the patent's noisy-OR row (needs the patent spec) |
| R3-10 | Timing on the demo laptop | M | Code | open | Not measured | Phase 4.2: `scripts/benchmark.py` |
| R3-11 | The final test report | M | Code | open | Not written | Phase 5: `reports/FINAL_TEST_REPORT.md` |
| R3-12 | One set of numbers everywhere | T | Code for FINAL_NUMBERS; restating it is People | open | Not written | Phase 5: `reports/FINAL_NUMBERS.md`. The team copies it into the deck, report, patent and paper |
| R3-13 | Indian attack stories | B | Inputs: console presets | open | The console has a KYC preset only | Phase 2.2: KYC freeze, courier customs fee, work-from-home task scam, a legitimate order |
| R3-14 | Results on real or lab-made bundles | M | Blocked on R2-10 | blocked | 0 real bundles. When they exist, `refit_fusion.py` writes `reports/real_bundles_report.md` and `reports/real_bundles_metrics.json` by default (checked by `tests/test_refit_path.py`) | Blocked on R2-10 |
| R3-15 | Who would use it | B | People | people | Not a code item | Bala writes it |
| R3-16 | Privacy and ethics | M | Inputs: PRIVACY.md | open | Not written | Phase 5: `docs/PRIVACY.md` |
| R3-17 | The limitations slide | M | Inputs: the measured list in FINAL_NUMBERS | open | v2's list is section 5 of `reports/results.md` | Phase 5 |
| R3-18 | Each member's lessons learned | T | People | people | Not a code item | Each member writes theirs |
| R3-19 | The Capstone-2 plan | B | Inputs: CP2_BACKLOG | open | Not written | Phase 5: `docs/CP2_BACKLOG.md` |
| R3-20 | The near-final project report | T | Inputs: `docs/report/` | open | Not written | Phase 5 |
| R3-21 | README and user manual | V | Code | open | v2's `README.md` exists; no manual | Phase 5; NFR-05 in Phase 4.4 |
| R3-22 | Plagiarism check on the report | M | People | people | Not a code item | Manoj runs it |
| R3-23 | The deck in the KLEF template | B | People; the figures come from you | people | No figures yet | Phase 5 makes `reports/figures/`; Bala builds the deck |
| R3-24 | Practise the Q&A | T | Inputs: VIVA_BY_MODULE. The mock viva is People | open | Not written | Phase 5: `docs/VIVA_BY_MODULE.md` |
| R3-25 | Submit the abstract, slides, report and code 2 days early | B | People | people | Not a code item | Bala submits |
| R3-26 | Confirm the guide will attend | B | People | people | Not a code item | Bala confirms |
| R3-27 | All four present, in formal attire, with the signed diary | T | People | people | Not a code item | The team |
| PT-01 | Choose the filing route with KL IPFC | B | People | people | Not a code item | Bala |
| PT-02 | Confirm the applicant and the inventors | B | People | people | Not a code item | Bala |
| PT-03 | Match every measured number to the final run | B, M | Inputs: PATENT_NUMBERS | blocked | The patent spec is not in `docs/inputs/` | S adds the spec; then Phase 5 writes `docs/PATENT_NUMBERS.md` |
| PT-04 | Know what is built and what is only described | T | Inputs: BUILT_VS_DESCRIBED | blocked | The patent spec is not in `docs/inputs/` | S adds the spec; then Phase 5 writes `docs/BUILT_VS_DESCRIBED.md` |
| PT-05 | Go over prior art with KL IPFC | B | People | people | Not a code item | Bala |
| PT-06 | Check the fees | B | People | people | Not a code item | Bala |
| PT-07 | Finish the formatting | M | People | people | Not a code item | Manoj |
| PT-08 | Prepare the forms | B | People | people | Not a code item | Bala |
| PT-09 | File it and keep the proof | B | People | people | Not a code item | Bala |
| PT-10 | Keep everything private until it is filed | T | Rule 8, in force now | done | `git remote -v` is empty; `.gitignore` keeps `docs/inputs/`, data and keys out of git; nothing has been uploaded | Keep it this way until the filing receipt exists |
| MS-01 | Choose the journal with the guide | B | People | people | Not a code item | Bala and the guide |
| MS-02 | Move the draft into the journal's template | B | People | people | Not a code item | Bala |
| MS-03 | Rewrite the method and results from the final build | B, M | Inputs | open | Not written | Phase 5: `docs/MANUSCRIPT_METHOD_RESULTS.md` |
| MS-04 | Write related work and check every reference | K | People | people | Not a code item | Krishna |
| MS-05 | Redraw the figures for print | V | Inputs: `reports/figures/` | open | No figures yet | Phase 5 |
| MS-06 | Agree the author list | B | People | people | Not a code item | Bala and the team |
| MS-07 | Add the declarations the journal asks for | M | People | people | Not a code item | Manoj |
| MS-08 | Run a similarity check | M | People | people | Not a code item | Manoj |
| MS-09 | Write the cover letter | B | People | people | Not a code item | Bala |
| MS-10 | Submit after the patent is filed | B | People | people | Not a code item | Bala, after PT-09 |
| RD-01 | Check each drafted entry against what really happened | T | Inputs (dated facts) and People | open | Git history starts 2 Nov 2026 | Phase 5: `docs/DIARY_ENTRIES.md` gives dated facts from git; the team checks each entry |
| RD-02 | Hand-copy the drafted pages | T | People | people | Not a code item | The team |
| RD-03 | Record the guide's feedback each week | B | People | people | Not a code item | Bala |
| RD-04 | Collect the signatures | B | People | people | Not a code item | Bala |
| RD-05 | Update the traceability matrix (p.14) | M | Inputs | open | Not written | Phase 5: `docs/DIARY_ENTRIES.md` |
| RD-06 | Update the evidence pages (p.49, p.50, p.53, p.54) | M | Inputs | open | Not written | Phase 5: `docs/DIARY_ENTRIES.md` |
| RD-07 | Write the weeks after Review-2 | T | Inputs (dated log) and People | open | Not written | Phase 5: a dated log from git in `docs/DIARY_ENTRIES.md` |

## Count by status

| Status | Items |
|---|---|
| done | 4 |
| partial | 9 |
| open | 23 |
| blocked | 3 |
| people | 30 |
| **total** | **69** |
