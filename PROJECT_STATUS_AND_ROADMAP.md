# Project status and roadmap

AI-Based Multi-Channel Phishing Detection System, team Y23-HTE-PROJECT-88. Written 7 Nov 2026.

This file has three parts:

1. **Done**: what the first work session (2 Nov 2026) finished, with the file that proves each piece.
2. **Next session**: the steps that finish Capstone-1 (CP1), in order.
3. **From prototype to a real-time app**: what it takes before the system can be used live for consultancy clients.

Numbers are never typed here. Every figure lives in `reports/`; this file says where.

---

## Part 1. Done (session of 2 Nov 2026)

The work follows `CP1_FINISH_TASK.md`. Item-by-item status for all 69 checklist items is in `CHECKLIST_STATUS.md`.

### Where the code is

| What | Where |
|---|---|
| Finished, tested and merged work | branch `main` (Phases 0 to 2) |
| Phase 3 work in progress | branch `module/email-sms` (not merged yet) |
| Tags | `v2-baseline` (v2 exactly as received), `test-run-20261102-0`, `-1`, `-2` (end of Phases 0, 1, 2) |
| Git remote | none, on purpose (patent privacy, rule 8) |

### Phase 0: baseline and audit (done)

- Git repository created. The first commit is v2 byte for byte (`v2-baseline`).
- Project venv, `requirements.lock.txt`, `reports/model_manifest.json` (SHA-256 of every model), secret scan (`scripts/secret_scan.py`).
- The eight demo cases TC-01 to TC-08 are now tests (`tests/test_demo_cases.py`). They reproduced to 3 decimals.
- A fresh download and retrain reproduced every Review-3 figure. Every data source still downloads (`reports/baseline_check.md`).

### Phase 1: test suite, defects, code fixes (done)

- All 112 test-plan cases ported to v2, one test each, tagged Ported, Replaced or N/A (`tests/test_final_cases.py`).
- Code fixes, each with a regression test (`tests/test_defects.py`):
  - bad input is refused with HTTP 422 and a reason (empty text, unknown channel, malformed URL, bad time);
  - a bundle with nothing to assess answers `CANNOT_ASSESS`, never a low score;
  - calls and video are "not assessed" and no longer block a bundle;
  - CORS names explicit origins, never `*`;
  - one missing model file degrades one channel instead of stopping the API;
  - the email cleaner strips scripts and HTML and keeps link targets.
- The filled workbook `reports/Test_Cases_and_Test_Data_FINAL.xlsx` and `reports/defect_log.md`.
- Defects: 11 closed, 7 open (D-01, D-09, D-10, D-12, D-16, D-17, D-18).

### Phase 2: event store, console, checks (done)

- **Event store** (`src/event_store.py`): SQLite, one store per recipient, campaigns built with v2's own window code, one alert per campaign. Recipients and identity tokens are stored as HMAC-SHA256; message text only on request. Routes `/events`, `/campaigns`, `/alerts`, `/purge`. Its answer equals `/correlate` on TC-04, TC-06 and TC-07 (`tests/test_event_store.py`).
- **Console** built with Vite and served by the API at `/`. Presets for TC-01 to TC-08 and four Indian stories. Side-by-side view and "replay into event store".
- **No network at runtime**: `scripts/offline_check.py` passes (`reports/offline_check.md`).
- **Console checks UI-01 to UI-07** in Chrome and Edge with Playwright: 6 pass. UI-03 fails on D-18 (`reports/ui_checks.json`, screenshots in `reports/screenshots/`).
- **R2-09 evidence table**: `reports/r2_09_evidence.md`.

### Phase 3: models (partly done)

- **Email (3.1): two attempts, both failed the adoption rule.** The Nazario, SpamAssassin and Ling corpora were downloaded from their original sources (`download_email_extra.sh`, licences in `DATA_SOURCES.md`). Attempt 1 added them. Attempt 2 kept that and also raised the alert line, with the rule fixed before it ran. Both lift the honest email measure well beyond v2's interval and catch more standard phishing. Both still fail the rule:
  - (b) a legitimate payment receipt (E-L08) becomes a false alarm;
  - (c) TC-07 starts alerting, because its parcel email alone now crosses the line.

  So v2's email model stays live, and the brief leaves the next step to the team. Results: `reports/candidates/email_candidates.md` and `email_candidates_attempt2.md`.
