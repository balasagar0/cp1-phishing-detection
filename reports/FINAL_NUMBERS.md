# Final numbers (CP1)

**Build: tag `cp1-final`, commit `18ba1d94b103ebeac3aefd775f4d9673c039b451` (07 Nov 2026).** Written by `scripts/make_final_numbers.py` on 2026-11-14T10:59:00+05:30. Every number is read from `reports/` or measured by that script on this build; none is typed. The script checks that the API, models and training code (`api.py`, `src`, `models`, `console/dist`, `console.html`, `requirements.txt`, `requirements.lock.txt`) are byte for byte those of `cp1-final` before it writes anything.

Quote the honest number. Never quote the flattering one alone. Simulated results are always called simulated. Demo cases are hand-written, not a test set.

## 1. Detectors

### Email (TF-IDF word 1-2-grams, numbers masked, logistic regression)

72,428 emails from 3 corpora (CEAS_08, Enron, FraudEmail) after cleaning and de-duplication. A term is kept only if it appears in at least two corpora (49,011 of 400,000 candidate terms).

**Honest: F1 82.2%**, the mean of 3 leave-one-corpus-out runs (train on two corpora, test on the third).

| Measure | n | Precision | Recall | F1 | False-positive rate | ROC-AUC | TN / FP / FN / TP |
|---|---|---|---|---|---|---|---|
| Held out: CEAS_08 | 34,294 | 77.7% | 96.5% | 86.1% | 28.0% | 0.9419 | 12,281 / 4,765 / 609 / 16,639 |
| Held out: Enron | 28,917 | 97.1% | 61.0% | 74.9% | 1.8% | 0.9470 | 14,224 / 261 / 5,627 / 8,805 |
| Held out: FraudEmail | 9,217 | 77.7% | 95.4% | 85.7% | 22.2% | 0.9634 | 3,961 / 1,130 / 189 / 3,937 |
| **Flattering:** pooled random split | 7,243 | 98.7% | 98.8% | 98.8% | 1.3% | 0.9992 | 3,616 / 46 / 43 / 3,538 |

The pooled split's F1 95% CI is 98.5%-99.0%. It is flattering because each corpus has its own style.

On real mail: the live email model flags 23.5% of 4,069 legitimate emails from the account owner's own mailbox, and 21.6% of 2,104 generated legitimate transactional emails (`reports/candidates/email_candidates_v3.json`, one class only: false-positive rate). 3 retrain attempts failed the adoption rule; v2's email model stays live.

### SMS (three classes: ham, spam, smishing)

5,789 messages: 4,829 ham, 433 spam, 527 smishing. Test split 1,158 messages, of which 105 smishing. The alert score is 1 - P(ham).

**Honest: smishing-vs-rest F1 87.1% (95% CI 82.3%-91.7%).**

| Measure | n | Precision | Recall | F1 | False-positive rate | ROC-AUC | TN / FP / FN / TP |
|---|---|---|---|---|---|---|---|
| **Honest:** smishing vs rest | 1,158 | 90.7% | 83.8% | 87.1% | 0.9% | 0.9851 | 1,044 / 9 / 17 / 88 |
| **Flattering:** spam or smishing vs ham | 1,158 | 99.5% | 96.9% | 98.2% | 0.1% | 0.9964 | 965 / 1 / 6 / 186 |

Three-class macro F1: 89.7%. Few smishing examples, so the interval is wide.

### URL (character n-grams on the URL text, 3 popularity flags, logistic regression; no network lookups)

260,000 URLs on 101,523 hosts, split 80/20 by host so no host is in both halves (204,817 train, 55,183 test).

**Honest: host-grouped F1 90.4% (95% CI 90.0%-90.9%).**

| Measure | n | Precision | Recall | F1 | False-positive rate | ROC-AUC | TN / FP / FN / TP |
|---|---|---|---|---|---|---|---|
| **Honest:** host-grouped test | 55,183 | 96.1% | 85.4% | 90.4% | 0.6% | 0.9848 | 46,950 / 277 / 1,160 / 6,796 |
| **Flattering:** offline feature benchmark, random split, 111 features | 17,440 | 95.4% | 95.4% | 95.4% | 2.5% | 0.9943 | 11,060 / 282 / 279 / 5,819 |

The login-page trade-off: false alarms on login URLs of 1,000 held-out popular domains fell from 92.2% to 0.0%; recall on bad URLs hosted on top-10k domains fell from 49.9% to 30.7% (n = 381); detection of brand-impersonation probes went from 99.4% to 95.3%. Quote both halves.

### Voice and video

Not trained. No accessible data. `/score` answers HTTP 501 for them; `/correlate` and `/events` mark calls 'not assessed' (`CANNOT_ASSESS`). Never SAFE.

## 2. Correlation (SIMULATED bundles)

Trained on 24,000 simulated bundles, tuned on 8,000, tested on 12,000 (49.6% malicious). The events are real held-out messages; the links between them are constructed. No public dataset links one attacker's events across channels. The risk is not a calibrated probability, and the alert line 0.5 is tied to the simulation's mix.

