# R2-09: does correlation change a verdict with real scores?

Written by `scripts/make_r2_09_evidence.py` on 2026-11-02T11:54:10+05:30. Every row says what kind of evidence it is.

| Evidence | Kind | Event scores | Alerts alone? | Bundle | Correlation lifts the verdict? | Source |
|---|---|---|---|---|---|---|
| S-03 on the old build (29 Sep run) | fixed scores (55 / 52 / 58 on a 0-100 scale), rule bonus | email 55, sms 52, url 58 | best single 58.0 = SUSPICIOUS | 83.0 = HIGH RISK (bonus +25) | yes, from SUSPICIOUS to HIGH RISK, on fixed scores | team workbook, SYS-03 'Actual result' (29 Sep) |
| S-03 fixed scores through v2's engine | fixed scores (0.55 / 0.52 / 0.58) | email 0.550, sms 0.520, url 0.580 | yes (each is at or above 0.5) | 1.000 | no: with one line at 0.5 these scores already alert alone | fusion.Fusion.risk, computed here |
| TC-06: weak parcel campaign, 15 minutes | hand-written, not a test set (real detector scores) | sms 0.421, url 0.451, email 0.204 | no | 0.595 (alert; 1 window, shared dom:parcel-redelivery.info) | yes: no event alerts alone, the bundle does | POST /correlate, run here |
| TC-07: TC-06's messages 3 days apart (control) | hand-written, not a test set (real detector scores) | sms 0.421, url 0.451, email 0.204 | no | 0.451 (no alert; 3 windows, shared none) | no: stays below the line | POST /correlate, run here |
| TC-05: colleague shares an article (linked but harmless) | hand-written, not a test set (real detector scores) | sms 0.002, email 0.000, url 0.000 | no | 0.000 (no alert; 1 window, shared dom:wikipedia.org) | no: stays below the line | POST /correlate, run here |
| TC-04: KYC campaign on one domain | hand-written, not a test set (real detector scores) | sms 1.000, url 0.995, email 0.998 | yes | 1.000 (alert; 1 window, shared dom:sbi-kyc-update.top) | no: already alerts alone | POST /correlate, run here |
| Simulated linked attacks where every event is below 0.5 | SIMULATED bundles (12,000 test bundles; real held-out messages, constructed links) | 27 campaigns (0.8% of simulated linked attacks) | no (by definition) | flagged by the 60-minute engine: 18.5% (5 of 27); by the whole-bundle model: 18.5% | yes, for a minority of a small group, on simulated bundles | reports/window_metrics.json, reports/fusion_metrics.json |

**SYS-14 as the plan wrote it** (S-01, S-02, S-11 with the real models): S-01: best single alert, bundle alert (1.000); S-02: best single alert, bundle alert (1.000); S-11: best single alert, bundle alert (1.000). The detectors already alert on all three, so correlation cannot raise the verdict.

**Reading.** The only case with real detector scores where correlation lifts a verdict is TC-06, which is hand-written; its control TC-07 (same messages, days apart) does not lift, and the harmless linked case TC-05 stays low. On simulated bundles, correlation flags a minority of the small group of campaigns that every single-channel filter misses. Neither is a field result: real bundles (R2-10) are needed before claiming more.
