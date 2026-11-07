# Chapter 3. Testing and validation

The full record is `reports/FINAL_TEST_REPORT.md`. This chapter summarises it for build `{{build.tag}}`.

## 3.1 Strategy

- **Unit and module tests** for each part: identity tokens and windows, the defects fixed, the event store, the console routes, the refit path
  and the private-mail privacy pipeline (`tests/`).
- **The test plan's {{tests.cases.total}} cases**, ported to this build in `tests/test_final_cases.py`. The plan was written on 29 Sep for an
  older codebase with 0-100 scores and verdict bands, so each case is marked Ported ({{tests.cases.tag.ported}}), Replaced
  ({{tests.cases.tag.replaced}}: same intent, this build's alert line) or N/A ({{tests.cases.tag.na}}: the feature does not exist). IDs are
  kept and no expectation was weakened.
- **Hand-written demo cases** TC-01 to TC-08, checked to three decimals (`tests/test_demo_cases.py`). They are demos, not a test set.
- **System checks** over real HTTP: an end-to-end run, the console in Chrome and Edge, an offline run with every socket blocked, a latency
  benchmark, and a fresh clone set up from the README alone.
- **Model evaluation** on held-out data with the honest splits described in chapter 4.

## 3.2 Results on the final build

| Check | Result |
|---|---|
| pytest | {{tests.pytest.passed}} passed, {{tests.pytest.xfailed}} expected failures (open defects), {{tests.pytest.skipped}} skipped, {{tests.pytest.failed}} failed |
| Smoke test | {{tests.smoke.passed}} passed, {{tests.smoke.skipped}} skipped |
| Ported plan cases | {{tests.cases.pass}} pass, {{tests.cases.fail}} fail on open defects, {{tests.cases.known_limitation}} known limitation, {{tests.cases.na}} N/A |
| End-to-end check | {{tests.e2e.passed}} of {{tests.e2e.steps}} steps pass |
| Console checks in Chrome and Edge | {{tests.ui.passed}} of {{tests.ui.n}} pass; failing: {{tests.ui.failed}} (defect D-18) |
| Offline run | {{tests.offline}} |
| Fresh clone from the README (NFR-05) | {{tests.nfr05}} |
| Latency, full case, slowest | {{latency.case.max}} against a target of 5 seconds |

## 3.3 Exit criteria

Judged against the targets the plan wrote; no target was moved after a result.

{{block:exit}}

## 3.4 Defects

{{defects.open}} open and {{defects.closed}} closed. Open: {{defects.open_list}}. A defect is closed only when every case linked to it passes;
accepting an open defect is the team's decision, and written proposals are in `reports/defect_log.md`.

## 3.5 Not tested

Voice and video (not built); real coordinated bundles (none collected); the demo laptop itself; a run with the network physically off; other
browsers and Linux; concurrent load; penetration testing. Reasons are in `reports/FINAL_TEST_REPORT.md`, section 8.