| Method (SIMULATED, alert line 0.5) | Precision | Recall | F1 (95% CI) | False-positive rate (95% CI) | Hard campaigns flagged |
|---|---|---|---|---|---|
| Single-channel: alert if any event >= 0.5 | 87.0% | 95.3% | 91.0% (90.4%-91.4%) | 14.1% (13.2%-15.1%) | 0.0% |
| Parallel multi-channel: fusion without link and timing features | 97.0% | 92.2% | 94.5% (94.2%-94.9%) | 2.8% (2.5%-3.3%) | 11.1% |
| Correlation model on the whole bundle (pools up to 72 h) | 97.0% | 92.9% | 94.9% (94.6%-95.3%) | 2.8% (2.5%-3.2%) | 18.5% |
| **Deployed engine: 60-minute windows (what the API does)** | 89.4% | 94.9% | 92.0% (91.5%-92.5%) | 11.1% (10.3%-11.9%) | 18.5% |

Engine without a window: precision 96.8%, recall 93.0%, F1 94.8%, false-positive rate 3.0%.

Hard campaigns: 27 simulated linked attacks (0.8% of them) have every event below 0.5. 95.6% of simulated linked attack bundles fit inside 60 minutes. AUC: 0.9746 (max single score) -> 0.9847 (learned combination) -> 0.9874 (with link and timing).

Patent noisy-OR row: not evaluated: the owner decided on 7 Nov 2026 that the patent will be written from this build; the old draft's noisy-OR method and its generated numbers are not used. Real bundles: blocked on R2-10: 0 real bundles collected.

**Reading:** inside the window the engine beats single-channel alerting by a little, on simulated bundles. That claim stays open until real bundles test it.

## 3. The time window

**60 minutes**, set at `src/fusion.py:13` (`DEFAULT_WINDOW_MIN`). Used at `src/eval_comparison.py:40`, `src/eval_comparison.py:61`, `src/eval_window.py:39`, `src/fusion.py:59`, `src/fusion.py:71`, `src/fusion.py:143`. Events further apart are not combined or linked; each window is scored and the bundle takes the highest; a window with one event gets that event's detector score. The value was fixed before the window evaluation ran. The simulation cannot settle it; `src/refit_fusion.py` suggests one from real bundles.

## 4. Demo cases and stories (hand-written, not a test set)

Scored on this build through `/correlate`. Never compute a rate from these.

| Case | What it is | Channels | Event scores | Alerts alone? | Bundle risk | Outcome |
|---|---|---|---|---|---|---|
| TC-01 | Phishing email alone | email | 0.998 | yes | 0.998 | alert |
| TC-02 | Smishing SMS alone | sms | 1.000 | yes | 1.000 | alert |
| TC-03 | Voice call (not assessed: no voice detector) | call | not assessed | not assessed | CANNOT_ASSESS | not assessed |
| TC-04 | SMS + URL + email on one domain, 12 min | sms, url, email | 1.000 / 0.995 / 0.998 | yes | 1.000 | alert |
| TC-05 | A colleague shares an article, 10 min | sms, email, url | 0.002 / 0.000 / 0.000 | no | 0.000 | no alert |
| TC-06 | Weak parcel campaign, 15 min | sms, url, email | 0.421 / 0.451 / 0.204 | no | 0.595 | alert |
| TC-07 | TC-06's messages, 3 days apart | sms, url, email | 0.421 / 0.451 / 0.204 | no | 0.451 | no alert |
| TC-08 | Courier SMS + email sharing a tracking number | sms, email | 0.970 / 0.031 | yes | 1.000 | alert |
| IN-01 | KYC freeze (SMS, link, call) | sms, url, call | 1.000 / 0.927 / not assessed | yes | 1.000 | alert |
| IN-02 | Courier customs fee (SMS, email, link) | sms, email, url | 0.927 / 0.437 / 0.988 | yes | 1.000 | alert |
| IN-03 | Work-from-home task scam (SMS, email) | sms, email | 0.736 / 0.479 | yes | 0.999 | alert |
| IN-04 | Legitimate order (should stay quiet) | sms, email, url | 0.412 / 0.400 / 0.005 | no | 0.053 | no alert |

The final run on `cp1-rc1` was not adopted: its retrained correlation model moves TC-06 from 0.595 to 0.456 (live correlation model with the retrained detectors: 0.595). See `reports/final_run/README.md`.

## 5. Tests and checks on this build

| Check | Result | Evidence |
|---|---|---|
| pytest | 180 passed, 7 expected failures (open defects), 1 skipped, 0 failed | `reports/test_run.json` |
| Smoke test | 24 passed, 1 skipped, 0 failed | `tests/smoke_test.py` |
| Ported test-plan cases | 112 cases: 7 Fail, 1 Known limitation, 12 N/A, 92 Pass; run on `cp1-final` | `reports/final_cases_results.json` |
| Exit criteria | 4 of 8 rows met | `reports/exit_criteria.md` |
| End-to-end (API -> correlation -> event store -> alert -> console) | 10 of 10 steps pass | `reports/e2e_check.md` |
| Console UI checks (Chrome and Edge) | 6 of 7 pass; failing: UI-03 | `reports/ui_checks.json` |
| Offline (no network at runtime) | pass | `reports/offline_check.md` |
| NFR-05: fresh clone from the README alone | Pass | `reports/nfr05_fresh_clone.json` |