- **URL (3.2) done.** The scheme and the trailing slash no longer change any label, so no retrain is needed (`reports/candidates/url_d01.md`).
- **SMS (3.3) done.** No new SMS data with a checkable licence exists, so D-09 and D-16 stay open (`reports/candidates/sms_d09.md`). v2's SMS training data was traced to its source and licence (CC BY 4.0).

### Written ahead for later phases (code ready, not yet run on the final build)

`scripts/benchmark.py`, `scripts/preflight.py`, `start_demo.bat`, `scripts/nfr05_fresh_clone.py`, `src/eval_comparison.py`, `src/campaign_formula.py` (patent formula; its worked-example test waits for the spec), `README.md`, `docs/USER_MANUAL.md`, `docs/PRIVACY.md`, `docs/CP2_BACKLOG.md`, `DATA_SOURCES.md`, and the diagrams in `docs/diagrams/` (all four rendered to SVG and PNG).

---

## Part 2. Next session: finish CP1

### Before the session (team)

1. Put the patent specification (`Patent_Complete_Specification_Form2`, .docx or .md) in `docs/inputs/cp1_inputs/`. It unblocks PT-03, PT-04 and the patent row of the R3-09 comparison.
2. Decide on the email model after two failed attempts: keep v2's email model (both attempts recorded as negative results), or adopt attempt 2 with written reasons. Adopting it means overriding the adoption rule on (b) and (c), and TC-07 would no longer show 'no alert'.
3. Optional: put `Test_Plan_Phishing_Detection.docx` and `SRS_Phishing_Detection_v1.0.md` in the same folder, so `docs/BUILT_VS_DESCRIBED.md` can cover the SRS too.

### Start the session

Open Claude Code in the project folder and send:

> Read CP1_FINISH_TASK.md, CHECKLIST_STATUS.md and PROJECT_STATUS_AND_ROADMAP.md, run git log --oneline -30, and continue from the first unfinished step.

### Steps, in order

| # | Step | Brief section | Result |
|---|---|---|---|
| 1 | Commit the email candidate report, keep `models/candidates/` out of git, and merge `module/email-sms` into `main` | 3.1 | Phase 3 work on `main` |
| 2 | Read the patent spec. Fill the channel weights and the cross-channel and sequence factors into `src/campaign_formula.py` from the spec, and write the section 16 worked-example test | 4.3 | `tests/test_campaign_formula.py` passes in full |
| 3 | Point `scripts/compare_reports.py` and `src/make_report.py` at the honest email figure over the three original corpora, so they still work if more corpora are added | 3.1, 5 | correct headline figure in every report |
| 4 | Apply the team's email decision. If attempt 2 is adopted: make `train_email.py` reproduce it (extra corpora and the alert-line rule), refresh `reports/model_manifest.json`, update `tests/test_demo_cases.py` with the reason, and run every test (rule d) | 3.1 | the email model on `main` |
| 5 | Add `eval_comparison.py` to `run_all.sh`. Tag `cp1-rc1`. Run `download_data.sh` and `run_all.sh` on it. Commit the regenerated models and reports as "final run" | 4.1 | final models and reports |
| 6 | If the final run moved any demo-case score, update `tests/test_demo_cases.py` with the new values and the reason. Alert outcomes must not change | 4.1 | TC-01 to TC-08 pass |
| 7 | Run everything on the final build: all tests, the ported suite, the offline check, the UI checks, an end-to-end check, and `scripts/benchmark.py` over real HTTP | 4.2 | `reports/benchmark.md`, fresh `reports/ui_checks.json` |
| 8 | The R3-09 comparison, titled "simulated", including the patent row | 4.3 | `reports/comparison_metrics.json` |
| 9 | NFR-05 (`scripts/nfr05_fresh_clone.py`) and NFR-07 (regression against the earlier run). Fill the FINAL workbook. Judge the 7 exit criteria against the plan's own targets | 4.4 | exit criteria table |
| 10 | Tag `cp1-final`. Write the tag and commit into the workbook, `FINAL_NUMBERS.md` and `README.md` | 4.5 | the build every number comes from |
| 11 | Phase 5 documents, all generated from `cp1-final`: `FINAL_NUMBERS.md`, `FINAL_TEST_REPORT.md`, figures, `DEMO_SCRIPT.md`, `BUILT_VS_DESCRIBED.md`, `PATENT_NUMBERS.md`, `MANUSCRIPT_METHOD_RESULTS.md`, `DIARY_ENTRIES.md`, `docs/report/`, `VIVA_BY_MODULE.md`, plus a search for the retired numbers | 5 | the documents |
| 12 | Finish `CHECKLIST_STATUS.md` and send the Phase 6 summary | 6 | the hand-over message |

