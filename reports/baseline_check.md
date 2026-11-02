# Baseline check: v2 reproduced from scratch (Phase 0.7)

Written by `scripts/compare_reports.py` on 2026-11-02T11:05:43+05:30. Every value below is read from the metrics files; nothing is typed.

Fresh `download_data.sh` and `run_all.sh` on tag `v2-baseline`, in a scratch git worktree outside this folder, compared with the reports v2 shipped with. The 'Review-3' column is the figure `CP1_FINISH_TASK.md` section 1.2 says v2's reports should show.

Machine: Windows-11-10.0.26200-SP0, Python 3.13.0, AMD64 Family 25 Model 80 Stepping 0, AuthenticAMD.

## Data sources

| File | Bytes | SHA-256 | Download |
|---|---|---|---|
| `CEAS_08.csv` | 67,902,056 | `22375e7d5f5a8229dbe987914ee9b3705656c590038662a7df6054629b376074` | ok |
| `enron_spam_data.csv` | 51,690,056 | `009c86359b5bd6ec142a9b9ca85075ec864fd8c7c1c378c9a430e9427d0f7d57` | unpacked from an archive |
| `enron_spam_data.zip` | 15,642,124 | `e994ad3c09fd7528b397e1f921742da5dd59f19695bc25cdb3617eb3ded17634` | ok |
| `fraud_email.csv` | 15,940,304 | `b37e3f56ddcb13076f3f18d883f9199b8f90610ffb243d76dbb44e4ff3038c61` | unpacked from an archive |
| `fraud_repo.zip` | 11,263,555 | `ca59d02e242401939b26884046ab7b8e9817972c5ace156a1d746cfe583113a3` | ok |
| `opendns_top10k.txt` | 135,644 | `aba7a11689d0d46c927f012952af795c85d735b39831dea32236eb22b2fb4044` | ok |
| `smish/hcphap_lsdst.csv` | 595,987 | `649844f1c62a6b27e145eaf17a65f7010c56c390e11a794ea8329993a05ba71e` | ok |
| `smish/shaghayegh_combined.csv` | 8,749,929 | `4dc1311965acb80b9b97536db5afdbe874a1e2175143d3b145e32caf9bb81a8d` | ok |
| `sms.tsv` | 477,907 | `7d039a24a6083ed9ef0f806ebad56bbb976e3aeb8de05669173bfdc4996c239d` | ok |
| `url_features_full.csv` | 25,067,193 | `87da36a20c8c1a9d13db5899514071907179c0fe790dc2ea4f0811957d68745d` | ok |
| `url_strings.csv` | 22,774,334 | `3243f054f5205e352f7a9adc2d7b993d516acd4ad17cb032b91c989138e34808` | ok |

Every source in `download_data.sh` downloaded.

## Review-3 figures

