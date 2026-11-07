# CP1 detectors - training results

Every number below is produced by the scripts in `src/` from public data, on held-out rows. Nothing is hand-typed. Positive class = *not benign* (spam / phishing / fraud / smishing / malicious URL).

## 1. What is trained

| Model | Type | Training data (after cleaning + de-duplication) | Used live? |
|---|---|---|---|
| Email | TF-IDF 1-2-grams (numbers masked, vocabulary limited to terms seen in >=2 corpora) + logistic regression | 72,431 emails: CEAS_08 34,294; Enron 28,917; FraudEmail 9,220 | yes |
| SMS | 3-class (ham / spam / smishing) word + character TF-IDF + logistic regression | LSDST: 5,789 messages (ham 4,829, spam 433, smishing 527) | yes |
| URL | character 3-5-gram hashing + TF-IDF + 3 domain-popularity flags + logistic regression, raw URL string in | 260,000 URLs (15.1% labelled bad) + 12,000 constructed login URLs on popular domains | yes |
| URL (benchmark) | gradient boosting on 111 pre-computed features | 87,197 rows | no - 13 features need DNS/WHOIS/SSL/Google lookups |
| Correlation | gradient boosting on bundle features (per-channel scores, shared identity, time span), applied inside a time window (default 60 min) | 24,000 SIMULATED bundles built from real held-out messages | yes (`POST /correlate`) |
| Voice, video | not trained | no accessible training data | no |

## 2. Per-channel results (held-out data)

### Email

| Evaluation | n | Precision | Recall | F1 | False-positive rate | ROC-AUC | Note |
|---|---|---|---|---|---|---|---|
| Pooled random test (final model) | 7,244 | 99.0% | 98.6% | 98.8% | 1.0% | 0.999 | 95% CI F1 98.5%-99.0% |
|   of which CEAS_08 | 3,430 | 99.2% | 99.7% | 99.5% | 0.8% | 1.000 |  |
|   of which Enron | 2,892 | 99.4% | 97.3% | 98.4% | 0.5% | 0.999 |  |
|   of which FraudEmail | 922 | 96.7% | 98.3% | 97.5% | 2.8% | 0.998 |  |
| **Leave-one-corpus-out** (train on two corpora, test on the third) | | | | | | | |
|   held-out CEAS_08 | 34,294 | 77.8% | 96.5% | 86.1% | 27.9% | 0.943 |  |
|   held-out Enron | 28,917 | 97.2% | 60.6% | 74.7% | 1.8% | 0.947 |  |
|   held-out FraudEmail | 9,220 | 77.6% | 95.5% | 85.7% | 22.3% | 0.964 |  |
| Baseline: plain pipeline (no masking / vocabulary filter) | | | | | | | |
|   pooled random test | 7,499 | 99.1% | 99.2% | 99.2% | 0.9% | 1.000 |  |
|   held-out CEAS_08 | 35,742 | 74.3% | 99.1% | 84.9% | 37.0% | 0.961 |  |
|   held-out Enron | 29,997 | 95.5% | 61.3% | 74.7% | 2.7% | 0.935 |  |
|   held-out FraudEmail | 9,244 | 78.1% | 98.2% | 87.0% | 22.5% | 0.980 |  |

Average over the three held-out corpora: final F1 82.1% / AUC 0.951; plain F1 82.2% / AUC 0.959. No measurable cross-corpus gain from the robust variant. It is deployed because it no longer relies on years and numbers, which identify a corpus.

### SMS

| Evaluation | n | Precision | Recall | F1 | False-positive rate | ROC-AUC | Note |
|---|---|---|---|---|---|---|---|
| Smishing vs everything else (20% test) | 1,158 | 90.7% | 83.8% | 87.1% | 0.9% | 0.985 | 95% CI F1 82.3%-91.7% |
| Spam-or-smishing vs ham (20% test) | 1,158 | 99.5% | 96.9% | 98.2% | 0.1% | 0.996 | 95% CI F1 96.7%-99.3% |
| Smishing vs rest, 5-fold out-of-fold (all data) | 5,789 | 91.9% | 90.5% | 91.2% | 0.8% | 0.990 |  |
| External set, spam-or-smishing vs ham (texts not in training) | 65,280 | 95.9% | 74.7% | 84.0% | 2.2% | 0.977 | different collection; domain-shift check |

3-class macro-F1 on the test split: 89.7%. Per class: ham P 99.3% / R 100.0% (n=966); spam P 81.8% / R 82.8% (n=87); smishing P 90.7% / R 83.8% (n=105).