### Decisions the team owns

- Whether to accept the proposed defects in writing: D-09, D-12 and D-18 have written proposals. D-01, D-10, D-16 and D-17 stay open until a model change fixes them.
- Voice scope for CP1 (`VOICE_IN_CP1` is `no`).
- The patent: rewrite it around this build, or build what it claims. Phase 5 produces `BUILT_VS_DESCRIBED.md` and `PATENT_NUMBERS.md` to support that choice.

### Work only people can do

These are listed with their owners in `CHECKLIST_STATUS.md`:

- collect real bundles (R2-10);
- run the demo once with Wi-Fi off on the demo laptop (R3-06);
- rehearse the demo and the viva;
- the literature survey;
- the report, plagiarism check and diary signatures;
- the patent filing steps with KL IPFC;
- the journal steps.

---

## Part 3. From prototype to a real-time app for consultancy clients

### Where the prototype stands today

It runs on one laptop. A person pastes or replays messages; the API scores them and groups a recipient's events into campaigns. It is honest about its limits, and those limits matter for real use:

- The correlation model was trained on **simulated** bundles. Its risk is not a calibrated probability. No real multi-channel campaign has tested it yet.
- Every model was measured on public datasets, not on a client's traffic. A client's mail and SMS will look different (see the leave-one-corpus-out results in `reports/results.md`).
- Known misses and false alarms are open: missed standard phishing emails (D-17), flagged bank alerts (D-16), and login pages of small sites (D-01).
- Voice and video are not built.
- There is no login, no tenant separation, no live message source, and no deployment package.

Nothing below should be promised to a client until the "proof it works" for that stage is in hand.

### What has to be built, by area

Size: S is a few days, M is one to three weeks, L is more than three weeks, for one developer.

