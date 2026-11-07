# Final test report (CP1)

Written by `scripts/make_final_test_report.py` from the run of 2026-11-07 17:11 on **`cp1-final`** (commit `18ba1d9`), Python 3.13.0, Windows-11-10.0.26200-SP0. Every count below comes from `reports/final_cases_results.json` and the other files named; nothing is typed.

## 1. Why the suite was ported

The test plan (v1.1, 29 Sep) and its 112 cases were written for an older codebase: `/analyze` routes, scores from 0 to 100, a rule bonus capped at 25, and verdicts SAFE, SUSPICIOUS and HIGH RISK. The codebase changed after 29 Sep. This build has per-channel detectors that give a score from 0 to 1, a learned correlation model applied in time windows, and an alert line of 0.5. So each case was ported, not run as written, and kept its ID:

- **Ported:** the same check against this build.
- **Replaced:** the same intent with this build's expectation. HIGH RISK became an alert (risk at or above the alert line), SAFE became no alert, Rejected became HTTP 4xx.
- **N/A:** the feature does not exist in this build (the rule bonus, the risk threshold of 20, the 30/60 verdict bands, the voice module). The reason is given per case.

No expectation was weakened so a case would pass. Where the build behaves wrongly, the case fails and is linked to a defect.

## 2. Summary

112 cases: 92 Pass, 7 Fail, 1 Known limitation, 12 N/A. Porting: 12 N/A, 44 Ported, 56 Replaced. Every failure is linked to an open defect; there is no unexpected failure.

Other checks on the same build (from `reports/final_numbers.json`):

- pytest: 180 passed, 7 expected failures (open defects), 1 skipped, 0 failed.
- Smoke test: 24 passed, 1 skipped (it needs a spreadsheet program).
- End-to-end check over real HTTP: 10 of 10 steps pass (`reports/e2e_check.md`).
- Console UI checks in Chrome and Edge: 6 of 7 pass; failing: UI-03 (`reports/ui_checks.json`).
- Offline check (no network at runtime): pass (`reports/offline_check.md`).
- NFR-05, a fresh clone run from the README alone: Pass (`reports/nfr05_fresh_clone.json`).
- Latency over real HTTP: median 23 ms (email), 12 ms (SMS), 6 ms (URL); slowest full case 1970 ms (`reports/benchmark.md`).

## 3. Results by module

| Module | Cases | Pass | Fail | Known limitation | N/A | Not run |
|---|---|---|---|---|---|---|
| Console (UI) | 7 | 6 | 1 | 0 | 0 | 0 |
| Correlation engine | 17 | 12 | 0 | 0 | 5 | 0 |
| Email classifier | 10 | 7 | 2 | 1 | 0 | 0 |
| End-to-end cases | 14 | 13 | 1 | 0 | 0 | 0 |
| Non-functional | 7 | 7 | 0 | 0 | 0 | 0 |
| Preprocessing | 7 | 6 | 0 | 0 | 1 | 0 |
| SMS classifier | 8 | 7 | 1 | 0 | 0 | 0 |
| Scoring and verdict | 8 | 6 | 1 | 0 | 1 | 0 |
| Service (API) | 13 | 13 | 0 | 0 | 0 | 0 |
| URL classifier | 11 | 10 | 1 | 0 | 0 | 0 |
| Voice/Video module | 10 | 5 | 0 | 0 | 5 | 0 |

## 4. Every case: porting and result

