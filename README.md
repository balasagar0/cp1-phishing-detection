# AI-Based Multi-Channel Phishing Detection System (CP1 prototype)

Team Y23-HTE-PROJECT-88, B.Tech CSE, KL University. Build: tag `cp1-final`, commit `18ba1d9`. Every number for this build is in `reports/FINAL_NUMBERS.md`; the checks run on it are listed in `CHECKLIST_STATUS.md`.

Three trained detectors (email, SMS, URL), a correlation model that combines events inside a 60-minute window, an event store that groups a
recipient's events into campaigns and raises alerts, and a console. Every score comes from a trained model; there are no hand-written scoring rules.

**Not built:** voice and video detectors (calls and video are shown as "not assessed", never as safe). The correlation model was trained on
**simulated** bundles, because no public dataset links one attacker's email, SMS and URL events; its risk is not a calibrated probability.
All measured numbers are in `reports/FINAL_NUMBERS.md` and `reports/results.md`; this README quotes none.

## Install (once, needs the internet)

Python 3.10 or later (tested with 3.13). On Windows use Command Prompt, PowerShell or Git Bash in the project folder. The folder path may contain
spaces: keep it in quotes.

Windows:

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pytest tests -q
```

Linux or macOS:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest tests -q
```

scikit-learn must be exactly the version in `requirements.txt` (the models were saved with it). `requirements.lock.txt` lists every package
version the build was tested with. The trained models ship in `models/`; no data download is needed to run the demo or the tests.

## Run the demo (no internet needed)

Windows: double-click **`start_demo.bat`**. It runs `scripts/preflight.py`, which checks Python, the packages, the model files (against
`reports/model_manifest.json`) and the built console, starts the API on port 8000, runs TC-01 to TC-08, checks that nothing needs the network,
prints **GO** or **NO-GO**, and on GO opens the console at http://127.0.0.1:8000/.

Linux or macOS:

```bash
.venv/bin/python scripts/preflight.py --keep-running --open
```

Or start the API by hand and open http://127.0.0.1:8000/ in a browser:

```bash
.venv/Scripts/python.exe -m uvicorn api:app --port 8000 --no-access-log     # Windows (Linux: .venv/bin/python)
```