| Figure | Review-3 | v2 reports | v2 = Review-3 | re-run | re-run = v2 |
|---|---|---|---|---|---|
| Email F1, mean of 3 leave-one-corpus-out runs (honest) | 82.2% | 82.2% | yes | 82.2% | yes |
| Email F1, pooled random split (flattering) | 98.8% | 98.8% | yes | 98.8% | yes |
| SMS smishing-vs-rest F1 (honest) | 87.1% | 87.1% | yes | 87.1% | yes |
| SMS smishing-vs-rest F1, 95% CI low | 82.3% | 82.3% | yes | 82.3% | yes |
| SMS smishing-vs-rest F1, 95% CI high | 91.7% | 91.7% | yes | 91.7% | yes |
| SMS spam-or-smishing F1 (flattering) | 98.2% | 98.2% | yes | 98.2% | yes |
| URL F1, host-grouped (honest) | 90.4% | 90.4% | yes | 90.4% | yes |
| URL false alarms on login URLs of 1,000 held-out popular domains | 0.0% | 0.0% | yes | 0.0% | yes |
| URL recall on bad URLs on top-10k domains, before the fix | 49.9% | 49.9% | yes | 49.9% | yes |
| URL recall on bad URLs on top-10k domains, final | 30.7% | 30.7% | yes | 30.7% | yes |
| URL F1, offline feature benchmark (flattering) | 95.4% | 95.4% | yes | 95.4% | yes |
| Correlation (simulated): Single-channel, precision | 87.0% | 87.0% | yes | 87.0% | yes |
| Correlation (simulated): Single-channel, recall | 95.3% | 95.3% | yes | 95.3% | yes |
| Correlation (simulated): Single-channel, f1 | 91.0% | 91.0% | yes | 91.0% | yes |
| Correlation (simulated): Single-channel, false positive rate | 14.1% | 14.1% | yes | 14.1% | yes |
| Correlation (simulated): Whole-bundle model, precision | 97.0% | 97.0% | yes | 97.0% | yes |
| Correlation (simulated): Whole-bundle model, recall | 92.9% | 92.9% | yes | 92.9% | yes |
| Correlation (simulated): Whole-bundle model, f1 | 94.9% | 94.9% | yes | 94.9% | yes |
| Correlation (simulated): Whole-bundle model, false positive rate | 2.8% | 2.8% | yes | 2.8% | yes |
| Correlation (simulated): Engine, no window, precision | 96.8% | 96.8% | yes | 96.8% | yes |
| Correlation (simulated): Engine, no window, recall | 93.0% | 93.0% | yes | 93.0% | yes |
| Correlation (simulated): Engine, no window, f1 | 94.8% | 94.8% | yes | 94.8% | yes |
| Correlation (simulated): Engine, no window, false positive rate | 3.0% | 3.0% | yes | 3.0% | yes |
| Correlation (simulated): Engine, 60-minute window, precision | 89.4% | 89.4% | yes | 89.4% | yes |
| Correlation (simulated): Engine, 60-minute window, recall | 94.9% | 94.9% | yes | 94.9% | yes |
| Correlation (simulated): Engine, 60-minute window, f1 | 92.0% | 92.0% | yes | 92.0% | yes |
| Correlation (simulated): Engine, 60-minute window, false positive rate | 11.1% | 11.1% | yes | 11.1% | yes |
| Simulated linked attacks with every event below 0.5 (count) | 27 | 27 | yes | 27 | yes |
| Simulated linked attacks with every event below 0.5 (share) | 0.8% | 0.8% | yes | 0.8% | yes |
| Of those, flagged by the 60-minute engine | 18.5% | 18.5% | yes | 18.5% | yes |
| Simulated linked attack bundles that fit in 60 minutes | 95.6% | 95.6% | yes | 95.6% | yes |

v2's reports match 31 of 31 Review-3 figures as printed. The re-run matches v2 on 31 of 31 figures to 3 decimals.

## Every value in every metrics file

| File | Values compared | Identical | Different | Only in v2 | Only in re-run |
|---|---|---|---|---|---|
| `email_metrics.json` | 236 | 236 | 0 | 0 | 0 |
| `email_metrics_plain.json` | 247 | 128 | 119 | 0 | 0 |
| `fusion_metrics.json` | 83 | 83 | 0 | 0 | 0 |
| `probe_results.json` | 14 | 9 | 5 | 0 | 0 |
| `sms_metrics.json` | 111 | 111 | 0 | 0 | 0 |
| `url_metrics.json` | 162 | 155 | 7 | 0 | 0 |
| `window_metrics.json` | 166 | 166 | 0 | 0 | 0 |

### Values that differ (131)