Exit criteria, judged against the plan's own targets:

| # | Criterion | Result |
|---|---|---|
| 1 | All High-priority test cases executed | met: 0 not run |
| 2 | Non-model test cases: pass rate | met: 95.4% (83 pass, 4 fail) |
| 3 | All 12 sample groups meet their targets | not met: 8 of 12 |
| 4a | Held-out metrics pass (EML-10, SMS-08, URL-10): the plan's held-out split | met: 3 of 3 |
| 4b | The same 0.90 line on the honest measures | not met: 1 of 3 |
| 5 | Correlation changes a verdict with real models (SYS-14) | not met: Fail |
| 6 | Speed tests pass (NFR-01, NFR-02) | met: 2 of 2 |
| 7 | No open Critical or High defects | not met: 3 |

**Defects:** 7 open, 11 closed. Open: D-01 (High), D-09 (High), D-10 (Medium), D-12 (Medium), D-16 (Medium), D-17 (High), D-18 (Low). Closed: D-02, D-03, D-04, D-05, D-06, D-07, D-08, D-11, D-13, D-14, D-15. Accepting a defect is the team's call; proposals are in `reports/defect_log.md`.

## 6. Latency (real HTTP, one request at a time)

Machine: AMD Ryzen 7 5800HS with Radeon Graphics (16 logical CPUs), 15.4 GB RAM, Windows-11-10.0.26200-SP0, Python 3.13.0. Demo laptop: not confirmed: Viraj confirms whether this is the demo laptop, or re-runs this script on it (R3-10).

| Request | n | Median | 95th percentile | Max | Target |
|---|---|---|---|---|---|
| `/score` email | 100 | 23 ms | 39 ms | 138 ms | NFR-01: median 2 s or less |
| `/score` sms | 100 | 12 ms | 14 ms | 16 ms | NFR-01: median 2 s or less |
| `/score` url | 100 | 6 ms | 8 ms | 10 ms | NFR-01: median 2 s or less |
| `/correlate` full case | 100 | 67 ms | 89 ms | 1970 ms | NFR-02: every case 5 s or less |

Server start-up (models loaded, `/health` answering): 8.2 s.

## 7. What is not built

- Voice and video detectors: not trained, no accessible data. Calls and video are 'not assessed', never SAFE.
- Any result on real multi-channel bundles: 0 collected (R2-10). The correlation numbers above are simulated.
- A calibrated probability. The 0.5 line is tied to the simulation's half-malicious mix.
- A message queue or streaming source. The event store regroups a recipient's events on each `POST /events`.
- The old patent draft's noisy-OR score, 30-minute window, watch list, hash-chained audit log and voice module. Not built; the noisy-OR score is not evaluated (owner, 7 Nov 2026).
- Mail, SMS or browser integration. Messages reach the API only through its routes and the console.

## 8. Measured limitations