The console: pick a preset (TC-01 to TC-08, or one of the four Indian stories), press **Analyze events**, and read the side-by-side table (each
event's score, whether it alerts on its own, the bundle risk). **Replay into event store** sends the same events to the event store and shows the
campaign, its alert and the timeline. `docs/USER_MANUAL.md` walks through every view with screenshots; `docs/DEMO_SCRIPT.md` is the review script.
A one-file console is also served at http://127.0.0.1:8000/lite.

## API

| Route | What it does |
|---|---|
| `GET /health` | channels loaded, window minutes, what the correlation model was trained on; `status` is `degraded` if a model file is missing |
| `POST /score` | one message: `{"channel": "email"\|"sms"\|"url", "text": "...", "subject": "..."}`. Calls and video answer HTTP 501 (not built) |
| `POST /score/batch` | `{"items": [ ... ]}` |
| `POST /correlate` | a bundle: `{"events": [{"channel", "text", "subject", "identity", "time"}], "window_minutes": 60}`; returns per-event scores, the bundle risk, the windows and shared identity tokens. Nothing assessable gives `status: CANNOT_ASSESS` |
| `POST /events` | the event store: `{"recipient": "...", "events": [ ... ]}`; stores them, regroups the recipient's campaigns, raises alerts |
| `GET /campaigns`, `GET /campaigns/{id}` | campaigns (optionally `?recipient=`), and one campaign with its timeline |
| `GET /alerts`, `POST /alerts/{id}/ack` | open alerts, and acknowledging one |
| `POST /purge` | retention: `{"older_than_days": 30}` |
| `GET /presets` | the console presets (hand-written, not a test set) |

Example (Git Bash or Linux):

```bash
curl -s localhost:8000/correlate -H 'Content-Type: application/json' -d '{"events":[
  {"channel":"sms","text":"Your account will be blocked, update KYC at http://sbi-kyc-update.top/verify","identity":"+91 98765 43210","time":"0"},
  {"channel":"url","text":"http://sbi-kyc-update.top/verify","time":"4"}]}'
```

`/docs` and `/redoc` are switched off because their pages load files from the internet; the schema is at `/openapi.json`.
Bad input gets HTTP 422 with a reason (empty text, unknown channel, malformed URL, unreadable time). Privacy: `docs/PRIVACY.md`.

## Tests

```bash
.venv/Scripts/python.exe -m pytest tests -q          # everything except the smoke test (Linux: .venv/bin/python)
.venv/Scripts/python.exe tests/test_final_cases.py   # the 112 ported test-plan cases; writes reports/final_cases_results.json
.venv/Scripts/python.exe scripts/fill_final_workbook.py   # fills reports/Test_Cases_and_Test_Data_FINAL.xlsx (needs docs/inputs/)
.venv/Scripts/python.exe tests/smoke_test.py         # workbook, validator and refit checks; its second half needs data/processed (run_all.sh)
```

Failures of the ported cases that are linked to an open defect are reported as expected failures; `reports/defect_log.md` lists every defect.
`RUN_TESTS.bat` runs all of them on Windows. Checks with their own scripts: `scripts/offline_check.py` (no network at runtime),
`scripts/ui_checks.py` (console checks UI-01 to UI-07 with Playwright; `pip install -r requirements-dev.txt`), `scripts/benchmark.py` (latency).

## Retrain from scratch (needs the internet; about 20 minutes)

```bash
bash download_data.sh     # public datasets; see DATA_SOURCES.md for sources, licences and hashes
bash run_all.sh           # retrains every model and rewrites reports/ (uses .venv when present)
```

On Windows run these in Git Bash. `run_all.sh` stops at the first failed step. After a retrain, run the tests, `scripts/make_model_manifest.py`
and `scripts/preflight.py`.

On `cp1-final` a retrain gives models close to, but not the same as, the shipped ones: the email text cleaner was fixed after v2, and the
retrained correlation model changes one demo outcome. The shipped models are v2's, and `reports/` describes them. Do not commit `run_all.sh`
output over them; `reports/final_run/README.md` records what a retrain gives and why it was not adopted.

## Documents

Every document with a number is generated from the reports of `cp1-final`, never typed:

| File | What |
|---|---|
| `reports/FINAL_NUMBERS.md` | the one set of numbers: per detector (honest and flattering), correlation (simulated), demo cases, tests, latency, defects, limits, retired numbers |
| `reports/FINAL_TEST_REPORT.md` | why the test plan was ported, every case with its result, sample groups, exit criteria, defect log, what was not tested |
| `reports/figures/` | figures for the paper, poster and deck (PNG at 300 dpi and SVG); its README names each figure's data |
| `docs/DEMO_SCRIPT.md` | the demo order, what to say, expected values and fallbacks |
| `docs/PATENT_BASIS.md` | what is built (code and tests), every measured number with its source, and what is not built |
| `docs/MANUSCRIPT_METHOD_RESULTS.md`, `docs/report/` | text for the paper and the project report |
| `docs/VIVA_BY_MODULE.md`, `docs/DIARY_ENTRIES.md` | viva preparation per member; text to copy into the research diary |

Rebuild them all with `.venv/Scripts/python.exe scripts/make_documents.py` (needs `pip install -r requirements-docs.txt` for the figures). The
prose lives in `docs/templates/`; edit a template, never a generated file. `tests/test_documents.py` fails if a document is stale or carries a
typed or retired number.

## Troubleshooting

| Problem | What to do |
|---|---|
| `start_demo.bat` says the venv is missing | Run the Install commands once (they need the internet). |
| NO-GO: port 8000 is taken | Close the other program, or `.venv\Scripts\python.exe scripts\preflight.py --port 8001 --keep-running --open`. |
| NO-GO: model files do not match | The models were changed or damaged. Restore them with `git checkout -- models` (or retrain and refresh the manifest). |
| The API will not start, or warns about scikit-learn versions | Reinstall with `pip install -r requirements.txt` in the venv; scikit-learn must match exactly. |
| Blank page at http://127.0.0.1:8000/ | Hard-refresh the browser (Ctrl+F5). If it persists, open http://127.0.0.1:8000/lite, or rebuild the console: `npm install` and `npm run build` in `console/` (needs Node.js and the internet). |
| "Cannot reach the API" in the console | The API stopped. Start it again, then press Retry or Analyze. |
| `/health` says `degraded` | One model file is missing; that channel is "not assessed" until it is restored. |
| `console.html` opened as a file cannot reach the API | Expected: open http://127.0.0.1:8000/lite instead. |

## Layout

| Path | What |
|---|---|
| `api.py` | FastAPI app: scoring, correlation, event store routes, console |
| `src/predict.py`, `src/fusion.py`, `src/event_store.py` | detectors and identity tokens; correlation model and time windows; event store |
| `src/train_*.py`, `src/eval_*.py`, `src/make_report.py` | training and evaluation (run by `run_all.sh`) |
| `src/demo_cases.py` | TC-01 to TC-08 and the Indian stories (hand-written, not a test set) |
| `console/` | the React console (`console/dist` is the built copy the API serves) |
| `tests/` | all tests; `tests/data/workbook_cases.json` is copied from the team workbook |
| `scripts/` | preflight, offline check, UI checks, benchmark, workbook filler, report and document generators |
| `reports/` | every metric and run record, written by code; start with `FINAL_NUMBERS.md` |
| `docs/` | user manual, demo script, privacy, diagrams, report chapters and the other documents |
| `testcases/`, `TESTCASE_FORMAT.md` | the real-bundle workbook (R2-10) and its rules; `src/refit_fusion.py` evaluates and refits on it |
