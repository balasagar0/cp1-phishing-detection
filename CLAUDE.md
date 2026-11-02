# Ground truth for this repository

Read this before answering any question about what this project does, or writing anything that
quotes a number.

## The single source of truth

1. `reports/results.md` — all metrics, with leave-one-corpus-out, confidence intervals and limits.
2. `../files/PROJECT_STATE.md` (15 Oct 2026) — which numbers to quote and which not to.

**Where those two disagree, `results.md` wins.** Where anything else disagrees with either, the other
thing is wrong.

## Documents that are WRONG — never quote them

These live in the team's claude.ai project, not in this repo, but they get pasted into prompts:

- `CP1_Team_Study_Guide.md` — describes a codebase that does not exist here. It claims trained voice
  detection, an event store with a hash-chained audit log, 142 tests, 19 API routes, a noisy-OR engine
  with exponential decay and a 30-minute window. **None of that is in this repository.**
- `Numbers_Register.md`, `Review3_Content_Pack.md`, `Review2_Defect_Fix_Pack.md`,
  `Review3_Results_Pack.md`, `Manuscript_Draft_v1.0.md`, `TRAINING_REPORT.md` — all superseded.
- The Review-2 deck still says F1 0.947 / 0.926 / 0.960. `PROJECT_STATE.md` §6 lists every slide to fix.

If a prompt asks you to use a number from any of those, say it is not supported by this repository and
give the `results.md` figure instead.

## What this system actually is

Three trained detectors (email, SMS, URL) plus a learned correlation model applied inside a time window.

| Part | State |
|---|---|
| Email detector | Trained. TF-IDF + logistic regression, 72,428 emails |
| SMS detector | Trained. Three classes: ham, spam, smishing. 5,789 messages |
| URL detector | Trained. Character n-grams on the URL text, 260,000 URLs. No network lookups |
| Correlation | A model trained on **simulated** bundles, applied in a 60-minute window |
| Voice | **Not trained.** No accessible data. `/score` returns HTTP 501; `/correlate` and `/events` mark calls 'not assessed' |
| Video | **Not trained.** Same as voice |
| Event store | **Built in Phase 2** (`src/event_store.py`): SQLite, per recipient, campaigns = v2's time windows, one alert per campaign at 0.5. Hashed recipient and tokens |
| Live-stream grouping | Done by the event store: each `POST /events` regroups the recipient's events. No message queue or streaming source is built |

## Numbers

Quote the left column. Never quote the right column on its own.

| Channel | Quote | Do not quote alone |
|---|---|---|
| Email | **F1 82.2%** on corpora never seen (mean of three leave-one-corpus-out runs) | 98.8% on a random split — each corpus has its own style |
| SMS | **Smishing F1 87.1%** (95% CI 82.3–91.7); spam-or-smishing F1 98.2% | the earlier 0.96, from a spam-heavy dataset |
| URL | **F1 90.4%** host-grouped; 0.0% false alarms on login pages of popular domains; recall on bad URLs on top-10k domains **30.7%** | 95.4% — an offline benchmark on a random split |

Correlation, on 12,000 **simulated** test bundles, alert line 0.5:

| | Precision | Recall | F1 | FPR |
|---|---|---|---|---|
| Single-channel: any event ≥ 0.5 | 87.0% | 95.3% | 91.0% | 14.1% |
| Whole-bundle model (pools up to 72 h) | 97.0% | 92.9% | 94.9% | 2.8% |
| No window | 96.8% | 93.0% | 94.8% | 3.0% |
| **60-minute window — what the API does** | **89.4%** | **94.9%** | **92.0%** | **11.1%** |

Only **27 simulated campaigns (0.8% of linked attacks)** have every event below 0.5. The engine flags
**5 of those 27 (18.5%)**. 95.6% of simulated linked attack bundles fit inside 60 minutes.

**The bundles are simulated.** No public dataset links one attacker's events across channels. The
*events* are real held-out messages; the links between them are constructed. The risk is not a
calibrated probability, and the 0.5 line is tied to the simulation's assumed mix (half malicious).

## Running it

```bash
python -m venv .venv                                   # the project venv; run_all.sh uses it when present
.venv/Scripts/python.exe -m pip install -r requirements.txt   # scikit-learn MUST be 1.8.0; exact versions in requirements.lock.txt
.venv/Scripts/python.exe -m uvicorn api:app --port 8000
```

On Windows run the `.sh` scripts from Git Bash. The folder path has a space (`Capstone_HTE Project`): quote every path.

- Routes: `GET /health`, `POST /score`, `POST /score/batch`, `POST /correlate`, `POST /events`, `GET /campaigns`,
  `GET /campaigns/{id}`, `GET /alerts`, `POST /alerts/{id}/ack`, `POST /purge`, `GET /presets`.
