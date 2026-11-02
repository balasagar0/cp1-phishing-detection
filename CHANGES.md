# Changes in this version (v2)

The trained models are unchanged. What changed is the correlation step around them, the identity tokens, the tests and the documents.

| Change | Where |
|---|---|
| Configurable time window (default 60 min; `window_minutes` per request; a refit can store its own). Events further apart are not combined or linked. | `src/fusion.py`, `api.py`, `src/refit_fusion.py` |
| A window with one event is judged by its detector, not by the correlation model (the simulation's 50% attack rate had inflated lone events). | `src/fusion.py` (`SingleEventPassThrough`) |
| The span feature is capped at the largest span the model saw in training (72 h). | `src/fusion.py` |
| Phone numbers: only phone shapes count; links are cut out first; order, tracking and account numbers and dates are skipped. A 12-digit FedEx number no longer links two events. | `src/predict.py` |
| `/correlate` returns `window_minutes`, `n_windows`, `window_event_indices`, `window_time_span_minutes` and `in_window` per event. A bad `time` gives HTTP 422 (it was a 500). `/health` reports the default window. | `api.py` |
| `refit_fusion.py` evaluates with the same window (`--window N`, `--no-window`) and stores it with `--save`. | `src/refit_fusion.py` |
| New evaluation of the window on the simulated test bundles; its table is added to `reports/results.md`. | `src/eval_window.py`, `src/make_report.py`, `run_all.sh` |
| Console: window box, a "days apart" preset, events outside the window greyed out. | `console/phishing_correlation_console.jsx` |
| New tests (17); the smoke test no longer needs a Claude-only recalculation script and checks the window options. `openpyxl` and `httpx` added to `requirements.txt`. | `tests/`, `requirements.txt` |
| Documents updated: README, TESTCASE_FORMAT.md, results.md (limitations 1 and 5). | root, `reports/` |

## Read this before quoting numbers

The correlation rows at the top of `reports/results.md` (F1 94.9%, false-positive rate 2.8%) describe the model scoring a **whole bundle**, including events up to 72 hours apart. The deployed engine uses a 60-minute window, so quote the **window table** below them. On the simulated bundles the windowed engine scores lower than the whole-bundle model and only a little above single-channel alerting; the reason is in the README, section "Time window, single events and identity tokens".
