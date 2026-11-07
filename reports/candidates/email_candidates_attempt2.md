# Email candidate, attempt 2 (Phase 3.1)

Written by `src/eval_email_attempt2.py`. Its rule was fixed in the script before it ran:

> the same data and training as C1 (today's cleaner + Nazario, SpamAssassin, Ling; C chosen on validation in attempt 1). ONLY the alert line moves:   t = the lowest line at or above 0.5 at which C2, scoring the LEGITIMATE SpamAssassin and Ling-Spam emails with models that never saw that corpus,       raises no more false alarms than the v2 recipe (v2's three corpora, today's cleaner) raises on the same emails. The line is applied as an intercept shift (intercept - logit(t)), so a score of 0.5 from the shifted model means t from the unshifted one and the API's single 0.5 line stays. t is chosen on those two corpora only: the honest metric (CEAS_08, Enron, FraudEmail held out), the workbook emails and the demo cases are never used to set it; they are only checked afterwards, under the same adoption rule as attempt 1.

## The alert line

- Calibration set: 6,499 legitimate emails from SpamAssassin, LingSpam, each scored by a model that never saw its corpus.
- False alarms there: v2 recipe 5.8%; attempt 2 at 0.5 7.3%; attempt 2 at the chosen line 5.7%.
- Chosen line t = **0.62** (applied as an intercept shift, so the API keeps its 0.5 line).

## Held-out corpora at the chosen line

| Corpus held out | Attempt 2 |
|---|---|
| CEAS_08 | F1 94.1% (P 92.1%, R 96.1%, FPR 8.3%) |
| Enron | F1 83.8% (P 93.8%, R 75.7%, FPR 5.0%) |
| FraudEmail | F1 88.9% (P 82.2%, R 96.9%, FPR 17.0%) |
| Nazario | recall 61.8% (n=4,914) |
| SpamAssassin | F1 89.9% (P 83.8%, R 97.0%, FPR 7.8%) |
| LingSpam | F1 86.4% (P 88.5%, R 84.5%, FPR 2.1%) |

Honest metric (mean F1 over held-out CEAS_08, Enron, FraudEmail): attempt 2 **88.9%** (95% interval 88.7% to 89.2%); v2's 95% interval 81.9% to 82.6%.

## Workbook emails (hand-written, not a test set; never trained on, never used to set the line)

| Check | live v2 model | attempt 2 |
|---|---|---|
| EML-01 standard phishing | 63.6% | 81.8% |
| EML-02 standard legitimate | 100.0% | 90.9% |
| EML-03 hard phishing | 66.7% | 66.7% |
| EML-03 hard legitimate | 66.7% | 66.7% |
| D-10 emails right (E-L08, E-H06, E-H04, E-L06) | E-L08, E-H06, E-L06 | E-H06, E-L06 |
| D-17 emails right (E-P03, E-P06, E-P07, E-P09, E-H01) | none | E-P03, E-P06 |

## Demo cases (hand-written): alert outcome

| Case | live | attempt 2 |
|---|---|---|
| TC-01 | 0.998 (alert) | 1.000 (alert) |
| TC-02 | 1.000 (alert) | 1.000 (alert) |
| TC-03 | CANNOT_ASSESS | CANNOT_ASSESS |
| TC-04 | 1.000 (alert) | 1.000 (alert) |
| TC-05 | 0.000 (no alert) | 0.000 (no alert) |
| TC-06 | 0.595 (alert) | 0.590 (alert) |
| TC-07 | 0.451 (no alert) | 0.601 (alert) |
| TC-08 | 1.000 (alert) | 1.000 (alert) |

## Adoption rule

- (a) honest metric not worse than v2's beyond its 95% interval: **True** (attempt 2 mean held-out F1 0.8894 vs v2 95% interval [0.8187, 0.8257])
- (b) the target defects' cases improve (D-10, D-17): **False**
- (c) TC-01 to TC-08 keep their alert outcome: **False**
- (d) every test passes: checked after adoption by running the tests

**Decision: keep v2's model; attempt 2 is a negative result (second failed attempt: the team decides next, per the brief).**
