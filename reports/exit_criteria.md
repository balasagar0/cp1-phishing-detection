# Exit criteria (R2-11)

Written by `scripts/exit_criteria.py` on 2026-11-07T16:49:26+05:30 from the run on `cp1-rc1-2-g50c3228-dirty`. Targets: read from the team workbook's Summary sheet and equal to the constants (6 values checked). No target was moved after a result.

| # | Criterion | Target | Current | Status | Detail |
|---|---|---|---|---|---|
| 1 | All High-priority test cases executed | 0 not run | 0 not run | **Met** | every High case ran |
| 2 | Non-model test cases: pass rate | 95% or more | 95.4% (83 pass, 4 fail) | **Met** | N/A and Not run cases are left out, as the workbook's formula does |
| 3 | All 12 sample groups meet their targets | 12 of 12 | 8 of 12 | **Not met** | email Legitimate Hard case 67% (target 70%); email Legitimate Standard 100% (target 90%); email Phishing Hard case 67% (target 70%); email Phishing Standard 64% (target 90%); sms Legitimate Hard case 50% (target 70%); sms Legitimate Standard 92% (target 90%); sms Phishing Hard case 75% (target 70%); sms Phishing Standard 100% (target 90%); url Legitimate Hard case 80% (target 70%); url Legitimate Standard 100% (target 90%); url Phishing Hard case 100% (target 70%); url Phishing Standard 100% (target 90%). Samples are hand-written, not a test set |
| 4a | Held-out metrics pass (EML-10, SMS-08, URL-10): the plan's held-out split | 3 of 3 | 3 of 3 | **Met** | the plan reads each channel's held-out split against F1 0.90: email pooled random split, SMS spam-or-smishing, URL host-grouped |
| 4b | The same 0.90 line on the honest measures | 3 of 3 | 1 of 3 | **Not met** | email: mean leave-one-corpus-out F1 82.2% (not met); SMS: smishing-vs-rest F1 87.1% (not met); URL: host-grouped F1 90.4% (met) |
| 5 | Correlation changes a verdict with real models (SYS-14) | Pass | Fail | **Not met** | S-01, S-02 and S-11 already alert on one channel; TC-06 (hand-written) is the case where correlation lifts a bundle, see reports/r2_09_evidence.md |
| 6 | Speed tests pass (NFR-01, NFR-02) | 2 of 2 | 2 of 2 | **Met** | scripts/benchmark.py over real HTTP, 100 requests each (AMD Ryzen 7 5800HS with Radeon Graphics (16 logical CPUs), 15.4 GB RAM, Windows-11-10.0.26200-SP0, Pytho |
| 7 | No open Critical or High defects | 0 | 3 | **Not met** | D-01 (High), D-09 (High), D-17 (High) |

4 of 8 rows met. Criterion 4 is shown twice, as the brief asks: the plan's own held-out split (4a) and the honest measure (4b).