| ID | Module | Priority | Porting | Why (Replaced or N/A) | Result | Defect |
|---|---|---|---|---|---|---|
| API-01 | Service (API) | High | Replaced | v2's /health lists the trained channels and the untrained ones instead of a readiness map. | Pass | none |
| API-02 | Service (API) | High | Replaced | v2 has no /analyze/email; POST /score with channel=email. v2 returns score (0-1), label (malicious/benign) and the terms that moved the score instead of confidence and top_signals. | Pass | none |
| SCO-01 | Scoring and verdict | High | Replaced | v2 has no SAFE / SUSPICIOUS / HIGH RISK bands (0-30-60-100). Its one line is 0.5. Same intent: the boundary is placed exactly; 0.5 alerts, just below does not, for a channel score and for the bundle label. | Pass | none |
| SYS-01 | End-to-end cases | High | Replaced | HIGH RISK -> alert (bundle risk >= 0.5), SAFE -> no alert. v2's evidence for a shared link is a shared identity token. | Pass | none |
| PRE-01 | Preprocessing | Medium | Ported | same check | Pass | D-11 |
| PRE-02 | Preprocessing | High | N/A | v2 does not replace URLs and e-mail addresses with placeholder tokens. The email model reads the words of the URL, and the correlation step extracts registered domains as identity tokens (tested by COR-02, COR-03 and tests/test_window_and_ids.py). | N/A | none |
| PRE-03 | Preprocessing | Medium | Ported | same check | Pass | D-15 |
| PRE-04 | Preprocessing | Medium | Ported | same check | Pass | none |
| PRE-05 | Preprocessing | High | Replaced | v2 has no 30-feature URL extractor. Its URL representation is the canonical URL's character 3-5-gram hashing (2^20 slots) plus 3 domain-popularity flags. Same intent: the vector for U-P01 is complete and identical on repeat, and the IP host carries no popularity flag. | Pass | none |
| PRE-06 | Preprocessing | Medium | Replaced | Same intent as PRE-05 for odd input: v2's URL representation is built for every input without an exception. (At the API, malformed URLs are refused instead: URL-08.) | Pass | none |
| PRE-07 | Preprocessing | Low | Ported | same check | Pass | none |
| EML-01 | Email classifier | High | Ported | same check | Fail | D-17 |
| EML-02 | Email classifier | High | Ported | same check | Pass | D-10 |
| EML-03 | Email classifier | Medium | Ported | same check | Fail | D-10, D-17 |
| EML-04 | Email classifier | Medium | Replaced | v2 returns a probability from 0 to 1 and a label (malicious or benign) plus the terms that moved the score; it has no separate 'confidence' field. Same intent: the score is a valid probability, the label matches the 0.5 line and E-P01 scores higher than E-L01. | Pass | none |
| EML-05 | Email classifier | Medium | Ported | same check | Pass | none |
| EML-06 | Email classifier | Medium | Ported | same check | Pass | none |
| EML-07 | Email classifier | Medium | Replaced | v2 has no /analyze/email; the same request goes to POST /score with channel=email. Rejected = HTTP 4xx. | Pass | D-02 |
| EML-08 | Email classifier | Medium | Ported | same check | Pass | none |
| EML-09 | Email classifier | High | Ported | same check | Known limitation | none |
| EML-10 | Email classifier | High | Ported | same check | Pass | none |
| SMS-01 | SMS classifier | High | Ported | same check | Pass | D-09 |
| SMS-02 | SMS classifier | High | Ported | same check | Pass | none |
| SMS-03 | SMS classifier | Medium | Ported | same check | Fail | D-09, D-16 |
| SMS-04 | SMS classifier | High | Ported | same check | Pass | none |
| SMS-05 | SMS classifier | Medium | Ported | same check | Pass | none |
| SMS-06 | SMS classifier | Medium | Ported | same check | Pass | none |
| SMS-07 | SMS classifier | Medium | Replaced | v2 has no /analyze/sms; the same request goes to POST /score with channel=sms. Rejected = HTTP 4xx. | Pass | D-02 |
| SMS-08 | SMS classifier | High | Replaced | v2's SMS model has three classes. The plan's 'spam class' (unwanted vs ham) is v2's spam-or-smishing vs ham on its 20% test split. The honest SMS metric, smishing vs rest, is reported beside it. | Pass | none |
| URL-01 | URL classifier | High | Ported | same check | Pass | none |
| URL-02 | URL classifier | High | Ported | same check | Pass | D-01 |
| URL-03 | URL classifier | Medium | Ported | same check | Pass | D-01 |
| URL-04 | URL classifier | High | Ported | same check | Pass | none |
| URL-05 | URL classifier | High | Ported | same check | Pass | D-01 |
| URL-06 | URL classifier | Medium | Ported | same check | Pass | D-01 |
| URL-07 | URL classifier | Medium | Ported | same check | Fail | D-01 |
| URL-08 | URL classifier | Medium | Replaced | v2 has no /analyze/url; the same request goes to POST /score with channel=url. Rejected = HTTP 4xx. | Pass | D-02 |
| URL-09 | URL classifier | Medium | Ported | same check | Pass | none |
| URL-10 | URL classifier | High | Ported | same check | Pass | none |
| URL-11 | URL classifier | Low | Ported | same check | Pass | none |
| VV-01 | Voice/Video module | High | Replaced | v2 has no stub class. Same intent: the service says video and voice are not available. /health lists them as not trained and /score answers HTTP 501 for them. | Pass | none |
| VV-02 | Voice/Video module | Medium | Replaced | Same intent as VV-01 with odd input: every call for the video channel gets a clean answer (501 not available, or 422 for a missing text), never a 500. | Pass | none |
| VV-03 | Voice/Video module | High | Replaced | v2 has no /analyze. The S-07 case goes to POST /correlate with a channel='video' event. Expected: the email is scored and the video comes back 'not assessed'. | Pass | D-13 |
| VV-04 | Voice/Video module | High | Replaced | v2 has no evidence list. Same intent: a video event never adds risk. It is kept out of the correlation features, the shared tokens and the window. | Pass | D-13 |
| VV-05 | Voice/Video module | High | Replaced | v2 has no verdicts. 'Not SAFE (for example cannot assess)' becomes: the response says CANNOT_ASSESS (or rejects the request with HTTP 4xx) and gives no risk score. | Pass | D-03 |
| VV-06 | Voice/Video module | Low | N/A | No voice or video detector exists in v2 or in CP1 (VOICE_IN_CP1 = no; video is Capstone-2), and there is no media-file input. Calls and video are 'not assessed'. Not built. | N/A | none |
| VV-07 | Voice/Video module | Low | N/A | No voice or video detector exists in v2 or in CP1 (VOICE_IN_CP1 = no; video is Capstone-2), and there is no media-file input. Calls and video are 'not assessed'. Not built. | N/A | none |
| VV-08 | Voice/Video module | Low | N/A | No voice or video detector exists in v2 or in CP1 (VOICE_IN_CP1 = no; video is Capstone-2), and there is no media-file input. Calls and video are 'not assessed'. Not built. | N/A | none |
| VV-09 | Voice/Video module | Low | N/A | No voice or video detector exists in v2 or in CP1 (VOICE_IN_CP1 = no; video is Capstone-2), and there is no media-file input. Calls and video are 'not assessed'. Not built. | N/A | none |
| VV-10 | Voice/Video module | Low | N/A | No voice or video detector exists in v2 or in CP1 (VOICE_IN_CP1 = no; video is Capstone-2), and there is no media-file input. Calls and video are 'not assessed'. Not built. | N/A | none |
| COR-01 | Correlation engine | High | Replaced | v2 has no evidence strings or bonus. Same intent: the shared link is found as a shared identity token and the link features are on. Uses fixed detector scores through v2's correlation engine (Fusion.risk), as the plan does. | Pass | none |
| COR-02 | Correlation engine | High | Replaced | Same intent as COR-01: the flagged URL inside the email gives the email the URL's domain token, shared with the URL event. Uses fixed detector scores through v2's correlation engine (Fusion.risk), as the plan does. | Pass | none |
| COR-03 | Correlation engine | High | Replaced | Same intent as COR-02 for the SMS. Uses fixed detector scores through v2's correlation engine (Fusion.risk), as the plan does. | Pass | none |
| COR-04 | Correlation engine | High | Replaced | v2 reports a shared link as a fact whatever the scores, and the learned model decides its weight; there is no bonus. Same intent: three legitimate channels sharing a link and a brand raise no alert (bundle risk below 0.5). Uses fixed detector scores through v2's correlation engine (Fusion.risk), as the plan does. | Pass | none |
| COR-05 | Correlation engine | Medium | N/A | v2 has no rule that link evidence needs a risky URL channel. Shared links are identity tokens and the learned model weighs them with the scores. | N/A | none |
| COR-06 | Correlation engine | Medium | N/A | v2 has no rule that identity evidence needs both email and SMS to be risky. Brand names are not identity tokens in v2 (only domains, phone numbers and the identity field). | N/A | none |
| COR-07 | Correlation engine | Medium | Ported | same check | Pass | none |
| COR-08 | Correlation engine | High | N/A | v2 has no bonus and so no MAX_BONUS cap. The bundle risk is a probability from the learned model, between 0 and 1 by construction. | N/A | none |
| COR-09 | Correlation engine | Medium | Replaced | Same intent as VV-04 at the API: a video event never contributes to the bundle risk. | Pass | D-13 |
| COR-10 | Correlation engine | High | Replaced | v2 has one alert line (0.5), so S-03's fixed scores 0.55 / 0.52 / 0.58 each alert on their own and the SUSPICIOUS band does not exist. Same intent where it can be kept: the bundle alerts and its risk is at least the best single score. The lift from below the line is SYS-14 / TC-06. Uses fixed detector scores through v2's correlation engine (Fusion.risk), as the plan does. | Pass | none |
| COR-11 | Correlation engine | Medium | N/A | v2 has no time-evidence rule that needs email, SMS and URL timestamps. The time span of a window is a model feature for any two or more events. | N/A | none |
| COR-12 | Correlation engine | High | Replaced | v2 has no evidence strings. Same intent: events 3 and 6 days apart fall in separate 60-minute windows, are not linked, and the bundle risk is the strongest single event. Uses fixed detector scores through v2's correlation engine (Fusion.risk), as the plan does. | Pass | none |
| COR-13 | Correlation engine | Medium | Replaced | v2 has no evidence text. Same intent: the window's time span is the real span (90 s = 1.5 minutes). | Pass | none |
| COR-14 | Correlation engine | High | Replaced | Same intent: the shared link on a .online host is found as a shared identity token (full public suffix list). Uses fixed detector scores through v2's correlation engine (Fusion.risk), as the plan does. | Pass | none |
| COR-15 | Correlation engine | Medium | Ported | same check | Pass | none |
| COR-16 | Correlation engine | Low | N/A | v2 has no risk threshold of 20 and no separate phishing label for evidence. Its one line is 0.5. | N/A | none |
| COR-17 | Correlation engine | Medium | Replaced | v2 has no bonus. Same intent: missing content does not crash the service; it is rejected with HTTP 4xx (no 500). | Pass | none |
| SCO-02 | Scoring and verdict | High | Replaced | v2's bundle risk is a learned model, not min(100, best + bonus), so the formula part is N/A. The second part is kept: the bundle risk is never below the best channel score, for S-01, S-02 and S-05. | Pass | none |
| SCO-03 | Scoring and verdict | Medium | N/A | v2 returns no correlation_delta field (no bonus). It returns bundle_risk and, for comparison, bundle_risk_without_correlation. | N/A | none |
| SCO-04 | Scoring and verdict | Medium | Replaced | v2 scores are probabilities from 0 to 1 (the plan's 0-100 scale divided by 100). | Pass | none |
| SCO-05 | Scoring and verdict | Medium | Replaced | v2 has no /analyze. Same intent through /correlate: a URL-only case returns one URL event and no other channel. | Pass | none |
| SCO-06 | Scoring and verdict | High | Replaced | v2 has no analyze({}). The empty case goes to POST /correlate. Expected: rejected with HTTP 4xx or CANNOT_ASSESS, never a low risk. | Pass | D-03 |
| SCO-07 | Scoring and verdict | Medium | Ported | same check | Pass | none |
| SCO-08 | Scoring and verdict | High | Replaced | Same intent through /correlate: with S-06, the bundle risk is at least the email score. | Fail | D-18 |
| API-03 | Service (API) | Medium | Replaced | POST /score with channel=sms instead of /analyze/sms. | Pass | none |
| API-04 | Service (API) | Medium | Replaced | POST /score with channel=url instead of /analyze/url. | Pass | none |
| API-05 | Service (API) | High | Replaced | POST /correlate instead of /analyze. It returns per-event scores, bundle_risk, bundle_label, shared identity tokens and the window instead of combined_score, verdict and correlation_delta. | Pass | none |
| API-06 | Service (API) | Medium | Ported | same check | Pass | none |
| API-07 | Service (API) | Medium | Ported | same check | Pass | none |
| API-08 | Service (API) | Low | Replaced | v2 takes one 'time' per event (minutes or ISO). The S-01 case goes to /correlate with times 'a', 'b', 'c'. | Pass | none |
| API-09 | Service (API) | High | Replaced | v2 has no per-channel readiness map. Same intent: with the SMS model file missing, the service still starts, SMS is 'not assessed', and email and URL are still scored. | Pass | D-14 |
| API-10 | Service (API) | Medium | Ported | same check | Pass | none |
| API-11 | Service (API) | High | Replaced | Same intent: hostile strings are data, every answer is JSON and nothing runs. Email and SMS answer 200. For URL, a string that is not a URL may be refused with 422 instead, because URL-08 requires invalid URLs to be rejected; a 500 or a non-JSON answer fails. | Pass | none |
| API-12 | Service (API) | High | Replaced | Stricter than the plan, as CP1_FINISH_TASK.md R2-04 asks: CORS with explicit origins, never '*'. The console's dev origin (localhost:5173) gets the header and the preflight succeeds; an unknown origin gets no header. | Pass | D-06 |
| API-13 | Service (API) | Low | Ported | same check | Pass | none |
| UI-01 | Console (UI) | High | Replaced | Same check on v2's console, served by FastAPI. Panels: email, SMS and URL inputs and a voice/video line that reads 'not assessed'. | Pass | none |
| UI-02 | Console (UI) | High | Ported | same check | Pass | none |
| UI-03 | Console (UI) | High | Replaced | Preset scenario 1 = TC-04 (KYC campaign). 'Correlated at or above each single score' is kept. | Fail | D-18 |
| UI-04 | Console (UI) | High | Replaced | Preset scenario 2 = TC-06 (weak parcel campaign). 'Correlated at or above each single score' is kept. | Pass | D-18 |
| UI-05 | Console (UI) | Medium | Replaced | Same check: an email, an SMS and a URL entered by hand; the bundle risk and the shared tokens (v2's evidence) are shown. | Pass | none |
| UI-06 | Console (UI) | Medium | Ported | same check | Pass | none |
| UI-07 | Console (UI) | Low | Ported | same check | Pass | none |
| SYS-02 | End-to-end cases | High | Replaced | HIGH RISK -> alert (bundle risk >= 0.5), SAFE -> no alert. v2's evidence for a shared link is a shared identity token. | Pass | none |
| SYS-03 | End-to-end cases | High | Replaced | S-03 uses fixed scores 0.55 / 0.52 / 0.58, which /correlate cannot take, so it runs through the engine (as COR-10). With v2's single line at 0.5 the best channel already alerts. Kept: the bundle alerts and is at least the best single score. The lift from below the line is SYS-14 / TC-06. | Pass | none |
| SYS-04 | End-to-end cases | High | Replaced | HIGH RISK -> alert (bundle risk >= 0.5), SAFE -> no alert. v2's evidence for a shared link is a shared identity token. | Pass | none |
| SYS-05 | End-to-end cases | Medium | Replaced | HIGH RISK -> alert (bundle risk >= 0.5), SAFE -> no alert. v2's evidence for a shared link is a shared identity token. | Pass | none |
| SYS-06 | End-to-end cases | Medium | Replaced | HIGH RISK -> alert (bundle risk >= 0.5), SAFE -> no alert. v2's evidence for a shared link is a shared identity token. | Pass | none |
| SYS-07 | End-to-end cases | Medium | Replaced | HIGH RISK -> alert (bundle risk >= 0.5), SAFE -> no alert. v2's evidence for a shared link is a shared identity token. The video event must come back 'not assessed' and stay out of the shared tokens and features. | Pass | D-13 |
| SYS-08 | End-to-end cases | High | Replaced | 'Anything except SAFE (for example cannot assess)' becomes: CANNOT_ASSESS with no risk score, or HTTP 4xx. | Pass | D-03 |
| SYS-09 | End-to-end cases | High | Replaced | HIGH RISK -> alert (bundle risk >= 0.5), SAFE -> no alert. v2's evidence for a shared link is a shared identity token. 'No time-proximity evidence' = three separate windows and no shared token inside the scored window. | Pass | none |
| SYS-10 | End-to-end cases | Medium | Replaced | HIGH RISK -> alert (bundle risk >= 0.5), SAFE -> no alert. v2's evidence for a shared link is a shared identity token. 'Time-proximity evidence' = one window holding all three events. | Pass | none |
| SYS-11 | End-to-end cases | High | Replaced | HIGH RISK -> alert (bundle risk >= 0.5), SAFE -> no alert. v2's evidence for a shared link is a shared identity token. | Pass | none |
| SYS-12 | End-to-end cases | High | Replaced | 'Rejected (HTTP 4xx). Not reported as SAFE' is kept as written. | Pass | D-03 |
| SYS-13 | End-to-end cases | High | Replaced | HIGH RISK -> alert (bundle risk >= 0.5), SAFE -> no alert. v2's evidence for a shared link is a shared identity token. | Pass | D-01 |
| SYS-14 | End-to-end cases | High | Ported | same check | Fail | D-12 |
| NFR-01 | Non-functional | High | Ported | same check | Pass | none |
| NFR-02 | Non-functional | Medium | Replaced | S-01 goes to /correlate instead of /analyze. | Pass | none |
| NFR-03 | Non-functional | Medium | Ported | same check | Pass | none |
| NFR-04 | Non-functional | High | Ported | same check | Pass | none |
| NFR-05 | Non-functional | High | Ported | same check | Pass | none |
| NFR-06 | Non-functional | Medium | Replaced | The serving code now includes the event store, which may store message text only when CP1_STORE_CONTENT=1. Same intent: a message sent through the API never appears in a log line, and nothing is written to disk unless the event store is used. | Pass | none |
| NFR-07 | Non-functional | High | Ported | same check | Pass | none |

The actual result of each case is in `reports/final_cases_results.json` and in the FINAL workbook (`reports/Test_Cases_and_Test_Data_FINAL.xlsx`).

## 5. Sample groups (hand-written samples, not a test set)

The plan's 96 hand-written samples, run at the alert line as its 12 sample groups. These are the team's own examples: the counts show behaviour, not a detection rate.

| Channel | Expected | Group | Passed | Target |
|---|---|---|---|---|
| email | Legitimate | Hard case | 2 of 3 | 70% of the group |
| email | Legitimate | Standard | 11 of 11 | 90% of the group |
| email | Phishing | Hard case | 2 of 3 | 70% of the group |
| email | Phishing | Standard | 7 of 11 | 90% of the group |
| sms | Legitimate | Hard case | 2 of 4 | 70% of the group |
| sms | Legitimate | Standard | 11 of 12 | 90% of the group |
| sms | Phishing | Hard case | 3 of 4 | 70% of the group |
| sms | Phishing | Standard | 12 of 12 | 90% of the group |
| url | Legitimate | Hard case | 4 of 5 | 70% of the group |
| url | Legitimate | Standard | 13 of 13 | 90% of the group |
| url | Phishing | Hard case | 5 of 5 | 70% of the group |
| url | Phishing | Standard | 13 of 13 | 90% of the group |

For SMS the alert score is 1 - P(ham), the score the API alerts on.

## 6. Exit criteria

Judged by `scripts/exit_criteria.py` against the targets the plan wrote on 29 Sep. No target was moved after a result. 4 of 8 rows met.

| # | Criterion | Target | Current | Status |
|---|---|---|---|---|
| 1 | All High-priority test cases executed | 0 not run | 0 not run | **Met** |
| 2 | Non-model test cases: pass rate | 95% or more | 95.4% (83 pass, 4 fail) | **Met** |
| 3 | All 12 sample groups meet their targets | 12 of 12 | 8 of 12 | **Not met** |
| 4a | Held-out metrics pass (EML-10, SMS-08, URL-10): the plan's held-out split | 3 of 3 | 3 of 3 | **Met** |
| 4b | The same 0.90 line on the honest measures | 3 of 3 | 1 of 3 | **Not met** |
| 5 | Correlation changes a verdict with real models (SYS-14) | Pass | Fail | **Not met** |
| 6 | Speed tests pass (NFR-01, NFR-02) | 2 of 2 | 2 of 2 | **Met** |
| 7 | No open Critical or High defects | 0 | 3 | **Not met** |

## 7. Defect log

Status comes from the run: a defect is Closed only when every linked case passes. Accepting a defect is the team's call; no defect is marked accepted here.

| Defect | Severity | Module | What is wrong | Status | Linked cases | Fix or proposal |
|---|---|---|---|---|---|---|
| D-01 | High | URL classifier | The URL model flags legitimate URLs as phishing when they start with https:// or end with a slash. github.com scores 0.3 (legitimate) but https://github.com scores 89.4 (phishing). 12 of 13 standard legitimate sample URL | Open | URL-02 Pass, URL-03 Pass, URL-05 Pass, URL-06 Pass, URL-07 Fail, SYS-13 Pass | v2 canonicalises every URL the same way in training and serving, so https:// and a trailing slash no longer change the score (URL-05, URL-06). The remaining failure is U-H06 in URL-07: a real Google sign-in URL with a lo |
| D-02 | Medium | Service (API) | The API accepts empty or invalid input and returns a score. POST {} to /analyze/email returns 'phishing' 73.2. POST {} to /analyze/sms returns 'legitimate' 11.2. POST 'htp:/bad url' to /analyze/url returns 'phishing' 98. | Closed | EML-07 Pass, SMS-07 Pass, URL-08 Pass | Empty text was already refused with HTTP 422 in v2. /score and /correlate now also refuse malformed URLs and unknown channels with HTTP 422 and a message that says why (check_url in src/url_features.py). |
| D-03 | Medium | Scoring and verdict | A case with nothing to assess is reported SAFE. POST {} to /analyze returns combined score 0 and 'LOW RISK'. A case with only a video transcript (the stub says 'unavailable') is also SAFE. A caller cannot tell 'checked a | Closed | SCO-06 Pass, VV-05 Pass, SYS-08 Pass, SYS-12 Pass | An empty request is refused with HTTP 422. A bundle whose events cannot be assessed (calls, voice, video, or a channel whose model is missing) answers status CANNOT_ASSESS with no risk and the label 'cannot assess', neve |
| D-04 | High | Correlation engine | Time-proximity evidence has no maximum window. The engine works out the span between the email, SMS and URL timestamps but never compares it with a limit. Events 6 days apart still add +6 and the text says 'active within | Closed | COR-12 Pass, SYS-09 Pass | Events further apart than the window (60 minutes) are not combined or linked. Each window is scored on its own and the bundle takes the highest. |
| D-05 | Medium | Correlation engine | Shared-link matching only recognises links that end in one of 12 listed endings (com, net, org, tk, xyz, top, club, info, biz, ly, click, gq, ml). The same link on secure-bank-verify.online/login is not matched. In S-11  | Closed | COR-14 Pass, SYS-11 Pass | Domains are matched on the full public suffix list, so .online and .co.in hosts link events. |
| D-06 | High | Service (API) | No CORS settings. A browser page on another origin (for example the React console on http://localhost:5173) is blocked: GET /health returns no Access-Control-Allow-Origin header and OPTIONS /analyze returns 405. | Closed | API-12 Pass | CORS names the console's development origins (localhost:5173 and 127.0.0.1:5173, CP1_CORS_ORIGINS to change) and never '*'. The built console is served by the API itself, so it needs no CORS. |
| D-07 | Low | Service (API) | Non-numeric timestamps cause HTTP 500. timestamps is an untyped dict. When two or more channels are flagged and email, SMS and URL all have timestamps, the engine subtracts the values and raises a TypeError. | Closed | API-08 Pass | A 'time' that is not a number or an ISO timestamp gives HTTP 422 with the event number, not a 500. |
| D-08 | Medium | Correlation engine | Ordinary words count as a 'claimed identity'. The engine takes the first shared word of 4 or more letters that is not in a 16-word stop list. In the demo scenario the 'identity' is 'detected'. In S-02 it is 'urgent'. Bot | Closed | COR-07 Pass | Ordinary words are never identity tokens. |
| D-09 | High | SMS classifier | The SMS model misses most phishing-style messages. Only 1 of 12 standard phishing SMS was flagged (bank, KYC, UPI, e-challan and parcel-fee lures) and 2 of 4 hard cases. All 12 standard legitimate SMS were correct. The c | Open | SMS-01 Pass, SMS-03 Fail | The fault described here, missed phishing SMS, no longer shows: SMS-01 catches every standard phishing SMS. SMS-03 still fails, but on its legitimate half (bank alerts flagged), which is D-16. The case cannot pass, and s |
| D-10 | Medium | Email classifier | The email model flags some legitimate consumer-style mail: payment receipt E-L08 scored 82.4, statement notice E-H06 73.5, security alert E-H04 96.0, personal photo message E-L06 56.8. Standard legitimate emails: 9 of 11 | Open | EML-02 Pass, EML-03 Fail | EML-02 passes on v2. EML-03 still fails: one hard legitimate email (E-H04) is flagged, and one hard phishing email is missed (D-17). Two retrain attempts with the Nazario, SpamAssassin and Ling corpora (reports/candidate |
| D-11 | Low | Preprocessing | clean_text() does not remove HTML. Tags and script text stay in what the model sees. The effect on accuracy was not measured. | Closed | PRE-01 Pass | clean_text() drops script, style, head and title blocks with their content, keeps link targets as URLs, and strips only real tags. Training uses the same cleaner, so the email model is retrained in Phase 3. |
| D-12 | Medium | End-to-end cases | With the real models, correlation never changes the verdict on the test cases. Email, SMS and URL each score 88 or more on their own, so the best channel is already HIGH RISK and the bonus only lifts it to 100 (S-01: 99. | Open | SYS-14 Fail | Proposed: accept because no case in S-01, S-02 or S-11 can show a lift (each already alerts alone), and the lift is shown instead by TC-06 against TC-07. This stays a hand-written and simulated result until real bundles  |
| D-13 | Medium | Correlation engine | On v2, /correlate refuses the whole bundle with HTTP 501 when any one event is a call or a video. The email and SMS in the same bundle are never scored. | Closed | VV-03 Pass, VV-04 Pass, COR-09 Pass, SYS-07 Pass | Call, voice and video events are returned as 'not assessed' (score null, with the reason) and kept out of the fusion features, the shared tokens and the window. The rest of the bundle is scored as before. |
| D-14 | Medium | Service (API) | On v2, the API does not start when one model file is missing (FileNotFoundError at import). There is no degraded mode. | Closed | API-09 Pass | Each model loads on its own. A missing one makes only that channel unavailable: /health says 'degraded', /score answers 503 for it, and /correlate lists its events as not assessed. |
| D-15 | Low | Preprocessing | clean_text(123) returns '123'. The plan expects an empty string for any input that is not text. | Closed | PRE-03 Pass | clean_text() returns an empty string for anything that is not a string. |
| D-16 | Medium | SMS classifier | The SMS model flags legitimate transactional bank SMS: the card-use alert S-H05 and the bill reminder S-H08 in the hard group, and the credit alert S-L05 in the standard group (SMS-02 still meets its target). Scores are  | Open | SMS-03 Fail | Needs retraining with more legitimate transactional SMS (Phase 3.3), from a source whose licence can be checked. |
| D-17 | High | Email classifier | The email model misses standard phishing emails that the old build caught: E-P03 (password expiry), E-P06 (fake invoice), E-P07 (gift-card CEO fraud) and E-P09 (fake job offer), and the hard case E-H01. results.md limita | Open | EML-01 Fail, EML-03 Fail | Not fixed. Two retrain attempts with the Nazario, SpamAssassin and Ling corpora (reports/candidates/email_candidates.md and email_candidates_attempt2.md) raised the honest email measure beyond v2's interval and caught mo |
| D-18 | Low | Correlation engine | The learned correlation model can give a bundle less risk than its strongest event when the other events in the window are weaker: in S-06 the email alone scores higher than the bundle, and in TC-04 (UI-03) the bundle sh | Open | SCO-08 Fail, UI-03 Fail, UI-04 Pass | Proposed: accept because the alert does not change in S-06, and lowering a lone high score next to benign events is where the model's lower false-alarm rate on simulated bundles comes from. Recheck on real bundles (R2-10 |

## 8. What was not tested, and why

- **Voice and video.** No detector is built (no accessible data). Their cases are N/A; calls and video answer 'not assessed', never SAFE.
- **Real multi-channel bundles.** None collected yet (R2-10). Correlation is measured on simulated bundles only; SYS-14 with real bundles is still open.
- **The demo laptop.** Latency, offline and UI checks ran on the build laptop. A person confirms the demo laptop or re-runs `scripts/benchmark.py` and `scripts/preflight.py` there.
- **A real Wi-Fi-off run.** `scripts/offline_check.py` blocks sockets in software. One run with the network switched off is a person's job (R3-06).
- **Other browsers and Linux.** The console was checked in Chrome and Edge on Windows; NFR-05 ran on Windows.
- **Load.** Requests were timed one at a time. No concurrent-load test was run.
- **Security testing beyond the plan's cases.** Input checks, the secret scan and the privacy checks ran; no penetration test.
- **Calibration.** Scores are not calibrated probabilities, so no calibration test applies.
