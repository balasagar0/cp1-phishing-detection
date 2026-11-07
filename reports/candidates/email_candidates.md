# Email candidate (Phase 3.1)

Written by `src/eval_email_candidates.py`. Same protocol for every row: leave-one-corpus-out, alert line 0.5.

## Held-out corpora (each trained without the corpus it is tested on)

| Corpus held out | B0 v2 recipe | B1 v2 recipe + D-11 cleaner | C1 candidate (+3 corpora) | live v2 model (never saw it) |
|---|---|---|---|---|
| CEAS_08 | F1 86.1% (P 77.7%, R 96.5%, FPR 28.0%) | F1 86.1% (P 77.8%, R 96.5%, FPR 27.9%) | F1 93.9% (P 90.9%, R 97.2%, FPR 9.9%) | – |
| Enron | F1 74.9% (P 97.1%, R 61.0%, FPR 1.8%) | F1 74.7% (P 97.2%, R 60.6%, FPR 1.8%) | F1 86.1% (P 92.0%, R 80.9%, FPR 7.0%) | – |
| FraudEmail | F1 85.7% (P 77.7%, R 95.4%, FPR 22.2%) | F1 85.7% (P 77.6%, R 95.5%, FPR 22.3%) | F1 86.4% (P 77.4%, R 97.9%, FPR 23.2%) | – |
| Nazario | – | – | recall 67.5% (n=4,914) | recall 65.5% (n=4,914) |
| SpamAssassin | – | – | F1 88.3% (P 80.4%, R 97.9%, FPR 10.0%) | F1 89.9% (P 84.2%, R 96.4%, FPR 7.6%) |
| LingSpam | – | – | F1 86.6% (P 86.1%, R 87.1%, FPR 2.7%) | F1 86.5% (P 86.5%, R 86.6%, FPR 2.6%) |

| Honest metric: mean F1 over held-out CEAS_08, Enron, FraudEmail | 95% interval |
|---|---|
| B0 v2 recipe: 82.2% | 81.9% to 82.6% |
| B1 v2 recipe + D-11 cleaner: 82.1% | 81.8% to 82.5% |
| C1 candidate: 88.8% | 88.6% to 89.1% |

B0 reproduces v2's reported leave-one-corpus-out figures: True.

## Workbook emails (hand-written, not a test set; never trained on)

| Check | live v2 model | candidate |
|---|---|---|
| EML-01 standard phishing | 63.6% | 81.8% |
| EML-02 standard legitimate | 100.0% | 90.9% |
| EML-03 hard phishing | 66.7% | 66.7% |
| EML-03 hard legitimate | 66.7% | 66.7% |
| D-10 emails right (E-L08, E-H06, E-H04, E-L06) | E-L08, E-H06, E-L06 | E-H06, E-L06 |
| D-17 emails right (E-P03, E-P06, E-P07, E-P09, E-H01) | none | E-P03, E-P06 |

## Demo cases (hand-written): alert outcome with the live model and with the candidate

| Case | live | candidate |
|---|---|---|
| TC-01 | 0.998 (alert) | 1.000 (alert) |
| TC-02 | 1.000 (alert) | 1.000 (alert) |
| TC-03 | CANNOT_ASSESS | CANNOT_ASSESS |
| TC-04 | 1.000 (alert) | 1.000 (alert) |
| TC-05 | 0.000 (no alert) | 0.000 (no alert) |
| TC-06 | 0.595 (alert) | 0.590 (alert) |
| TC-07 | 0.451 (no alert) | 0.710 (alert) |
| TC-08 | 1.000 (alert) | 1.000 (alert) |

## Adoption rule

- (a) honest metric not worse than v2's beyond its 95% interval: **True** (candidate mean held-out F1 0.888 vs v2 95% interval [0.8187, 0.8257])
- (b) the target defects' cases improve (D-10, D-17): **False**
- (c) TC-01 to TC-08 keep their alert outcome: **False**
- (d) every test passes: checked after adoption by running the tests

**Decision: keep v2's model; report the candidate as a negative result.**