1. **Email does not transfer across corpora.** Leave-one-corpus-out F1 82.2% against 98.8% pooled. False-positive rates on unseen corpora: 1.8% to 28.0%; recall 61.0% to 96.5%.
2. **Email on real mail.** The live model flags 23.5% of 4,069 real legitimate emails from one person's mailbox.
3. **URL: login-page fix costs recall on popular domains.** Login false alarms 92.2% -> 0.0%; bad-URL recall on top-10k domains 49.9% -> 30.7%.
4. **SMS has few smishing examples** (105 in the test split), so the F1 interval is wide (82.3%-91.7%).
5. **Correlation is measured only on simulated bundles.** On them, the 60-minute engine has F1 92.0% and false-positive rate 11.1%, against 91.0% and 14.1% for single-channel alerting.
6. **The correlation model is not stable on borderline bundles.** A retrain on almost the same simulated data moves TC-06 from 0.595 to 0.456 while the simulated F1 moves from 92.0% to 92.1%.
7. **The correlated score can sit below the best single score** (D-18, UI-03): a lone high score next to benign-looking events is lowered a little.
8. **A detector false positive stays a false positive.** Correlation does not fix it (TC-08's courier SMS).

## 9. Retired numbers

These numbers are wrong. They must not be quoted. Patent Tables 2 and 3 are not listed: the old specification is not used (owner, 7 Nov 2026).

- email F1 0.947 (Review-2 deck)
- SMS F1 0.926 (Review-2 deck)
- URL F1 0.960 (Review-2 deck)
- F1 0.991 (TRAINING_REPORT.md)
- 'linear SVM' (TRAINING_REPORT.md)
- '460 campaigns'
- '80.0% -> 84.5%'
- '22 of 60'
- '32 of 60'
- '142 cases'
- '30-minute window'
- '50-minute window'
- quiet-attack demo score 87.8
- quiet-attack demo score 85.6
- voice ROC-AUC 0.952
- '19 routes'

Repository search: 199 text files (every tracked file except the built console bundle, plus the team's text inputs in `docs/inputs/`). 213 hits: 188 quotes it as wrong; 1 received, not edited; 24 written by code: a different measured value with the same digits, not the retired claim. Files received with v2 or given as team input are listed and not edited.

| Number | File | Line | Origin | Verdict |
|---|---|---|---|---|
| email F1 0.947 (Review-2 deck) | `CLAUDE.md` | 23 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `CLAUDE.md` | 23 | written in the CP1 finish work | quotes it as wrong |
| URL F1 0.960 (Review-2 deck) | `CLAUDE.md` | 23 | written in the CP1 finish work | quotes it as wrong |
| '142 cases' | `CLAUDE.md` | 227 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `CLAUDE.md` | 20 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `CLAUDE.md` | 227 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `CLAUDE.md` | 242 | written in the CP1 finish work | quotes it as wrong |
| '19 routes' | `CLAUDE.md` | 19 | written in the CP1 finish work | quotes it as wrong |
| '19 routes' | `CLAUDE.md` | 227 | written in the CP1 finish work | quotes it as wrong |
| email F1 0.947 (Review-2 deck) | `CP1_FINISH_TASK.md` | 252 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `CP1_FINISH_TASK.md` | 252 | written in the CP1 finish work | quotes it as wrong |
| URL F1 0.960 (Review-2 deck) | `CP1_FINISH_TASK.md` | 252 | written in the CP1 finish work | quotes it as wrong |
| F1 0.991 (TRAINING_REPORT.md) | `CP1_FINISH_TASK.md` | 252 | written in the CP1 finish work | quotes it as wrong |
| 'linear SVM' (TRAINING_REPORT.md) | `CP1_FINISH_TASK.md` | 252 | written in the CP1 finish work | quotes it as wrong |
| '460 campaigns' | `CP1_FINISH_TASK.md` | 252 | written in the CP1 finish work | quotes it as wrong |
| '80.0% -> 84.5%' | `CP1_FINISH_TASK.md` | 252 | written in the CP1 finish work | quotes it as wrong |
| '22 of 60' | `CP1_FINISH_TASK.md` | 252 | written in the CP1 finish work | quotes it as wrong |
| '32 of 60' | `CP1_FINISH_TASK.md` | 252 | written in the CP1 finish work | quotes it as wrong |
| '142 cases' | `CP1_FINISH_TASK.md` | 72 | written in the CP1 finish work | quotes it as wrong |
| '142 cases' | `CP1_FINISH_TASK.md` | 252 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `CP1_FINISH_TASK.md` | 72 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `CP1_FINISH_TASK.md` | 87 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `CP1_FINISH_TASK.md` | 252 | written in the CP1 finish work | quotes it as wrong |
| '50-minute window' | `CP1_FINISH_TASK.md` | 252 | written in the CP1 finish work | quotes it as wrong |
| quiet-attack demo score 87.8 | `CP1_FINISH_TASK.md` | 252 | written in the CP1 finish work | quotes it as wrong |
| quiet-attack demo score 85.6 | `CP1_FINISH_TASK.md` | 252 | written in the CP1 finish work | quotes it as wrong |
| voice ROC-AUC 0.952 | `CP1_FINISH_TASK.md` | 252 | written in the CP1 finish work | quotes it as wrong |
| '19 routes' | `CP1_FINISH_TASK.md` | 72 | written in the CP1 finish work | quotes it as wrong |
| '19 routes' | `CP1_FINISH_TASK.md` | 252 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `TESTCASE_FORMAT.md` | 55 | received with v2, unchanged | received, not edited |
| email F1 0.947 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 165 | written in the CP1 finish work | quotes it as wrong |
| email F1 0.947 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 186 | written in the CP1 finish work | quotes it as wrong |
| email F1 0.947 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 195 | written in the CP1 finish work | quotes it as wrong |
| email F1 0.947 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 218 | written in the CP1 finish work | quotes it as wrong |
| email F1 0.947 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 220 | written in the CP1 finish work | quotes it as wrong |
| email F1 0.947 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 226 | written in the CP1 finish work | quotes it as wrong |
| email F1 0.947 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 232 | written in the CP1 finish work | quotes it as wrong |
| email F1 0.947 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 235 | written in the CP1 finish work | quotes it as wrong |
| email F1 0.947 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 237 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 166 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 187 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 196 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 221 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 223 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 225 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 228 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 229 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 231 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 233 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 236 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 239 | written in the CP1 finish work | quotes it as wrong |
| URL F1 0.960 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 167 | written in the CP1 finish work | quotes it as wrong |
| URL F1 0.960 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 188 | written in the CP1 finish work | quotes it as wrong |
| URL F1 0.960 (Review-2 deck) | `reports/FINAL_NUMBERS.md` | 197 | written in the CP1 finish work | quotes it as wrong |
| F1 0.991 (TRAINING_REPORT.md) | `reports/FINAL_NUMBERS.md` | 168 | written in the CP1 finish work | quotes it as wrong |
| F1 0.991 (TRAINING_REPORT.md) | `reports/FINAL_NUMBERS.md` | 198 | written in the CP1 finish work | quotes it as wrong |
| F1 0.991 (TRAINING_REPORT.md) | `reports/FINAL_NUMBERS.md` | 216 | written in the CP1 finish work | quotes it as wrong |
| F1 0.991 (TRAINING_REPORT.md) | `reports/FINAL_NUMBERS.md` | 217 | written in the CP1 finish work | quotes it as wrong |
| F1 0.991 (TRAINING_REPORT.md) | `reports/FINAL_NUMBERS.md` | 222 | written in the CP1 finish work | quotes it as wrong |
| F1 0.991 (TRAINING_REPORT.md) | `reports/FINAL_NUMBERS.md` | 224 | written in the CP1 finish work | quotes it as wrong |
| F1 0.991 (TRAINING_REPORT.md) | `reports/FINAL_NUMBERS.md` | 227 | written in the CP1 finish work | quotes it as wrong |
| F1 0.991 (TRAINING_REPORT.md) | `reports/FINAL_NUMBERS.md` | 230 | written in the CP1 finish work | quotes it as wrong |
| F1 0.991 (TRAINING_REPORT.md) | `reports/FINAL_NUMBERS.md` | 234 | written in the CP1 finish work | quotes it as wrong |
| F1 0.991 (TRAINING_REPORT.md) | `reports/FINAL_NUMBERS.md` | 238 | written in the CP1 finish work | quotes it as wrong |
| 'linear SVM' (TRAINING_REPORT.md) | `reports/FINAL_NUMBERS.md` | 169 | written in the CP1 finish work | quotes it as wrong |
| 'linear SVM' (TRAINING_REPORT.md) | `reports/FINAL_NUMBERS.md` | 199 | written in the CP1 finish work | quotes it as wrong |
| '460 campaigns' | `reports/FINAL_NUMBERS.md` | 170 | written in the CP1 finish work | quotes it as wrong |
| '460 campaigns' | `reports/FINAL_NUMBERS.md` | 200 | written in the CP1 finish work | quotes it as wrong |
| '80.0% -> 84.5%' | `reports/FINAL_NUMBERS.md` | 171 | written in the CP1 finish work | quotes it as wrong |
| '80.0% -> 84.5%' | `reports/FINAL_NUMBERS.md` | 201 | written in the CP1 finish work | quotes it as wrong |
| '80.0% -> 84.5%' | `reports/FINAL_NUMBERS.md` | 219 | written in the CP1 finish work | quotes it as wrong |
| '22 of 60' | `reports/FINAL_NUMBERS.md` | 172 | written in the CP1 finish work | quotes it as wrong |
| '22 of 60' | `reports/FINAL_NUMBERS.md` | 202 | written in the CP1 finish work | quotes it as wrong |
| '32 of 60' | `reports/FINAL_NUMBERS.md` | 173 | written in the CP1 finish work | quotes it as wrong |
| '32 of 60' | `reports/FINAL_NUMBERS.md` | 203 | written in the CP1 finish work | quotes it as wrong |
| '142 cases' | `reports/FINAL_NUMBERS.md` | 174 | written in the CP1 finish work | quotes it as wrong |
| '142 cases' | `reports/FINAL_NUMBERS.md` | 189 | written in the CP1 finish work | quotes it as wrong |
| '142 cases' | `reports/FINAL_NUMBERS.md` | 204 | written in the CP1 finish work | quotes it as wrong |
| '142 cases' | `reports/FINAL_NUMBERS.md` | 205 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `reports/FINAL_NUMBERS.md` | 147 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `reports/FINAL_NUMBERS.md` | 175 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `reports/FINAL_NUMBERS.md` | 190 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `reports/FINAL_NUMBERS.md` | 191 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `reports/FINAL_NUMBERS.md` | 192 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `reports/FINAL_NUMBERS.md` | 206 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `reports/FINAL_NUMBERS.md` | 207 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `reports/FINAL_NUMBERS.md` | 208 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `reports/FINAL_NUMBERS.md` | 215 | written in the CP1 finish work | quotes it as wrong |
| '50-minute window' | `reports/FINAL_NUMBERS.md` | 176 | written in the CP1 finish work | quotes it as wrong |
| '50-minute window' | `reports/FINAL_NUMBERS.md` | 209 | written in the CP1 finish work | quotes it as wrong |
| quiet-attack demo score 87.8 | `reports/FINAL_NUMBERS.md` | 177 | written in the CP1 finish work | quotes it as wrong |
| quiet-attack demo score 87.8 | `reports/FINAL_NUMBERS.md` | 210 | written in the CP1 finish work | quotes it as wrong |
| quiet-attack demo score 85.6 | `reports/FINAL_NUMBERS.md` | 178 | written in the CP1 finish work | quotes it as wrong |
| quiet-attack demo score 85.6 | `reports/FINAL_NUMBERS.md` | 211 | written in the CP1 finish work | quotes it as wrong |
| voice ROC-AUC 0.952 | `reports/FINAL_NUMBERS.md` | 179 | written in the CP1 finish work | quotes it as wrong |
| voice ROC-AUC 0.952 | `reports/FINAL_NUMBERS.md` | 212 | written in the CP1 finish work | quotes it as wrong |
| '19 routes' | `reports/FINAL_NUMBERS.md` | 180 | written in the CP1 finish work | quotes it as wrong |
| '19 routes' | `reports/FINAL_NUMBERS.md` | 193 | written in the CP1 finish work | quotes it as wrong |
| '19 routes' | `reports/FINAL_NUMBERS.md` | 194 | written in the CP1 finish work | quotes it as wrong |
| '19 routes' | `reports/FINAL_NUMBERS.md` | 213 | written in the CP1 finish work | quotes it as wrong |
| '19 routes' | `reports/FINAL_NUMBERS.md` | 214 | written in the CP1 finish work | quotes it as wrong |
| F1 0.991 (TRAINING_REPORT.md) | `reports/baseline_check.md` | 107 | written in the CP1 finish work | written by code: a different measured value with the same digits, not the retired claim |
| F1 0.991 (TRAINING_REPORT.md) | `reports/baseline_check.md` | 116 | written in the CP1 finish work | written by code: a different measured value with the same digits, not the retired claim |
| email F1 0.947 (Review-2 deck) | `reports/candidates/email_candidates.json` | 20 | written in the CP1 finish work | written by code: a different measured value with the same digits, not the retired claim |
| '80.0% -> 84.5%' | `reports/candidates/email_candidates_attempt2.md` | 22 | written in the CP1 finish work | written by code: a different measured value with the same digits, not the retired claim |
| email F1 0.947 (Review-2 deck) | `reports/email_metrics.json` | 208 | received with v2, unchanged | written by code: a different measured value with the same digits, not the retired claim |
| email F1 0.947 (Review-2 deck) | `reports/final_numbers.json` | 624 | written in the CP1 finish work | quotes it as wrong |
| email F1 0.947 (Review-2 deck) | `reports/final_numbers.json` | 687 | written in the CP1 finish work | quotes it as wrong |
| email F1 0.947 (Review-2 deck) | `reports/final_numbers.json` | 848 | written in the CP1 finish work | quotes it as wrong |
| email F1 0.947 (Review-2 deck) | `reports/final_numbers.json` | 862 | written in the CP1 finish work | quotes it as wrong |
| email F1 0.947 (Review-2 deck) | `reports/final_numbers.json` | 904 | written in the CP1 finish work | quotes it as wrong |
| email F1 0.947 (Review-2 deck) | `reports/final_numbers.json` | 946 | written in the CP1 finish work | quotes it as wrong |
| email F1 0.947 (Review-2 deck) | `reports/final_numbers.json` | 967 | written in the CP1 finish work | quotes it as wrong |
| email F1 0.947 (Review-2 deck) | `reports/final_numbers.json` | 981 | written in the CP1 finish work | quotes it as wrong |
| email F1 0.947 (Review-2 deck) | `reports/final_numbers.json` | 1004 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/final_numbers.json` | 631 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/final_numbers.json` | 694 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/final_numbers.json` | 869 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/final_numbers.json` | 883 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/final_numbers.json` | 897 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/final_numbers.json` | 918 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/final_numbers.json` | 925 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/final_numbers.json` | 939 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/final_numbers.json` | 953 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/final_numbers.json` | 974 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/final_numbers.json` | 995 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/final_numbers.json` | 1005 | written in the CP1 finish work | quotes it as wrong |
| URL F1 0.960 (Review-2 deck) | `reports/final_numbers.json` | 638 | written in the CP1 finish work | quotes it as wrong |
| URL F1 0.960 (Review-2 deck) | `reports/final_numbers.json` | 701 | written in the CP1 finish work | quotes it as wrong |
| URL F1 0.960 (Review-2 deck) | `reports/final_numbers.json` | 1006 | written in the CP1 finish work | quotes it as wrong |
| F1 0.991 (TRAINING_REPORT.md) | `reports/final_numbers.json` | 708 | written in the CP1 finish work | quotes it as wrong |
| F1 0.991 (TRAINING_REPORT.md) | `reports/final_numbers.json` | 834 | written in the CP1 finish work | quotes it as wrong |
| F1 0.991 (TRAINING_REPORT.md) | `reports/final_numbers.json` | 841 | written in the CP1 finish work | quotes it as wrong |
| F1 0.991 (TRAINING_REPORT.md) | `reports/final_numbers.json` | 876 | written in the CP1 finish work | quotes it as wrong |
| F1 0.991 (TRAINING_REPORT.md) | `reports/final_numbers.json` | 890 | written in the CP1 finish work | quotes it as wrong |
| F1 0.991 (TRAINING_REPORT.md) | `reports/final_numbers.json` | 911 | written in the CP1 finish work | quotes it as wrong |
| F1 0.991 (TRAINING_REPORT.md) | `reports/final_numbers.json` | 932 | written in the CP1 finish work | quotes it as wrong |
| F1 0.991 (TRAINING_REPORT.md) | `reports/final_numbers.json` | 960 | written in the CP1 finish work | quotes it as wrong |
| F1 0.991 (TRAINING_REPORT.md) | `reports/final_numbers.json` | 988 | written in the CP1 finish work | quotes it as wrong |
| F1 0.991 (TRAINING_REPORT.md) | `reports/final_numbers.json` | 1007 | written in the CP1 finish work | quotes it as wrong |
| 'linear SVM' (TRAINING_REPORT.md) | `reports/final_numbers.json` | 715 | written in the CP1 finish work | quotes it as wrong |
| 'linear SVM' (TRAINING_REPORT.md) | `reports/final_numbers.json` | 1008 | written in the CP1 finish work | quotes it as wrong |
| '460 campaigns' | `reports/final_numbers.json` | 722 | written in the CP1 finish work | quotes it as wrong |
| '460 campaigns' | `reports/final_numbers.json` | 1009 | written in the CP1 finish work | quotes it as wrong |
| '80.0% -> 84.5%' | `reports/final_numbers.json` | 729 | written in the CP1 finish work | quotes it as wrong |
| '80.0% -> 84.5%' | `reports/final_numbers.json` | 855 | written in the CP1 finish work | quotes it as wrong |
| '80.0% -> 84.5%' | `reports/final_numbers.json` | 1010 | written in the CP1 finish work | quotes it as wrong |
| '22 of 60' | `reports/final_numbers.json` | 736 | written in the CP1 finish work | quotes it as wrong |
| '22 of 60' | `reports/final_numbers.json` | 1011 | written in the CP1 finish work | quotes it as wrong |
| '32 of 60' | `reports/final_numbers.json` | 743 | written in the CP1 finish work | quotes it as wrong |
| '32 of 60' | `reports/final_numbers.json` | 1012 | written in the CP1 finish work | quotes it as wrong |
| '142 cases' | `reports/final_numbers.json` | 645 | written in the CP1 finish work | quotes it as wrong |
| '142 cases' | `reports/final_numbers.json` | 750 | written in the CP1 finish work | quotes it as wrong |
| '142 cases' | `reports/final_numbers.json` | 757 | written in the CP1 finish work | quotes it as wrong |
| '142 cases' | `reports/final_numbers.json` | 1013 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `reports/final_numbers.json` | 652 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `reports/final_numbers.json` | 659 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `reports/final_numbers.json` | 666 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `reports/final_numbers.json` | 764 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `reports/final_numbers.json` | 771 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `reports/final_numbers.json` | 778 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `reports/final_numbers.json` | 827 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `reports/final_numbers.json` | 1014 | written in the CP1 finish work | quotes it as wrong |
| '50-minute window' | `reports/final_numbers.json` | 785 | written in the CP1 finish work | quotes it as wrong |
| '50-minute window' | `reports/final_numbers.json` | 1015 | written in the CP1 finish work | quotes it as wrong |
| quiet-attack demo score 87.8 | `reports/final_numbers.json` | 792 | written in the CP1 finish work | quotes it as wrong |
| quiet-attack demo score 87.8 | `reports/final_numbers.json` | 1016 | written in the CP1 finish work | quotes it as wrong |
| quiet-attack demo score 85.6 | `reports/final_numbers.json` | 799 | written in the CP1 finish work | quotes it as wrong |
| quiet-attack demo score 85.6 | `reports/final_numbers.json` | 1017 | written in the CP1 finish work | quotes it as wrong |
| voice ROC-AUC 0.952 | `reports/final_numbers.json` | 806 | written in the CP1 finish work | quotes it as wrong |
| voice ROC-AUC 0.952 | `reports/final_numbers.json` | 1018 | written in the CP1 finish work | quotes it as wrong |
| '19 routes' | `reports/final_numbers.json` | 673 | written in the CP1 finish work | quotes it as wrong |
| '19 routes' | `reports/final_numbers.json` | 680 | written in the CP1 finish work | quotes it as wrong |
| '19 routes' | `reports/final_numbers.json` | 813 | written in the CP1 finish work | quotes it as wrong |
| '19 routes' | `reports/final_numbers.json` | 820 | written in the CP1 finish work | quotes it as wrong |
| '19 routes' | `reports/final_numbers.json` | 1019 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `reports/final_run/comparison_metrics.json` | 41 | written in the CP1 finish work | written by code: a different measured value with the same digits, not the retired claim |
| F1 0.991 (TRAINING_REPORT.md) | `reports/final_run/email_metrics_plain.json` | 198 | written in the CP1 finish work | written by code: a different measured value with the same digits, not the retired claim |
| SMS F1 0.926 (Review-2 deck) | `reports/final_run/log_comparison.txt` | 2 | written in the CP1 finish work | written by code: a different measured value with the same digits, not the retired claim |
| F1 0.991 (TRAINING_REPORT.md) | `reports/final_run/log_email_plain.txt` | 16 | written in the CP1 finish work | written by code: a different measured value with the same digits, not the retired claim |
| SMS F1 0.926 (Review-2 deck) | `reports/final_run/log_url.txt` | 10 | written in the CP1 finish work | written by code: a different measured value with the same digits, not the retired claim |
| email F1 0.947 (Review-2 deck) | `reports/final_run/results.md` | 28 | written in the CP1 finish work | written by code: a different measured value with the same digits, not the retired claim |
| F1 0.991 (TRAINING_REPORT.md) | `reports/final_run/results.md` | 62 | written in the CP1 finish work | written by code: a different measured value with the same digits, not the retired claim |
| SMS F1 0.926 (Review-2 deck) | `reports/final_run/run_all_log.txt` | 58 | written in the CP1 finish work | written by code: a different measured value with the same digits, not the retired claim |
| SMS F1 0.926 (Review-2 deck) | `reports/final_run/run_all_log.txt` | 91 | written in the CP1 finish work | written by code: a different measured value with the same digits, not the retired claim |
| F1 0.991 (TRAINING_REPORT.md) | `reports/final_run/run_all_log.txt` | 17 | written in the CP1 finish work | written by code: a different measured value with the same digits, not the retired claim |
| SMS F1 0.926 (Review-2 deck) | `reports/final_run/url_metrics.json` | 193 | written in the CP1 finish work | written by code: a different measured value with the same digits, not the retired claim |
| email F1 0.947 (Review-2 deck) | `reports/final_run_check.md` | 238 | written in the CP1 finish work | written by code: a different measured value with the same digits, not the retired claim |
| SMS F1 0.926 (Review-2 deck) | `reports/final_run_check.md` | 538 | written in the CP1 finish work | written by code: a different measured value with the same digits, not the retired claim |
| F1 0.991 (TRAINING_REPORT.md) | `reports/final_run_check.md` | 419 | written in the CP1 finish work | written by code: a different measured value with the same digits, not the retired claim |
| email F1 0.947 (Review-2 deck) | `reports/log_email.txt` | 14 | received with v2, unchanged | written by code: a different measured value with the same digits, not the retired claim |
| SMS F1 0.926 (Review-2 deck) | `reports/log_url.txt` | 10 | received with v2, unchanged | written by code: a different measured value with the same digits, not the retired claim |
| email F1 0.947 (Review-2 deck) | `reports/results.md` | 28 | received with v2, regenerated since | written by code: a different measured value with the same digits, not the retired claim |
| F1 0.991 (TRAINING_REPORT.md) | `reports/results.md` | 62 | received with v2, regenerated since | written by code: a different measured value with the same digits, not the retired claim |
| SMS F1 0.926 (Review-2 deck) | `reports/url_metrics.json` | 193 | received with v2, unchanged | written by code: a different measured value with the same digits, not the retired claim |
| email F1 0.947 (Review-2 deck) | `scripts/make_final_numbers.py` | 19 | written in the CP1 finish work | quotes it as wrong |
| SMS F1 0.926 (Review-2 deck) | `scripts/make_final_numbers.py` | 19 | written in the CP1 finish work | quotes it as wrong |
| URL F1 0.960 (Review-2 deck) | `scripts/make_final_numbers.py` | 20 | written in the CP1 finish work | quotes it as wrong |
| F1 0.991 (TRAINING_REPORT.md) | `scripts/make_final_numbers.py` | 20 | written in the CP1 finish work | quotes it as wrong |
| 'linear SVM' (TRAINING_REPORT.md) | `scripts/make_final_numbers.py` | 21 | written in the CP1 finish work | quotes it as wrong |
| '460 campaigns' | `scripts/make_final_numbers.py` | 21 | written in the CP1 finish work | quotes it as wrong |
| '460 campaigns' | `scripts/make_final_numbers.py` | 21 | written in the CP1 finish work | quotes it as wrong |
| '80.0% -> 84.5%' | `scripts/make_final_numbers.py` | 22 | written in the CP1 finish work | quotes it as wrong |
| '22 of 60' | `scripts/make_final_numbers.py` | 22 | written in the CP1 finish work | quotes it as wrong |
| '32 of 60' | `scripts/make_final_numbers.py` | 22 | written in the CP1 finish work | quotes it as wrong |
| '142 cases' | `scripts/make_final_numbers.py` | 23 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `scripts/make_final_numbers.py` | 23 | written in the CP1 finish work | quotes it as wrong |
| '30-minute window' | `scripts/make_final_numbers.py` | 352 | written in the CP1 finish work | quotes it as wrong |
| '50-minute window' | `scripts/make_final_numbers.py` | 24 | written in the CP1 finish work | quotes it as wrong |
| quiet-attack demo score 87.8 | `scripts/make_final_numbers.py` | 24 | written in the CP1 finish work | quotes it as wrong |
| quiet-attack demo score 85.6 | `scripts/make_final_numbers.py` | 25 | written in the CP1 finish work | quotes it as wrong |
| voice ROC-AUC 0.952 | `scripts/make_final_numbers.py` | 25 | written in the CP1 finish work | quotes it as wrong |
| '19 routes' | `scripts/make_final_numbers.py` | 25 | written in the CP1 finish work | quotes it as wrong |