| File | Key | v2 | re-run |
|---|---|---|---|
| `email_metrics_plain.json` | `validation_by_C.1.precision` | 0.982 | 0.9823 |
| `email_metrics_plain.json` | `validation_by_C.1.recall` | 0.986 | 0.9857 |
| `email_metrics_plain.json` | `validation_by_C.1.false_positive_rate` | 0.0177 | 0.0175 |
| `email_metrics_plain.json` | `validation_by_C.1.tn` | 3714 | 3715 |
| `email_metrics_plain.json` | `validation_by_C.1.fp` | 67 | 66 |
| `email_metrics_plain.json` | `validation_by_C.1.fn` | 52 | 53 |
| `email_metrics_plain.json` | `validation_by_C.1.tp` | 3665 | 3664 |
| `email_metrics_plain.json` | `pooled_test.accuracy` | 0.9919 | 0.9917 |
| `email_metrics_plain.json` | `pooled_test.precision` | 0.9901 | 0.9898 |
| `email_metrics_plain.json` | `pooled_test.f1` | 0.9918 | 0.9917 |
| `email_metrics_plain.json` | `pooled_test.false_positive_rate` | 0.0098 | 0.01 |
| `email_metrics_plain.json` | `pooled_test.tn` | 3746 | 3745 |
| `email_metrics_plain.json` | `pooled_test.fp` | 37 | 38 |
| `email_metrics_plain.json` | `pooled_test_ci95.precision.0` | 0.9868 | 0.9866 |
| `email_metrics_plain.json` | `pooled_test_ci95.precision.1` | 0.9929 | 0.9926 |
| `email_metrics_plain.json` | `pooled_test_ci95.f1.0` | 0.9896 | 0.9894 |
| `email_metrics_plain.json` | `pooled_test_ci95.f1.1` | 0.9938 | 0.9936 |
| `email_metrics_plain.json` | `pooled_test_at_1pct_fpr.threshold` | 0.5262 | 0.5228 |
| `email_metrics_plain.json` | `pooled_test_at_1pct_fpr.accuracy` | 0.9919 | 0.9916 |
| `email_metrics_plain.json` | `pooled_test_at_1pct_fpr.precision` | 0.9911 | 0.9906 |
| `email_metrics_plain.json` | `pooled_test_at_1pct_fpr.f1` | 0.9918 | 0.9915 |
| `email_metrics_plain.json` | `pooled_test_at_1pct_fpr.false_positive_rate` | 0.0087 | 0.0093 |
| `email_metrics_plain.json` | `pooled_test_at_1pct_fpr.tn` | 3750 | 3748 |
| `email_metrics_plain.json` | `pooled_test_at_1pct_fpr.fp` | 33 | 35 |
| `email_metrics_plain.json` | `pooled_test_per_source.Enron.accuracy` | 0.9917 | 0.9913 |
| `email_metrics_plain.json` | `pooled_test_per_source.Enron.precision` | 0.9951 | 0.9944 |
| `email_metrics_plain.json` | `pooled_test_per_source.Enron.f1` | 0.9913 | 0.991 |
| `email_metrics_plain.json` | `pooled_test_per_source.Enron.false_positive_rate` | 0.0045 | 0.0051 |
| `email_metrics_plain.json` | `pooled_test_per_source.Enron.tn` | 1547 | 1546 |
| `email_metrics_plain.json` | `pooled_test_per_source.Enron.fp` | 7 | 8 |
| `email_metrics_plain.json` | `pooled_test_per_source.Enron.pr_auc` | 0.9997 | 0.9996 |
| `email_metrics_plain.json` | `pooled_test_per_source.FraudEmail.roc_auc` | 0.9984 | 0.9985 |
| `email_metrics_plain.json` | `baseline_complement_nb_test.roc_auc` | 0.9992 | 0.9993 |
| `email_metrics_plain.json` | `leave_one_corpus_out.CEAS_08.accuracy` | 0.8182 | 0.8184 |
| `email_metrics_plain.json` | `leave_one_corpus_out.CEAS_08.precision` | 0.7438 | 0.744 |
| `email_metrics_plain.json` | `leave_one_corpus_out.CEAS_08.recall` | 0.9909 | 0.991 |
| `email_metrics_plain.json` | `leave_one_corpus_out.CEAS_08.f1` | 0.8498 | 0.8499 |
| `email_metrics_plain.json` | `leave_one_corpus_out.CEAS_08.false_positive_rate` | 0.3681 | 0.3678 |
| `email_metrics_plain.json` | `leave_one_corpus_out.CEAS_08.tn` | 10867 | 10872 |
| `email_metrics_plain.json` | `leave_one_corpus_out.CEAS_08.fp` | 6330 | 6325 |
| `email_metrics_plain.json` | `leave_one_corpus_out.CEAS_08.fn` | 168 | 167 |
| `email_metrics_plain.json` | `leave_one_corpus_out.CEAS_08.tp` | 18377 | 18378 |
| `email_metrics_plain.json` | `leave_one_corpus_out.CEAS_08.pr_auc` | 0.9565 | 0.9564 |
| `email_metrics_plain.json` | `leave_one_corpus_out.Enron.accuracy` | 0.8038 | 0.8004 |
| `email_metrics_plain.json` | `leave_one_corpus_out.Enron.precision` | 0.955 | 0.9541 |
| `email_metrics_plain.json` | `leave_one_corpus_out.Enron.recall` | 0.6225 | 0.6156 |
| `email_metrics_plain.json` | `leave_one_corpus_out.Enron.f1` | 0.7537 | 0.7484 |
| `email_metrics_plain.json` | `leave_one_corpus_out.Enron.false_positive_rate` | 0.0273 | 0.0276 |
| `email_metrics_plain.json` | `leave_one_corpus_out.Enron.tn` | 15109 | 15105 |
| `email_metrics_plain.json` | `leave_one_corpus_out.Enron.fp` | 424 | 428 |
| `email_metrics_plain.json` | `leave_one_corpus_out.Enron.fn` | 5460 | 5560 |
| `email_metrics_plain.json` | `leave_one_corpus_out.Enron.tp` | 9004 | 8904 |
| `email_metrics_plain.json` | `leave_one_corpus_out.Enron.roc_auc` | 0.9363 | 0.9354 |
| `email_metrics_plain.json` | `leave_one_corpus_out.Enron.pr_auc` | 0.9349 | 0.9338 |
| `email_metrics_plain.json` | `leave_one_corpus_out.FraudEmail.accuracy` | 0.8694 | 0.8686 |
| `email_metrics_plain.json` | `leave_one_corpus_out.FraudEmail.precision` | 0.7822 | 0.7812 |
| `email_metrics_plain.json` | `leave_one_corpus_out.FraudEmail.f1` | 0.8711 | 0.8704 |
| `email_metrics_plain.json` | `leave_one_corpus_out.FraudEmail.false_positive_rate` | 0.2229 | 0.2243 |
| `email_metrics_plain.json` | `leave_one_corpus_out.FraudEmail.tn` | 3956 | 3949 |
| `email_metrics_plain.json` | `leave_one_corpus_out.FraudEmail.fp` | 1135 | 1142 |
| `email_metrics_plain.json` | `leave_one_corpus_out.FraudEmail.pr_auc` | 0.9785 | 0.9784 |
| `email_metrics_plain.json` | `top_terms_malicious.0.1` | 15.389 | 15.388 |
| `email_metrics_plain.json` | `top_terms_malicious.1.1` | 12.901 | 12.88 |
| `email_metrics_plain.json` | `top_terms_malicious.2.1` | 10.568 | 10.554 |
| `email_metrics_plain.json` | `top_terms_malicious.3.1` | 10.344 | 10.303 |
| `email_metrics_plain.json` | `top_terms_malicious.4.1` | 10.338 | 10.302 |
| `email_metrics_plain.json` | `top_terms_malicious.5.1` | 9.287 | 9.304 |
| `email_metrics_plain.json` | `top_terms_malicious.6.1` | 8.91 | 8.951 |
| `email_metrics_plain.json` | `top_terms_malicious.7.1` | 8.236 | 8.225 |
| `email_metrics_plain.json` | `top_terms_malicious.8.1` | 7.838 | 7.817 |
| `email_metrics_plain.json` | `top_terms_malicious.9.1` | 7.75 | 7.747 |
| `email_metrics_plain.json` | `top_terms_malicious.10.1` | 7.676 | 7.667 |
| `email_metrics_plain.json` | `top_terms_malicious.11.1` | 7.59 | 7.614 |
| `email_metrics_plain.json` | `top_terms_malicious.12.1` | 7.401 | 7.409 |
| `email_metrics_plain.json` | `top_terms_malicious.13.1` | 7.326 | 7.339 |
| `email_metrics_plain.json` | `top_terms_malicious.14.1` | 7.137 | 7.133 |
| `email_metrics_plain.json` | `top_terms_malicious.15.1` | 6.973 | 6.99 |
| `email_metrics_plain.json` | `top_terms_malicious.16.1` | 6.681 | 6.689 |
| `email_metrics_plain.json` | `top_terms_malicious.17.1` | 6.647 | 6.638 |
| `email_metrics_plain.json` | `top_terms_malicious.18.1` | 6.558 | 6.555 |
| `email_metrics_plain.json` | `top_terms_malicious.19.1` | 6.517 | 6.521 |
| `email_metrics_plain.json` | `top_terms_malicious.20.1` | 6.491 | 6.493 |
| `email_metrics_plain.json` | `top_terms_malicious.21.1` | 6.481 | 6.483 |
| `email_metrics_plain.json` | `top_terms_malicious.22.1` | 6.475 | 6.447 |
| `email_metrics_plain.json` | `top_terms_malicious.24.1` | 6.372 | 6.37 |
| `email_metrics_plain.json` | `top_terms_malicious.25.1` | 6.253 | 6.273 |
| `email_metrics_plain.json` | `top_terms_malicious.26.1` | 6.16 | 6.155 |
| `email_metrics_plain.json` | `top_terms_malicious.27.1` | 5.983 | 5.973 |
| `email_metrics_plain.json` | `top_terms_malicious.28.1` | 5.884 | 5.896 |
| `email_metrics_plain.json` | `top_terms_malicious.29.1` | 5.619 | 5.617 |
| `email_metrics_plain.json` | `top_terms_legit.0.1` | -17.379 | -17.367 |
| `email_metrics_plain.json` | `top_terms_legit.1.1` | -12.151 | -12.193 |
| `email_metrics_plain.json` | `top_terms_legit.2.1` | -11.952 | -12.078 |
| `email_metrics_plain.json` | `top_terms_legit.3.1` | -10.065 | -10.049 |
| `email_metrics_plain.json` | `top_terms_legit.4.1` | -9.862 | -9.836 |
| `email_metrics_plain.json` | `top_terms_legit.5.1` | -9.604 | -9.614 |
| `email_metrics_plain.json` | `top_terms_legit.6.1` | -9.55 | -9.58 |
| `email_metrics_plain.json` | `top_terms_legit.7.1` | -9.418 | -9.482 |
| `email_metrics_plain.json` | `top_terms_legit.8.1` | -9.393 | -9.4 |
| `email_metrics_plain.json` | `top_terms_legit.9.1` | -9.042 | -9.081 |
| `email_metrics_plain.json` | `top_terms_legit.10.1` | -8.59 | -8.619 |
| `email_metrics_plain.json` | `top_terms_legit.11.1` | -8.542 | -8.544 |
| `email_metrics_plain.json` | `top_terms_legit.12.1` | -8.267 | -8.279 |
| `email_metrics_plain.json` | `top_terms_legit.13.1` | -7.532 | -7.539 |
| `email_metrics_plain.json` | `top_terms_legit.14.1` | -7.53 | -7.531 |
| `email_metrics_plain.json` | `top_terms_legit.15.1` | -7.332 | -7.334 |
| `email_metrics_plain.json` | `top_terms_legit.16.1` | -7.299 | -7.301 |
| `email_metrics_plain.json` | `top_terms_legit.17.1` | -7.266 | -7.29 |
| `email_metrics_plain.json` | `top_terms_legit.18.1` | -7.153 | -7.156 |
| `email_metrics_plain.json` | `top_terms_legit.19.1` | -7.088 | -7.115 |
| `email_metrics_plain.json` | `top_terms_legit.21.1` | -6.795 | -6.794 |
| `email_metrics_plain.json` | `top_terms_legit.22.1` | -6.783 | -6.77 |
| `email_metrics_plain.json` | `top_terms_legit.23.1` | -6.724 | -6.731 |
| `email_metrics_plain.json` | `top_terms_legit.24.1` | -6.659 | -6.668 |
| `email_metrics_plain.json` | `top_terms_legit.25.1` | -6.524 | -6.567 |
| `email_metrics_plain.json` | `top_terms_legit.26.1` | -6.29 | -6.33 |
| `email_metrics_plain.json` | `top_terms_legit.27.1` | -6.286 | -6.299 |
| `email_metrics_plain.json` | `top_terms_legit.28.1` | -6.272 | -6.267 |
| `email_metrics_plain.json` | `top_terms_legit.29.1` | -6.144 | -6.169 |
| `probe_results.json` | `0.score` | 0.2353 | 0.2358 |
| `probe_results.json` | `1.score` | 0.0507 | 0.0508 |
| `probe_results.json` | `4.score` | 0.9877 | 0.9878 |
| `probe_results.json` | `6.score` | 0.9875 | 0.9877 |
| `probe_results.json` | `8.score` | 0.9972 | 0.9973 |
| `url_metrics.json` | `string_model.ablation.b_plus_popularity_flags.grouped_test.accuracy` | 0.9745 | 0.9746 |
| `url_metrics.json` | `string_model.ablation.b_plus_popularity_flags.grouped_test.recall` | 0.8573 | 0.8575 |
| `url_metrics.json` | `string_model.ablation.b_plus_popularity_flags.grouped_test.f1` | 0.9066 | 0.9067 |
| `url_metrics.json` | `string_model.ablation.b_plus_popularity_flags.grouped_test.fn` | 1135 | 1134 |
| `url_metrics.json` | `string_model.ablation.b_plus_popularity_flags.grouped_test.tp` | 6821 | 6822 |
| `url_metrics.json` | `string_model.ablation.b_plus_popularity_flags.false_positive_rate_on_login_urls_of_1000_held_out_popular_domains` | 0.6877 | 0.688 |
| `url_metrics.json` | `string_model.sanity_probes_NOT_an_evaluation.https://www.paypal.com/signin` | 0.235 | 0.236 |