| Area | What exists now | What a live service needs | Size | Proof it works |
|---|---|---|---|---|
| **Real evaluation data** | 0 real bundles; public corpora only | Real bundles (R2-10), then a pilot dataset from each client, collected with consent | L (people) | H1 to H3 from `src/refit_fusion.py` on real bundles, reported as they come out |
| **Model quality** | Open defects D-01, D-09, D-10, D-16, D-17 | Retrain with real phishing email and real legitimate transactional SMS. Choose the alert line per client on that client's validation data | L | The workbook groups pass their targets; per-client precision and false-alarm rate on held-out client data |
| **Calibrated risk** | Uncalibrated score, 0.5 line tied to the simulation's mix | A calibration step fitted on real bundles, with the risk shown as a band | M | A reliability curve on held-out real bundles |
| **Live message sources** | Messages are pasted, or replayed into `/events` | Connectors that call `/events` as messages arrive: email (Microsoft Graph or Gmail API push, or IMAP), SMS (an Android reader app or an SMS gateway export, keeping India's DLT sender headers), URLs (a browser extension or the mail connector's links) | L | Events arrive and campaigns form with no one pressing Replay; time from arrival to alert is measured |
| **Background processing** | Every request is scored while it waits | A queue (Redis or RabbitMQ) and worker processes, so a burst of mail does not slow the API | M | Load test: a burst of messages is processed without timeouts or lost events |
| **Database** | SQLite file on one machine | PostgreSQL with backups, migrations (Alembic), and one database or schema per client | M | Restore from backup drill; migration tests |
| **Client separation** | One store; recipients hashed with one key | Separate data and a separate HMAC key per client, held in a secrets manager or KMS, never in a file | M | A test that no query crosses clients; key rotation drill |
| **Sign-in and roles** | None | Login (OAuth2 or SSO), roles (analyst, admin, read-only), API keys for connectors, rate limits | M | Security tests: no route answers without a valid token and role |
| **Alert workflow** | Alerts listed and acknowledged | Triage states (new, investigating, confirmed, false alarm), notes, assignment, notifications (email, Teams or Slack, webhook), and a log of analyst actions | M | An analyst can take an alert from new to closed; every action is logged |
| **Learning from feedback** | None | Analyst verdicts saved as labels, with consent, for scheduled retraining under the same adoption rule | M | Each retrain is compared with the live model before it replaces it |
| **Monitoring** | `/health` only | Metrics without message content (requests, latency, alerts per day, score drift per channel), dashboards, alerts to the operator | M | Drift and outages are noticed by monitoring before a client reports them |
| **Packaging and deployment** | `start_demo.bat`, local venv | Docker images, a compose file for single-server installs, HTTPS through a reverse proxy, environment-based configuration | M | A fresh server reaches a working install from the deployment guide alone |
| **Quality gate** | Tests run by hand | CI on every commit: all tests, secret scan, dependency scan, offline check, build | S | No change reaches a client without a green pipeline |
| **Security review** | Input checks, no secrets in the repo | A threat model, dependency and container scanning, a penetration test before the first client | M | Findings fixed or accepted in writing |
| **Privacy and compliance** | Hashing, no text stored by default, a manual purge, `docs/PRIVACY.md` | Compliance with India's Digital Personal Data Protection Act, 2023: notice and consent where needed, purpose limits, a scheduled retention purge, data-principal requests, breach procedure. A data processing agreement with every client | M (with legal advice) | A privacy review signed off by the institution's adviser or the client's DPO |
| **Data licences** | Several training datasets have no stated licence (`DATA_SOURCES.md`) | Confirm terms, or replace those datasets, before any commercial use of the trained models | S to M | Every dataset behind a shipped model has a recorded licence that allows the use |
| **Voice and video** | Not built | Only with a public benchmark and a measured error rate on unseen attacks (`docs/CP2_BACKLOG.md`, items 6 and 7) | L | Equal error rate on the official evaluation split, shown beside the bundle risk |
| **Client documentation** | README, user manual, privacy note | An installation and operations guide, an analyst guide, an onboarding checklist, and a one-page "what it does and does not do" for clients | S | A new client team installs and uses it from the documents |

### Suggested milestones

| Milestone | Contents | Ready when |
|---|---|---|
| **M1. CP1 final** | Part 2 of this file | Tag `cp1-final`, all documents generated from it |
| **M2. Pilot-ready, one client** | Real bundles collected and evaluated; one live source (email first); PostgreSQL; sign-in; Docker; CI; a scheduled purge | One consenting organisation runs it on its own mail for a pilot period, and its false-alarm rate and misses are measured and reported |
| **M3. Consultancy beta** | Client separation with per-client keys; alert workflow; monitoring; security review; DPDP compliance work; a data processing agreement template; licence clean-up | Two or more clients run it at once, with no data crossing between them |
| **M4. Wider coverage** | SMS source, URL source, calibrated risk, retraining from feedback, then voice and video if the data allows | Each new channel has its own measured, held-out result before it is switched on |

### Order of risk

1. **Patent first.** Nothing is published or shown to a client before the patent is filed (rule 8, PT-10).
2. **Real data before claims.** The simulated correlation results must not be sold as field performance.
3. **Privacy before scale.** Client separation, key handling and the retention purge come before a second client.
4. **Licences before money.** Training data with unknown terms must be cleared or replaced before commercial use.