### URL

| Evaluation | n | Precision | Recall | F1 | False-positive rate | ROC-AUC | Note |
|---|---|---|---|---|---|---|---|
| String model, host-grouped test (final) | 55,183 | 96.1% | 85.4% | 90.4% | 0.6% | 0.985 | 95% CI F1 90.0%-90.9% |
| Feature benchmark, gradient boosting, all features | 17,440 | 95.4% | 95.4% | 95.4% | 2.5% | 0.994 | random split; offline only |
| Feature benchmark, gradient boosting, lexical-only features | 17,440 | 92.6% | 89.1% | 90.8% | 3.8% | 0.981 | 98 features |
| Feature benchmark, random forest, all features | 17,440 | 95.2% | 95.4% | 95.3% | 2.6% | 0.994 |  |

**Fixing false alarms on login pages** - same host-grouped split, same settings, three variants:

| Variant | F1 | ROC-AUC | False alarms on login URLs of 1,000 held-out popular domains | Detection of 2,000 brand-impersonation probes | Recall on bad URLs hosted on top-10k domains |
|---|---|---|---|---|---|
| (a) n-grams only (first version) | 90.3% | 0.991 | 92.2% | 99.4% | 49.9% (n=381) |
| (b) + domain-popularity flags | 90.7% | 0.985 | 68.8% | 99.4% | 33.3% (n=381) |
| (c) + login URLs on popular domains (final) | 90.4% | 0.985 | 0.0% | 95.3% | 30.7% (n=381) |

The login URLs and brand-impersonation probes are *constructed* (path and host templates in `src/url_features.py`), not real traffic. The popularity list has 10,000 domains; 39.0% of the dataset's good URLs and 3.0% of its bad URLs sit on one, so the flags are a strong signal in this data.

### Correlation model (simulated bundles)

| Evaluation | n | Precision | Recall | F1 | False-positive rate | ROC-AUC | Note |
|---|---|---|---|---|---|---|---|
| Single-channel: alert if any event >= 0.5 | 12,000 | 87.1% | 95.4% | 91.0% | 14.0% | 0.975 | AUC of max score 0.9749 |
| Correlation model at 0.5, whole bundle, no window (see the window table below for the deployed engine) | 12,000 | 96.8% | 93.3% | 95.0% | 3.1% | 0.988 |  |
| Correlation model at the single-channel false-positive rate | 12,000 | 87.2% | 97.4% | 92.0% | 14.1% | 0.988 | threshold set on validation bundles |
|   same, link + timing features removed | 12,000 | 86.9% | 97.2% | 91.7% | 14.5% | 0.985 | AUC 0.9852 |

Campaigns where every event scores below 0.5 (missed by all single-channel filters): 26 of the linked attacks (0.7%); the correlation model catches 42.3% of them, 34.6% without link and timing features.

Share of bundles flagged, by bundle type (single-channel / correlation model at matched false-positive rate): attack_linked 99.3% / 99.2%; attack_single 89.3% / 97.6%; benign_linked 15.5% / 2.8%; benign_unlinked 13.0% / 21.4%; mixed_unlinked 89.8% / 91.5%.

**This is a simulation.** Bundles are built from real held-out messages scored by the real detectors, but the bundle structure is assumed:

- bundle mix: attack_linked 30%, attack_single 10%, mixed_unlinked 10%, benign_linked 20%, benign_unlinked 30%
- label: 1 if any event in the bundle is truly malicious (attack_linked, attack_single, mixed_unlinked), else 0
- attack linked: 2-3 malicious events on different channels, shared identity, gaps ~ Exponential(mean 15 min); each event's identity observed with prob 0.85
- benign linked: 2-3 benign events on different channels, shared identity, gaps Exponential with mean 30 min (50%) or 6 h (50%)
- unlinked bundles: events with distinct identities, times uniform over 72 h; with prob 0.08 a spurious shared identity is added
- scores: each event gets the real held-out score of a randomly drawn real message of the right class and channel

### Correlation engine with the time window (same simulated test bundles, alert line 0.5)