## Model files

| File | v2 SHA-256 | re-run SHA-256 | Same bytes |
|---|---|---|---|
| `email_model.joblib` | `b8f8ea9f4434fa11...` | `aab1793be001ca34...` | no |
| `email_model_plain.joblib` | `6d4bbced6ecd7158...` | `110a20351c38b8ac...` | no |
| `fusion_model.joblib` | `179294b428e3ab52...` | `63c4763a1112b303...` | no |
| `sms_model.joblib` | `34f5ad3b99326dd6...` | `5a4f1d2bb69a5314...` | no |
| `url_features_all_features.joblib` | `c70a746d0b22df78...` | `e877dbc4881f700d...` | no |
| `url_features_lexical_only.joblib` | `e4eb1ac5379dea6c...` | `58052731be8ad9e7...` | no |
| `url_string_model.joblib` | `466e710ab3f212ab...` | `670623455f507105...` | no |

Pickled models can differ in bytes while making identical predictions (pickle stores object ids and dict order). The metrics above are the comparison that matters.

## End of the run log

```
engine_default_window_at_0.5               {'precision': 0.894, 'recall': 0.9486, 'f1': 0.9205, 'false_positive_rate': 0.1109, 'roc_auc': 0.9789}
by window: {'15': 0.9138, '30': 0.9172, '60': 0.9205, '120': 0.925, '240': 0.9301, '1440': 0.9446}
fit in one window: {np.str_('attack_linked'): 0.9558, np.str_('attack_single'): 1.0, np.str_('benign_linked'): 0.4078, np.str_('benign_unlinked'): 0.3082, np.str_('mixed_unlinked'): 0.0233}
flag rates: {'single_channel': {np.str_('attack_linked'): 0.9924, np.str_('attack_single'): 0.893, np.str_('benign_linked'): 0.1568, np.str_('benign_unlinked'): 0.1306, np.str_('mixed_unlinked'): 0.8966}, 'whole_bundle_model': {np.str_('attack_linked'): 0.9866, np.str_('attack_single'): 0.8897, np.str_('benign_linked'): 0.0109, np.str_('benign_unlinked'): 0.0391, np.str_('mixed_unlinked'): 0.7933}, 'engine_default_window': {np.str_('attack_linked'): 0.9866, np.str_('attack_single'): 0.893, np.str_('benign_linked'): 0.0824, np.str_('benign_unlinked'): 0.1295, np.str_('mixed_unlinked'): 0.8906}}
hard campaigns: {'n': 27, 'caught_whole_bundle_model_at_0.5': 0.1852, 'caught_engine_default_window_at_0.5': 0.1852}
wrote results.md 14387 chars
```