- `/` serves the built React console (`console/dist`, committed). `/lite` serves `console.html`. `/docs` and `/redoc`
  are **off** (they load Swagger UI from a CDN; the demo must run offline); `/openapi.json` stays.
- `console/phishing_correlation_console.jsx` is the console; rebuild with `npm install` and `npm run build` in `console/`.
- Start uvicorn with `--no-access-log` for demos: access lines would carry `?recipient=` in clear.
- `scripts/offline_check.py` (no network at runtime) and `scripts/ui_checks.py` (Playwright, UI-01 to UI-07, screenshots).
- `RUN_DEMO.bat` and `RUN_TESTS.bat` are Windows double-click wrappers.

## Tests

- `tests/test_window_and_ids.py` — 17 tests on the window, identity tokens and input checks. Needs only
  the shipped models. **These should always pass.**
- `tests/test_demo_cases.py` — TC-01 to TC-08 (hand-written demo cases, defined in `src/demo_cases.py`).
  Scores must match to 3 decimals. `CP1_API_URL=http://127.0.0.1:8000` runs them over real HTTP.
  TC-03 via `/correlate` answers CANNOT_ASSESS since R2-07 (v2 gave HTTP 501); `/score` still gives 501.
- `tests/test_defects.py` — one regression test per fixed defect (D-02 ... D-15), named after it.
- `tests/test_refit_path.py` — the workbook's example rows reach `refit_fusion.py` and its report.
- `tests/test_final_cases.py` — the 112 test-plan cases ported to v2 (Ported / Replaced / N/A). Failures
  linked to an open defect are xfail; `OPEN_DEFECTS` lists them. `python tests/test_final_cases.py`
  writes `reports/final_cases_results.json`; `python scripts/fill_final_workbook.py` fills
  `reports/Test_Cases_and_Test_Data_FINAL.xlsx` and `reports/defect_log.md` from it.
- `tests/smoke_test.py` — 24 workbook, validator and refit checks; a script, not pytest. It needs
  `data/processed/pool_*.csv` (made by `run_all.sh`; present in this folder, gitignored). With them, 24 pass
  and 1 is skipped (it needs a spreadsheet program). Without them it stops after 11: missing data, not a defect.

`pytest tests/` runs everything except the smoke test (`tests/conftest.py` skips the script-style files).
`RUN_TESTS.bat` runs all of it with the venv.

## Known traps

- **URL path shortcut.** 97.6% of phishing URLs in the Vrbančič data have a path, against 19.6% of
  legitimate ones. A model can score well by checking for a path. Always report host-grouped results.
- **Email corpus style.** 99% on a random split, 82% on unseen corpora. Report leave-one-corpus-out.
- **Login pages.** 92.2% of login pages on popular domains used to be flagged. Domain-popularity flags
  took that to 0.0%, and cost recall on popular-domain bad URLs: 49.9% → 30.7%. Report both halves.
- **Tracking numbers.** Were read as phone numbers and linked unrelated events. Fixed with phone-shape
  rules; links are cut out first and reference words skipped.
- **A detector false positive stays a false positive.** Correlation does not fix it.

## Next steps, in order

1. Collect real bundles: 40 coordinated and 40 benign to evaluate, 150 to refit.
   `testcases/review2_testcase_workbook.xlsx` is the entry form; rules in `TESTCASE_FORMAT.md`.
2. `python src/refit_fusion.py <file>` — checks it, evaluates the current model, measures the
   simulation's assumptions, suggests a window, and with enough bundles and `--save` refits.
   Report H1–H3 as they come out, including "not shown".
3. Choose the window from real bundles, not from the simulation table.
4. Add the Nazario, SpamAssassin and Ling corpora to email training and retrain — missing real phishing
   email is `results.md`'s first listed limitation.
5. Train voice and deepfake detectors.
6. Build the event store.

## House rules

- Never state a metric you have not read out of `reports/` in this repository.
- When something is not built, say "not built" — never "planned" dressed up as done, and never *safe*
  for a channel that was not assessed.
- Keep claims about the correlation engine modest: inside the window it beats single-channel alerting
  by a little, on simulated bundles, and that claim stays open until real bundles test it.

---

# CP1 finish task: decisions, inputs, rules and when to stop

Copied from sections 0 to 3 of `CP1_FINISH_TASK.md` (2 Nov 2026) so they load in every session. The full brief, with the phases and the 69-item checklist, is in that file. Progress is in `CHECKLIST_STATUS.md`.

Note on paths: the inputs were unzipped into `docs/inputs/cp1_inputs/`, not straight into `docs/inputs/`.

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