| Evaluation | n | Precision | Recall | F1 | False-positive rate | ROC-AUC | Note |
|---|---|---|---|---|---|---|---|
| Single-channel: alert if any event >= 0.5 | 12,000 | 87.1% | 95.4% | 91.0% | 14.0% | 0.975 |  |
| Correlation model on the whole bundle (rows above) | 12,000 | 96.8% | 93.3% | 95.0% | 3.1% | 0.988 | no time limit; a lone event is scored by the model |
| Engine without a window | 12,000 | 96.6% | 93.3% | 94.9% | 3.2% | 0.986 | a lone event = its detector score |
| Engine, window 15 min | 12,000 | 88.0% | 95.2% | 91.5% | 12.8% | 0.977 |  |
| Engine, window 30 min | 12,000 | 88.6% | 95.1% | 91.8% | 12.0% | 0.978 |  |
| Engine, window 60 min (default) | 12,000 | 89.4% | 94.9% | 92.1% | 11.1% | 0.979 |  |
| Engine, window 120 min | 12,000 | 90.3% | 94.8% | 92.5% | 10.0% | 0.981 |  |
| Engine, window 240 min | 12,000 | 91.4% | 94.7% | 93.0% | 8.8% | 0.982 |  |
| Engine, window 1440 min | 12,000 | 95.2% | 93.9% | 94.6% | 4.6% | 0.985 |  |

Share of simulated bundles whose events all fit in one 60-minute window: attack_linked 95.6%; attack_single 100.0%; benign_linked 40.8%; benign_unlinked 30.8%; mixed_unlinked 2.3%.

Share of bundles flagged at 0.5, by type (single-channel / whole-bundle model / engine with the 60-minute window): attack_linked 99.3% / 98.7% / 98.7%; attack_single 89.3% / 89.5% / 89.3%; benign_linked 15.5% / 1.1% / 8.4%; benign_unlinked 13.0% / 4.4% / 12.8%; mixed_unlinked 89.8% / 80.9% / 89.1%.

Campaigns where every event scores below 0.5: 26; flagged by the whole-bundle model 19.2%, by the engine with the window 19.2%.

The 60-minute window and the single-event rule were fixed before this evaluation was run. The other window sizes are shown for information and were not used to pick anything. The model itself was not retrained.

### R3-09: correlation against the baselines (SIMULATED bundles, alert line 0.5)

| Method | n | Precision | Recall | F1 (95% CI) | False-positive rate (95% CI) | Simulated campaigns every filter misses, flagged |
|---|---|---|---|---|---|---|
| Single-channel: alert if any event >= 0.5 | 12,000 | 87.1% | 95.4% | 91.0% (90.5%-91.5%) | 14.0% (13.1%-14.8%) | 0.0% |
| Parallel multi-channel: fusion without link and timing features, whole bundle | 12,000 | 97.0% | 92.6% | 94.8% (94.3%-95.1%) | 2.8% (2.4%-3.3%) | 15.4% |
| Correlation model on the whole bundle (pools up to 72 h) | 12,000 | 96.8% | 93.3% | 95.0% (94.7%-95.4%) | 3.1% (2.7%-3.5%) | 19.2% |
| Deployed engine: 60-minute windows (what the API does) | 12,000 | 89.4% | 94.9% | 92.1% (91.6%-92.6%) | 11.1% (10.3%-11.8%) | 19.2% |
| Patent noisy-OR campaign score | – | – | – | – | – | not evaluated: the owner decided on 7 Nov 2026 that the patent will be written from this build; the old draft's noisy-OR method and its generated numbers are not used |

SIMULATED bundles (12,000 test bundles; events are real held-out messages, links are constructed). Parallel multi-channel = the same fusion recipe trained without link and timing features (src/eval_comparison.py). Real bundles: blocked on R2-10: 0 real bundles collected.

## 3. How to read these numbers

