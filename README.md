# CP1 - trained per-channel detectors (email, SMS, URL)

Real trained models, no hand-written scoring rules. Each detector returns `score` = probability the item is **not benign**,
plus the terms/n-grams that pushed the score (so the console can show *why*). Voice and video are not trained (no accessible data).

## Run it
```bash
pip install -r requirements.txt           # scikit-learn must be 1.8.0 (models are pickled with it)
uvicorn api:app --port 8000               # local demo API (CORS open - local use only)
python src/predict.py url "http://sbi-kyc-update.top/verify-now.php"     # CLI check
```
```js
// from the React console
const r = await fetch("http://localhost:8000/score", {method: "POST", headers: {"Content-Type": "application/json"},
  body: JSON.stringify({channel: "sms", text: "Dear customer your SBI account will be blocked..."})});
const {score, label, class_probabilities, top_terms_toward_smishing} = await r.json();
```
Endpoints: `GET /health`, `POST /score` (`channel`: email | sms | url; `subject` optional for email), `POST /score/batch`,
`POST /correlate` (a bundle of events -> per-event scores plus one bundle risk from the correlation model; optional `window_minutes`, see below). Voice/video return HTTP 501.
```bash
curl -s localhost:8000/correlate -H 'Content-Type: application/json' -d '{"events":[
  {"channel":"sms","text":"Your account will be blocked, update KYC at http://sbi-kyc-update.top/verify","identity":"+91 98765 43210","time":"0"},
  {"channel":"url","text":"http://sbi-kyc-update.top/verify","time":"4"}]}'
```
Events are linked by identity tokens (registered domains found in the text or URL, phone numbers, the optional `identity` field) and by `time` (minutes, or ISO timestamps).

## Time window, single events and identity tokens
- **Time window.** Events further apart than `window_minutes` are not combined or linked. The default is 60 minutes (`DEFAULT_WINDOW_MIN` in `src/fusion.py`); send `window_minutes` (above 0, up to 10080) to change it for one request. A refit on real bundles can store its own window (`refit_fusion.py ... --window N --save`) and the API then uses that.
- **How a bundle is scored.** The events are split into time windows (a window starts at one event and holds every event that follows within the window). Each window is scored on its own and the bundle takes the highest. Response fields: `window_minutes`, `n_windows`, `window_event_indices`, `window_time_span_minutes`, and `in_window` on each event. `bundle_risk_without_correlation` is all events pooled with no link or timing evidence.
- **A lone event is judged by its detector.** The correlation model was trained on simulated bundles with an assumed 50% attack rate, which made a lone event look worse than its detector says (a URL scoring 0.45 was rated 0.82). A window with one event now returns that event's own score. Windows with two or more events go to the model.
- **Why 60 minutes.** It is the deck's one-hour window, and about 95% of the simulated linked attack bundles fit in it (`results.md` has the exact figure). It is an assumption until real bundles replace it: `refit_fusion.py` suggests a value (90th percentile of the span of coordinated bundles, rounded up to 5 minutes) once there are 20 such bundles.
- **What the window costs on the simulation.** The window table in `results.md` shows that, on the simulated bundles, the engine scores lower with a window than when it pools every event of a bundle. The simulation's unlinked bundles hold events up to 72 hours apart and are labelled as a whole, so pooling them helps there; the window stops it. The simulation cannot settle the window, so do not choose it from that table. Quote the row that matches the setting you demo.
- **Phone numbers.** A number counts as a phone number only in a phone shape: a leading `+` with 10-15 digits, 10 digits, 11 digits starting with 0, or 12 digits starting with 91 and a mobile digit. Links are cut out first, and a number right after words like order, tracking, ref or account is skipped unless the words before it say call or phone. Tracking, order and account numbers and dates are not identities.
- **Limits.** `/correlate` scores a bundle you give it. It does not group a live stream of events and has no event store. A popular domain shared by two unrelated messages (wikipedia.org, gmail.com) still counts as shared identity; the model learned from simulated benign linked bundles that this is weak evidence, but check it on real benign linked bundles.

