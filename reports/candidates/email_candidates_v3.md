# Email model v3 (Phase 3.1, third attempt)

Written by `src/eval_email_v3.py`. Its rule was fixed in the script before it ran:

> attempt 2's recipe (today's cleaner; CEAS_08, Enron, FraudEmail + Nazario, SpamAssassin, Ling-Spam; C from attempt 1; the alert line set by attempt 2's rule: no more false alarms than the v2 recipe on held-out legitimate SpamAssassin and Ling-Spam emails, applied as an intercept shift) PLUS three legitimate sources, all label 0:   GeneratedLegit  imnim/multiclass-email-classification, MIT: 2,105 emails GENERATED with GPT-3.5 (synthetic, not real messages)   Templates       Postmark and Mailgun transactional templates, MIT: real company wording, placeholders removed   OwnInbox        the account owner's own legitimate mail (receipts, bank, order, shipping, OTP and account notices), exported by them, with consent The adoption rule is unchanged: (a) honest metric (mean F1, held-out CEAS_08, Enron, FraudEmail) not worse than v2's 95% interval; (b) the D-10 and D-17 workbook cases improve and no EML group falls; (c) TC-01 to TC-08 keep their alert outcome; (d) every test passes after adoption. Reported beside the rule, not part of it: the false-alarm rate on each legitimate source held out (OwnInbox held out = real receipts the model never saw), for v3 and for v2's live model. Needs at least 100 own-inbox emails after cleaning; with fewer it stops without training. The workbook emails, the scenarios and TC-01 to TC-08 are never trained on and never used to set anything; they are only checked afterwards.

## Training data

| Source | Legitimate | Unwanted |
|---|---|---|
| CEAS_08 | 17,046 | 17,248 |
| Enron | 14,485 | 14,432 |
| FraudEmail | 5,091 | 4,129 |
| GeneratedLegit | 2,104 | 0 |
| LingSpam | 2,402 | 464 |
| Nazario | 0 | 4,914 |
| OwnInbox | 4,069 | 0 |
| SpamAssassin | 4,097 | 1,710 |
| Templates | 14 | 0 |

GeneratedLegit is synthetic (GPT-3.5). Templates are company templates with placeholders removed. OwnInbox is the account owner's own legitimate mail, used with their consent, streamed (never stored as text) and never committed.

Own-inbox stream: 4,431 messages read, 3 skipped as Spam or Trash, 0 unreadable, 28 too short, 331 exact duplicates, 4,069 used.

Privacy of this run: outbound connection attempts 0; archive byte-identical before and after: True; model file: current user only (icacls), encrypted: False. The first run (7 Nov 2026) stopped at the demo-case step: its network guard also blocked loopback, which Windows' asyncio needs. This run is the same procedure; the guard now allows loopback and still blocks and counts everything that would leave the machine.

## The alert line

False alarms on held-out legitimate SpamAssassin, LingSpam emails: v2 recipe 5.8%; v3 at 0.5 8.4%; v3 at the chosen line 5.7%. Chosen line t = **0.685** (an intercept shift, so the API keeps 0.5).

## Held-out sources at the chosen line

| Source held out | v3 |
|---|---|
| CEAS_08 | F1 93.1% (P 94.3%, R 92.0%, FPR 5.6%) |
| Enron | F1 80.9% (P 95.8%, R 70.0%, FPR 3.1%) |
| FraudEmail | F1 89.7% (P 86.2%, R 93.4%, FPR 12.1%) |
| Nazario | recall 42.1% (n=4,914) |
| SpamAssassin | F1 88.6% (P 83.5%, R 94.4%, FPR 7.8%) |
| LingSpam | F1 85.7% (P 88.1%, R 83.4%, FPR 2.2%) |
| GeneratedLegit | false-alarm rate 26.4% (n=2,104) |
| Templates | false-alarm rate 0.0% (n=14) |
| OwnInbox | false-alarm rate 61.1% (n=4,069) |

Honest metric (mean F1 over held-out CEAS_08, Enron, FraudEmail): v3 **87.9%** (95% interval 87.6% to 88.2%); v2's 95% interval 81.9% to 82.6%.

## False alarms on legitimate transactional email the model never saw (reported, not part of the rule)

| Source | n | v3 (source held out) | live v2 model |
|---|---|---|---|
| GeneratedLegit | 2,104 | 26.4% | 21.6% |
| Templates | 14 | 0.0% | 0.0% |
| OwnInbox | 4,069 | 61.1% | 23.5% |

## Workbook emails (hand-written, not a test set; never trained on, never used to set anything)

| Check | live v2 model | v3 |
|---|---|---|
| EML-01 standard phishing | 63.6% | 81.8% |
| EML-02 standard legitimate | 100.0% | 100.0% |
| EML-03 hard phishing | 66.7% | 33.3% |
| EML-03 hard legitimate | 66.7% | 66.7% |
| D-10 emails right (E-L08, E-H06, E-H04, E-L06) | E-L08, E-H06, E-L06 | E-L08, E-H06, E-L06 |
| D-17 emails right (E-P03, E-P06, E-P07, E-P09, E-H01) | none | E-P03, E-P06 |

## Demo cases (hand-written): alert outcome

| Case | live | v3 |
|---|---|---|
| TC-01 | 0.998 (alert) | 1.000 (alert) |
| TC-02 | 1.000 (alert) | 1.000 (alert) |
| TC-03 | CANNOT_ASSESS | CANNOT_ASSESS |
| TC-04 | 1.000 (alert) | 1.000 (alert) |
| TC-05 | 0.000 (no alert) | 0.000 (no alert) |
| TC-06 | 0.595 (alert) | 0.590 (alert) |
| TC-07 | 0.451 (no alert) | 0.672 (alert) |
| TC-08 | 1.000 (alert) | 1.000 (alert) |

## Adoption rule

- (a) honest metric not worse than v2's beyond its 95% interval: **True** (v3 mean held-out F1 0.8789 vs v2 95% interval [0.8187, 0.8257])
- (b) the target defects' cases improve (D-10, D-17): **False**
- (c) TC-01 to TC-08 keep their alert outcome: **False**
- (d) every test passes: checked after adoption by running the tests
- privacy: scripts/privacy_audit_email.py must pass before the model is used (PRIVACY_AND_ETHICS.md)

**Decision: keep v2's model; v3 is a negative result.**