## How it was run

- Worktree: `git worktree add --detach <scratch folder> v2-baseline`, outside this project folder. Commit `3cc60b8`.
- Commands, in Git Bash with the project venv's Python first on PATH: `bash download_data.sh`, then `bash run_all.sh`.
- Started Mon Nov  2 10:35:44 IST 2026; finished Mon Nov  2 10:53:42 IST 2026. Wall time: `17m57.571s`.
- `download_data.sh` fetched every source (table above).

## Findings

1. **The Review-3 figures reproduce.** Every figure in the table above is the same to 3 decimals after a fresh download and retrain on this laptop. The deployed email, SMS, URL and correlation models give the same metrics.
2. **The URL benchmark step finished here.** `PROJECT_STATE.md` section 5 says it did not finish in the earlier environment, so `url_metrics.json` had never been re-run. It now has been: the deployed string model and its host-grouped figures are unchanged.
3. **Two non-deployed baselines moved slightly.** The plain email pipeline (`email_metrics_plain.json`, a comparison baseline, not served) differs on two held-out corpora, its pooled split and its top-term weights, and ablation variant (b) of the URL model differs by one URL. Exact values are in the list of differing values. A likely cause for the email baseline: `email_model_plain.joblib` and its metrics are dated 10 Oct, and `src/common.py` (the text cleaner they use) is dated 11 Oct, so the plain run was made with an earlier cleaner. Neither baseline is quoted as a result.
4. **Five hand-written URL probe scores moved in the fourth decimal** (`probe_results.json`, values in the list below). The retrained URL model is not bit-identical, but its test metrics are the same to 4 decimals. Probes are not an evaluation.
5. **Windows writes CRLF line endings.** Every regenerated report has CRLF endings, so git shows whole files as changed. Ignoring line endings, the changes are the ones listed above. `.gitattributes` now stores `.md`, `.json`, `.txt` and `.csv` with LF.
6. **The smoke test cannot reach its second half on Windows.** With the pools in place it still stopped: `tests/make_synthetic_testcases.py` writes its CSV in the system code page (cp1252), and the pool texts hold characters outside it. With `encoding="utf-8"` added to that one `open()` call (scratch worktree only), the smoke test gave 24 PASS, 1 SKIP and 0 FAIL, ending `ALL PASSED`. The skipped check needs a spreadsheet program to recalculate formulas. The fix goes into the repo in Phase 1.
7. **No data source is dead.** Nothing needed replacing.

## What was not compared

- Model files differ in bytes (table above). That is expected for pickles; the metrics are the comparison.
- The re-run's models stay in the scratch worktree. The live models in `models/` are v2's, unchanged (`reports/model_manifest.json`).