## React console
`console/phishing_correlation_console.jsx` calls `/correlate`; it has no scoring logic of its own.
```bash
npm create vite@latest console-app -- --template react && cd console-app && npm install
cp ../console/phishing_correlation_console.jsx src/App.jsx      # delete the App.css / index.css imports Vite adds
npm run dev                                                       # backend must be running on :8000
```

## Review-2 test cases
`testcases/review2_testcase_workbook.xlsx` is the data-entry workbook for real multi-channel bundles; the rules are in `TESTCASE_FORMAT.md`.
`python src/refit_fusion.py <file>` checks the file, tests the current correlation model on it, measures the simulation's assumptions, suggests a time window
and, with enough bundles and `--save`, refits the model (the API then serves `models/fusion_model_real.joblib`).

## Layout
| Path | What |
|---|---|
| `src/train_email.py` | final email model (numbers masked, vocabulary limited to terms seen in >=2 corpora) |
| `src/train_email_plain.py` | baseline email model, kept for the comparison in the report |
| `src/train_sms.py`, `src/train_url.py` | SMS (3-class) and URL (string model + feature benchmark) |
| `src/url_features.py` | URL canonicalisation, domain-popularity flags, constructed test URLs |
| `src/fusion.py`, `src/train_fusion.py` | correlation model, time windows, single-event rule and the simulated-bundle training |
| `src/eval_window.py` | evaluates the window and the single-event rule on the same simulated test bundles (`reports/window_metrics.json`) |
| `src/probes.py` | hand-written probe inputs (not an evaluation) |
| `src/predict.py`, `api.py` | inference wrapper and FastAPI app |
| `console/` | React console |
| `src/testcases.py`, `src/refit_fusion.py`, `src/make_testcase_workbook.py` | Review-2 file reader/validator, real-bundle evaluation and refit, workbook builder |
| `testcases/`, `tests/` | workbook + example rows; `smoke_test.py` (synthetic rows, all marked `example`) and `test_window_and_ids.py` (window, identity tokens, input checks) |
| `models/` | trained `.joblib` files (`url_features_*` are offline benchmarks, not used by the API) |
| `reports/results.md` | **all metrics, with leave-one-corpus-out, confidence intervals and known limitations** |
| `reports/*_metrics*.json`, `log_*.txt` | raw metrics and training logs |

## Tests
```bash
python tests/test_window_and_ids.py   # window, single-event rule, identity tokens, input checks; needs only the shipped models
python tests/smoke_test.py            # workbook loader, validator, refit script; needs the data from run_all.sh (pools) for its synthetic bundles
```

## Retrain from scratch
```bash
bash download_data.sh     # public GitHub sources only (raw data is not in this zip)
bash run_all.sh           # ~15 min on one CPU core; rewrites models/ and reports/ (including reports/window_metrics.json)
```
Nazario (real phishing emails), SpamAssassin and Ling are not in this run. They are on GitHub as well (`rokibulroni/Phishing-Email-Dataset`: `Nazario.csv`, `SpamAssasin.csv`, `Ling.csv`; reachable when this version was prepared).
To add them, put the CSVs in `data/raw/`, extend `load_email()` in `src/train_email.py`, and run `run_all.sh` again. Check each licence first.

## Data sources (check each licence before redistributing the data)
CEAS_08 (PHP4Life/Phishing-Email-Dataset), Enron-Spam (MWiechmann/enron_spam_data), fraud email corpus (smurlafries1/MachineLearningPhishingDetection),
LSDST smishing corpus (hcphap/Smishing-Dataset) and a second SMS collection (shaghayegh-hp/Smishing_Dataset) used only as an external check,
URL strings (faizann24/Using-machine-learning-to-detect-malicious-URLs), URL features (GregaVrbancic/Phishing-Dataset),
domain popularity list (opendns/public-domain-lists, top 10,000).