- **Pooled email scores are flattering.** The leave-one-corpus-out rows are the honest estimate: ranking stays fairly good (AUC 0.94-0.96) but a 0.5 threshold does not transfer. False-positive rates on unseen corpora: CEAS_08 27.9%, Enron 1.8%, FraudEmail 22.3%; recall: CEAS_08 96.5%, Enron 60.6%, FraudEmail 95.5%.
- **Email models partly learn corpus fingerprints.** Fingerprint-like terms among the 60 strongest features - plain: `enron`, `vince`, `opensuse`, `2008`, `2007`, `louise`, `2010`, `uai`, `2001`, `perl`, `2009`, `python`, `2004`, `2005`; final: `vince`, `louise`, `tony`, `python`, `houston`.
- **The URL fix has a price.** False alarms on login pages of popular domains fell from 92.2% to 0.0%, overall F1 stayed at 90.4%, but detection of brand-impersonation probes went from 99.4% to 95.3% and recall on bad URLs hosted on popular domains from 49.9% to 30.7%. The login test shares path templates with the training URLs, so it shows generalisation to new domains, not to new path styles.
- **Correlation: most of the gain comes from combining scores, not from link and timing evidence.** AUC 0.9749 (max score) -> 0.9852 (learned combination) -> 0.9878 (with link and timing). The detectors already catch nearly every attack in the pools, so little is left for correlation to find. Real multi-channel data is needed before claiming more.
- **The time window is not part of the trained model.** The API applies it on top (events further apart than the window are not combined or linked; a lone event is judged by its detector). In the simulation 95.6% of linked attack bundles fit in one 60-minute window, which is why that value is the default. **The window costs score on the simulation:** inside it the engine has F1 92.1% and false-positive rate 11.1%; without a window 94.9% and 3.2%; single-channel alerting 91.0% and 14.0%. The simulation's unlinked bundles hold events up to 72 hours apart and are labelled as a whole, so pooling them helps there, and the window stops that pooling. Read the default-window row as the cautious estimate of what correlation adds. The simulation cannot settle the window, so do not pick it from this table; the real value has to come from real bundles: `refit_fusion.py` suggests one from your coordinated test cases.
- **SMS has few smishing examples** (105 in the test split), hence the wide confidence intervals.

## 4. Hand-written probes (not an evaluation)

| Channel | Truth | Score | Input |
|---|---|---|---|
| url | legit | 0.24 | https://www.paypal.com/signin |
| url | legit | 0.05 | https://www.amazon.in/gp/your-account |
| url | legit | 0.00 | https://accounts.google.com/signin |
| url | legit | 0.00 | https://en.wikipedia.org/wiki/Phishing |
| url | legit | 0.99 | https://docs.google.com/document/d/1AbCdEf/edit |
| url | malicious | 1.00 | http://paypal-secure-login.verify-account.xyz/signin |
| url | malicious | 0.99 | https://secure-appleid.apple.com.account-verify.ml/login |
| url | malicious | 1.00 | http://sbi-kyc-update.top/verify-now.php |
| url | malicious | 1.00 | http://192.168.4.7/login/index.php |
| sms | legit | 0.84 | Your package will arrive tomorrow between 10 and 2. Track it at https://www.fede |
| sms | legit | 0.00 | Hey, can we move our project meeting to 4 pm tomorrow? |
| sms | malicious | 1.00 | Dear customer, your SBI account will be blocked today. Update your KYC now at ht |
| email | legit | 0.00 | Thanks for confirming. I wrote up the notes from yesterday. Call me tomorrow if  |
| email | malicious | 1.00 | Dear customer, your bank account has been suspended. Verify your password within |

Legitimate inputs scoring high (url Google Docs link, sms courier tracking message) are known false positives: legitimate cloud-document links and transactional SMS are under-represented as negatives in the public data.

## 5. Known limitations (state these in the review)

1. **Email labels are 'unwanted / fraudulent', not strictly phishing.** Corpora used: CEAS_08 (spam + phishing mix), Enron-Spam, a Nigerian-fraud corpus. Three retrain attempts that added Nazario (real phishing), SpamAssassin, Ling-Spam and legitimate transactional mail all failed the adoption rule (reports/candidates/), so the deployed model still uses these three corpora. Earlier text, kept for the record: Nazario (real phishing emails), SpamAssassin and Ling are not in this run; they are on GitHub and can be added (README, 'Retrain from scratch').
2. **URL login-page fix is partial.** It works for the 10,000 most popular domains; login pages on unknown small sites are still likely to be flagged, and phishing hosted on popular domains is caught less often (section 3).
3. **Known false positives:** legitimate Google Docs links and courier tracking SMS (section 4).
4. **Thresholds are not portable across sources** (email, section 3). The 0.5 operating point was not re-validated on any new environment.
5. **The correlation model is trained on simulated bundles.** Its numbers describe the simulation, not field performance. The API adds a time window (default 60 minutes, `window_minutes` per request) and judges a lone event by its detector; both came after training, so the model was not retrained, and the window value has to come from real bundles. Refit and evaluate on the Review-2 test-case set.
6. **No real-traffic or time-split evaluation.** All corpora are static public collections.
7. **Voice and video detectors are not trained** (no accessible data).

## 6. Reproduce

```
pip install -r requirements.txt
bash download_data.sh      # public GitHub sources only
bash run_all.sh            # trains everything, rewrites reports/
uvicorn api:app --port 8000
```
