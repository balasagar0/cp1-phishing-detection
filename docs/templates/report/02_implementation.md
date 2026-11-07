# Chapter 2. Implementation, module by module

Everything is Python 3 with scikit-learn, FastAPI and SQLite, plus a React console. One command, `bash run_all.sh`, retrains every model and
rewrites `reports/`. The models shipped in `{{build.tag}}` are v2's; why a full retrain on this build was not adopted is in
`reports/final_run/README.md`.

## 2.1 Email detector (Krishna)

- **Data.** {{email.n}} emails from {{email.corpora}} (`src/train_email.py`, `load_email`). Split for the pooled figures: {{email.split.train}}
  train, {{email.split.val}} validation, {{email.split.test}} test.
- **Cleaning.** `clean_text` in `src/common.py` drops `<script>`, `<style>`, `<head>` and `<title>` blocks with their content, keeps the
  target of each link as a URL in the text, strips the remaining tags, decodes `=3A`-style escapes and normalises spacing. Numbers and years
  are replaced by `numtok` and `yeartok`.
- **Features.** Word 1-2-grams counted on training emails; a term is kept only if it appears in at least five emails of at least two corpora
  ({{email.kept_terms}} kept of {{email.candidate_terms}}); sublinear TF-IDF (`Feat`).
- **Model.** Logistic regression with balanced class weights; the regularisation strength C = {{email.chosen_C}} was chosen on validation.
- **Scoring.** `Detectors.score_email` in `src/predict.py` returns the score, the label and the terms that pushed the score up or down.

## 2.2 SMS detector (Krishna)

- **Data.** {{sms.n}} messages in three classes (`src/train_sms.py`).
- **Model.** Word and character TF-IDF with logistic regression over ham, spam and smishing; C = {{sms.chosen_C}}, chosen by cross-validation.
- **Alert score.** 1 - P(ham), so both spam and smishing raise it. `Detectors.score_sms` also returns the three class probabilities.

## 2.3 URL detector (Viraj)

- **Data.** {{url.n}} URLs on {{url.hosts}} hosts, split by host (`src/train_url.py`), plus {{url.constructed.train_login_urls}} constructed
  login URLs on popular domains for training.
- **Representation.** `canon` makes the URL canonical; character n-grams of the text are hashed; `rep_matrix` adds three flags for
  membership in the top-100, top-1,000 and top-10,000 domains of the OpenDNS popularity list, which is stored inside the model file. The registered domain comes from tldextract's
  bundled public-suffix snapshot, so no list is downloaded at runtime.
- **Model.** Logistic regression. No DNS, no fetch, no lookup.
- **Input checks.** `check_url` refuses strings that are not a URL or a bare domain, with a reason; the API answers HTTP 422.

## 2.4 Correlation engine (Bala)

- **Identity tokens.** `extract_ids` in `src/predict.py`: registered domains from URLs, links and email addresses; phone numbers found by
  phone-shape rules after links are cut out, skipping numbers next to reference words; the optional `identity` field.
- **Windows.** `time_windows` in `src/fusion.py`: each event starts a window that holds every later event within {{window.minutes}}
  minutes of it (`DEFAULT_WINDOW_MIN`, `{{window.file_line}}`). A window that sits inside a larger one is dropped, so windows may overlap.
  Only events in the same window are combined and linked.
- **Features.** `bundle_features`: {{corr.features}}.
- **Model.** A gradient-boosting classifier (`src/train_fusion.py`) trained on {{corr.n_train}} simulated bundles and tuned on
  {{corr.n_val}}. `Fusion` wraps it so that a one-event window returns the detector score (`SingleEventPassThrough`).
- **Bundle score.** `window_risks` scores every window; `windowed_risk` returns the highest and the window it came from.

## 2.5 Event store (Bala)

- `src/event_store.py`, class `EventStore`, on SQLite. `add(recipient, events)` stores the events with the recipient and tokens hashed by
  HMAC-SHA256 (`h`, `htok`), regroups the recipient's events into campaigns using the same windows, and raises an alert when a campaign first
  reaches the line, with its reason (which events, which shared token kinds).
- `ack` acknowledges an alert; `purge(older_than_days)` deletes old events, their alerts and empty campaigns.
- The key comes from `CP1_HMAC_KEY` or a key file generated once (`load_key`); the file is gitignored.

## 2.6 API (Viraj)

`api.py` (FastAPI). Routes: `GET /health`, `POST /score`, `POST /score/batch`, `POST /correlate`, `POST /events`, `GET /campaigns`,
`GET /campaigns/{id}`, `GET /alerts`, `POST /alerts/{id}/ack`, `POST /purge`, `GET /presets`. The built console is served at `/` and a one-file
console at `/lite`. `/docs` and `/redoc` are off because they load a CDN; `/openapi.json` stays. CORS names explicit origins, never `*`. A
missing model file makes only its channel unavailable (degraded mode).

## 2.7 Console (Viraj)

`console/phishing_correlation_console.jsx`, built with Vite into `console/dist`. Presets load the demo cases and the Indian stories (all
marked hand-written). The editor holds up to six events. **Analyze events** shows the single-channel view, the correlated view, a side-by-side
table and one card per event with its explanation. **Replay into event store** sends the events to `POST /events` and shows campaigns and
alerts. The console makes no request outside the machine.

## 2.8 Tooling (Manoj)

- `tests/`: pytest suites (window and identities, demo cases, defects, event store, console and API, refit path, the ported plan cases, the
  privacy pipeline, the documents).
- `scripts/`: preflight, offline check, UI checks with Playwright, end-to-end check, benchmark, fresh-clone check, final numbers, figures and
  documents.
- Git: module branches (`module/email-sms`, `module/url`, `module/correlation`, `module/api-console`, `module/testing-docs`) merged into
  `main`; tags per phase; no remote.
