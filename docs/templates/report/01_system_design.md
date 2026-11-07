# Chapter 1. System design

## 1.1 Purpose and scope

The system looks for coordinated phishing: one attacker reaching one person over several channels within a short time, for example an SMS,
then a link, then an email. It scores each message on its own and then asks whether a recipient's recent messages form a campaign.

In scope for CP1: detectors for email, SMS and URL; identity linking; a time window; a learned correlation score; an event store with
campaigns and alerts; an HTTP API; a browser console. Out of scope for CP1, and shown as "not assessed": voice calls and video.

## 1.2 Architecture

![Components](../diagrams/components.svg)

The components and their files:

| Component | Role | Files |
|---|---|---|
| Detectors | Score one email, SMS or URL from its text alone | `src/predict.py` (`Detectors`), models in `models/` |
| Identity extraction | Take domains, phone numbers and an optional identity from each event | `src/predict.py` (`extract_ids`) |
| Correlation engine | Group events into windows, compute window features, score each window, take the highest | `src/fusion.py` |
| Event store | Keep each recipient's events hashed, form campaigns, raise alerts | `src/event_store.py`, SQLite file `data/events.db` |
| API | Routes for scoring, correlation, events, campaigns, alerts, purge and presets | `api.py` (FastAPI) |
| Console | Presets, an event editor, the single-channel and correlated views, replay into the event store | `console/` (React, built into `console/dist`) |
| Training | Train each detector and the correlation model, write the reports | `src/train_*.py`, `run_all.sh` |
| Refit | Evaluate and refit the correlation model on real bundles | `src/refit_fusion.py` |

## 1.3 Data flow

**Scoring one bundle (`POST /correlate`).** The request holds a list of events. Each scorable event is scored by its detector and its
identity tokens are extracted. Events are grouped into windows: each event starts a window that holds the events within {{window.minutes}} minutes after it, and
a window inside a larger one is dropped. Each window is described by
{{corr.n_features}} features and scored by the correlation model, which was trained on simulated bundles of real messages; a window with a
single event keeps its detector score. The answer holds every
event's score, the bundle risk (the highest window), the window it came from, the shared tokens, and whether any single event alerts alone.

![The /correlate sequence](../diagrams/correlate_sequence.svg)

**The live path (`POST /events`).** The same scoring, then the event store hashes the recipient and the tokens, stores the events, regroups all
of that recipient's events into campaigns (one per window), and raises an alert the first time a campaign reaches the alert line.

![The /events sequence](../diagrams/events_sequence.svg)

## 1.4 Data model

![Event store tables](../diagrams/event_store_er.svg)

The event store has events, campaigns and alerts. A campaign belongs to one recipient and is keyed by its first event. Recipients and identity
tokens are stored as HMAC-SHA256 hashes. Message text is not stored unless `CP1_STORE_CONTENT=1` is set.

## 1.5 Design decisions

| Decision | Why | Where |
|---|---|---|
| Score each channel separately, then correlate | Each channel has its own public data; the correlation model needs only scores, tokens and times | `src/fusion.py` |
| A fixed time window of {{window.minutes}} minutes | Messages days apart are rarely one campaign; the value was fixed before the evaluation ran | `{{window.file_line}}` |
| A lone event keeps its detector score | A model trained on bundles should not change the verdict on a single message | `SingleEventPassThrough` in `src/fusion.py` |
| The bundle takes its highest window | A campaign anywhere in the recipient's history should raise the alarm | `window_risks`, `windowed_risk` |
| Not assessed is never safe | A missing detector must not look like a clean result | `NOT_ASSESSED` in `src/predict.py`, `_assess` in `api.py` |
| No network at runtime | The demo must run offline, and a URL is never fetched | `scripts/offline_check.py` |
| Hash identities with a key | Linking needs equal tokens, not readable ones | `EventStore.h`, `EventStore.htok` |
| One alert per campaign | Repeated alerts for one campaign would be noise | `EventStore.add` |

## 1.6 Requirements traced to the build

| Requirement area | Built as | Evidence |
|---|---|---|
| Score email, SMS and URL | Three trained detectors | `reports/FINAL_NUMBERS.md`, section 1 |
| Link events by identity and time | Identity tokens and the time window | `tests/test_window_and_ids.py` |
| Composite risk and alert | Learned window score; one alert per campaign | `tests/test_event_store.py`, `tests/test_demo_cases.py` |
| Keep events per person, privately | Event store with HMAC hashes and purge | `docs/PRIVACY.md` |
| Show it to a user | Console and API | `reports/ui_checks.json`, `reports/e2e_check.md` |
| Voice and video | Not built; "not assessed" | `tests/test_demo_cases.py::test_tc03_voice_call_is_not_assessed` |
