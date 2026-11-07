# Reproducibility check

Written by `scripts/compare_reports.py` on 2026-11-07T15:43:32+05:30. Every value below is read from the metrics files; nothing is typed.

Machine: Windows-11-10.0.26200-SP0, Python 3.13.0, AMD64 Family 25 Model 80 Stepping 0, AuthenticAMD.

## Data sources

| File | Bytes | SHA-256 | Download |
|---|---|---|---|
| `CEAS_08.csv` | 67,902,056 | `22375e7d5f5a8229dbe987914ee9b3705656c590038662a7df6054629b376074` | ok |
| `email_extra/lingspam/lingspam_public.tar.gz` | 11,564,714 | `e3a0bb61dff2f1e47c368d1c376c27f79319cd600a8784ea3872e4b77d22c148` | not used by this run (Phase 3 candidate corpora) |
| `email_extra/nazario/20051114.mbox` | 4,071,556 | `928cbf1c394d01d0b398ded8dc7cbd94dd4ce9cb0d4efdecd12696338c247926` | not used by this run (Phase 3 candidate corpora) |
| `email_extra/nazario/LICENSE.txt` | 18,657 | `9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411` | not used by this run (Phase 3 candidate corpora) |
| `email_extra/nazario/phishing-2015` | 8,815,568 | `7523e62a5e6e4ee8134ab8b1a628e423097a7779e1003b28422864aa34f1c319` | not used by this run (Phase 3 candidate corpora) |
| `email_extra/nazario/phishing-2016` | 12,578,274 | `42393e4d686193bfb879d1608c23fd4d3b698ccd4d73f0e1d2276ba709718483` | not used by this run (Phase 3 candidate corpora) |
| `email_extra/nazario/phishing-2017` | 11,352,450 | `110fba876b38b44035bf065788952674bc68a7b6879c345a515a9ac844b1d704` | not used by this run (Phase 3 candidate corpora) |
| `email_extra/nazario/phishing-2018` | 8,775,701 | `83f49cf2a76c7b29b205d22d8778e46848e36af0f15ee1df126a543696acd48d` | not used by this run (Phase 3 candidate corpora) |
| `email_extra/nazario/phishing-2019` | 5,211,476 | `cab39d6fcb38cf80cdaabb3e6ffd1222777e2fcaac7e8480321b7f729c2e3c0e` | not used by this run (Phase 3 candidate corpora) |
| `email_extra/nazario/phishing-2020` | 5,826,445 | `99e20bf25f5e8556d37103f2c8140cd75181a62d3df91df8acf9d9aece9f08bb` | not used by this run (Phase 3 candidate corpora) |
| `email_extra/nazario/phishing-2021` | 2,719,946 | `636707cff42245d1482e4ae8a2c03369717a5e06bf9d1a0f4ec5dcd846661cee` | not used by this run (Phase 3 candidate corpora) |
| `email_extra/nazario/phishing-2022` | 4,775,954 | `a6291e2cb990204766fce425423949b403cce4ae6a660fc8d08812e40a063fa7` | not used by this run (Phase 3 candidate corpora) |
| `email_extra/nazario/phishing-2023` | 7,763,704 | `5007f1c1dc91b15e93e988afa3a1cf402e15c88f765d3057be8bfec50dae1fe8` | not used by this run (Phase 3 candidate corpora) |
| `email_extra/nazario/phishing-2024` | 15,457,816 | `60afa40a2757170093a2bde31ec9cda4e54d33992203ce04bfbbc86d2e5e5b99` | not used by this run (Phase 3 candidate corpora) |
| `email_extra/nazario/phishing-2025` | 18,769,863 | `f1fa7e0fe35c9a16f36d9aa20ade7e1d3908d1d0c1d917b8c53c8aa799ec1c8f` | not used by this run (Phase 3 candidate corpora) |
| `email_extra/nazario/phishing0.mbox` | 3,119,972 | `6184b0a34ed8cbbb252676e21c1eab9eac5fa4be89c61e30cc9954ebbb25d848` | not used by this run (Phase 3 candidate corpora) |
| `email_extra/nazario/phishing1.mbox` | 4,191,770 | `99f02474a11086408a5ce6d11ef38823f003c6611a4312c31fbee96773eeba28` | not used by this run (Phase 3 candidate corpora) |
| `email_extra/nazario/phishing2.mbox` | 10,420,294 | `5113277984eae759a5ff958ccf408b542441ce033a49b923ab3b0f324075e6bd` | not used by this run (Phase 3 candidate corpora) |
| `email_extra/nazario/README.txt` | 961 | `4589b63a4149bff0b65e82c2110baaebee36e5d9219009a31cc78bb6ab597fab` | not used by this run (Phase 3 candidate corpora) |
| `email_extra/spamassassin/20030228_easy_ham.tar.bz2` | 1,612,216 | `2b7b65904bcfcc31d2b5f51946f2d261370b257402cbbd62930b46ab83367438` | not used by this run (Phase 3 candidate corpora) |
| `email_extra/spamassassin/20030228_easy_ham_2.tar.bz2` | 1,077,892 | `b4bd3dc5ae5b40f38e99a0e41ad7d16b428b56e818e3a6ffa07330d62004dd38` | not used by this run (Phase 3 candidate corpora) |
| `email_extra/spamassassin/20030228_hard_ham.tar.bz2` | 1,029,898 | `ce2ce67880643dbde65ea7f85bffbfe4417349c4bd80b6b0de56262ae6b0a9c9` | not used by this run (Phase 3 candidate corpora) |
| `email_extra/spamassassin/20030228_spam.tar.bz2` | 1,183,768 | `c08debc32413804949a866be45ef78195cec2cbafd1da744ed76cdb860589743` | not used by this run (Phase 3 candidate corpora) |
| `email_extra/spamassassin/20050311_spam_2.tar.bz2` | 2,059,029 | `44280a0e28bf7645b2279e8e42659271ad82c6f40bf8d364dbda7f1df344a765` | not used by this run (Phase 3 candidate corpora) |
| `email_extra/spamassassin/readme.html` | 4,566 | `9f8cc0c8be6f32b25226d3ece26da775a6e008581b8fb061a679e3acee6b64be` | not used by this run (Phase 3 candidate corpora) |
| `email_legit/generated/dataset_creation.py.txt` | 7,878 | `3850b452fcd3047830c1de6c2065fc57b9bc17d52868d7da472c1cf6bf21180c` | not used by this run (Phase 3 candidate corpora) |
| `email_legit/generated/email_dataset.json` | 1,140,713 | `1093f1a3191e52b715ae728609b2e15bac71ba2573814a968856c43b009a0b30` | not used by this run (Phase 3 candidate corpora) |
| `email_legit/generated/README.md` | 738 | `de69b0adb28d0117105547af1f761bd2220aecab635f4dad429e53e69865c329` | not used by this run (Phase 3 candidate corpora) |
| `email_legit/templates/mailgun-templates.zip` | 182,447 | `c70b1c08163f6c06bf31556fba9f211ef1090a939b77ebfb1a756ab9860aae6e` | not used by this run (Phase 3 candidate corpora) |
| `email_legit/templates/postmark-templates.zip` | 418,647 | `3440ef5880d77a02164a2dbab4a27bddf99a0dc81c926d72c76d703d24ee53e1` | not used by this run (Phase 3 candidate corpora) |
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

The account owner's private mail export (`email_own/`) is left out of this table on purpose. No run in `run_all.sh` reads it.

Every source in `download_data.sh` downloaded.

## Review-3 figures

| Figure | Review-3 | v2 reports | v2 = Review-3 | Final run on cp1-rc1 | Final run on cp1-rc1 = v2 |
|---|---|---|---|---|---|
| Email F1, mean of 3 leave-one-corpus-out runs (honest) | 82.2% | 82.2% | yes | 82.1% | **no** |
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
| Correlation (simulated): Single-channel, precision | 87.0% | 87.0% | yes | 87.1% | **no** |
| Correlation (simulated): Single-channel, recall | 95.3% | 95.3% | yes | 95.4% | **no** |
| Correlation (simulated): Single-channel, f1 | 91.0% | 91.0% | yes | 91.0% | **no** |
| Correlation (simulated): Single-channel, false positive rate | 14.1% | 14.1% | yes | 14.0% | **no** |
| Correlation (simulated): Whole-bundle model, precision | 97.0% | 97.0% | yes | 96.8% | **no** |
| Correlation (simulated): Whole-bundle model, recall | 92.9% | 92.9% | yes | 93.3% | **no** |
| Correlation (simulated): Whole-bundle model, f1 | 94.9% | 94.9% | yes | 95.0% | **no** |
| Correlation (simulated): Whole-bundle model, false positive rate | 2.8% | 2.8% | yes | 3.1% | **no** |
| Correlation (simulated): Engine, no window, precision | 96.8% | 96.8% | yes | 96.6% | **no** |
| Correlation (simulated): Engine, no window, recall | 93.0% | 93.0% | yes | 93.3% | **no** |
| Correlation (simulated): Engine, no window, f1 | 94.8% | 94.8% | yes | 94.9% | yes |
| Correlation (simulated): Engine, no window, false positive rate | 3.0% | 3.0% | yes | 3.2% | **no** |
| Correlation (simulated): Engine, 60-minute window, precision | 89.4% | 89.4% | yes | 89.4% | yes |
| Correlation (simulated): Engine, 60-minute window, recall | 94.9% | 94.9% | yes | 94.9% | yes |
| Correlation (simulated): Engine, 60-minute window, f1 | 92.0% | 92.0% | yes | 92.1% | **no** |
| Correlation (simulated): Engine, 60-minute window, false positive rate | 11.1% | 11.1% | yes | 11.1% | yes |
| Simulated linked attacks with every event below 0.5 (count) | 27 | 27 | yes | 26 | **no** |
| Simulated linked attacks with every event below 0.5 (share) | 0.8% | 0.8% | yes | 0.7% | **no** |
| Of those, flagged by the 60-minute engine | 18.5% | 18.5% | yes | 19.2% | **no** |
| Simulated linked attack bundles that fit in 60 minutes | 95.6% | 95.6% | yes | 95.6% | yes |

v2's reports match 31 of 31 Review-3 figures as printed. The Final run on cp1-rc1 matches v2 on 15 of 31 figures to 3 decimals.

## Every value in every metrics file

| File | Values compared | Identical | Different | Only in v2 | Only in Final run on cp1-rc1 |
|---|---|---|---|---|---|
| `comparison_metrics.json` | 0 | 0 | 0 | 0 | 79 |
| `defect_status.json` | 0 | 0 | 0 | 0 | 0 |
| `email_metrics.json` | 236 | 41 | 195 | 0 | 0 |
| `email_metrics_plain.json` | 247 | 48 | 199 | 0 | 0 |
| `final_cases_results.json` | 0 | 0 | 0 | 0 | 128 |
| `fusion_metrics.json` | 83 | 20 | 63 | 0 | 0 |
| `offline_check.json` | 0 | 0 | 0 | 0 | 0 |
| `probe_results.json` | 14 | 9 | 5 | 0 | 0 |
| `r2_09_evidence.json` | 0 | 0 | 0 | 0 | 0 |
| `regression_baseline.json` | 0 | 0 | 0 | 0 | 128 |
| `sms_metrics.json` | 111 | 111 | 0 | 0 | 0 |
| `ui_checks.json` | 0 | 0 | 0 | 0 | 0 |
| `url_metrics.json` | 162 | 155 | 7 | 0 | 0 |
| `window_metrics.json` | 166 | 41 | 125 | 0 | 0 |

### Values that differ (594)

| File | Key | v2 | Final run on cp1-rc1 |
|---|---|---|---|
| `email_metrics.json` | `data.dedupe.rows_before` | 83043 | 83042 |
| `email_metrics.json` | `data.dedupe.rows_after` | 72428 | 72431 |
| `email_metrics.json` | `data.counts.FraudEmail.1` | 4126 | 4129 |
| `email_metrics.json` | `data.split.train` | 57942 | 57944 |
| `email_metrics.json` | `data.split.test` | 7243 | 7244 |
| `email_metrics.json` | `data.kept_terms` | 49011 | 49052 |
| `email_metrics.json` | `validation_by_C.1.positives` | 3581 | 3582 |
| `email_metrics.json` | `validation_by_C.1.accuracy` | 0.9845 | 0.9847 |
| `email_metrics.json` | `validation_by_C.1.precision` | 0.9838 | 0.9798 |
| `email_metrics.json` | `validation_by_C.1.recall` | 0.9849 | 0.9894 |
| `email_metrics.json` | `validation_by_C.1.f1` | 0.9844 | 0.9846 |
| `email_metrics.json` | `validation_by_C.1.false_positive_rate` | 0.0158 | 0.0199 |
| `email_metrics.json` | `validation_by_C.1.tn` | 3604 | 3588 |
| `email_metrics.json` | `validation_by_C.1.fp` | 58 | 73 |
| `email_metrics.json` | `validation_by_C.1.fn` | 54 | 38 |
| `email_metrics.json` | `validation_by_C.1.tp` | 3527 | 3544 |
| `email_metrics.json` | `validation_by_C.1.roc_auc` | 0.9984 | 0.9985 |
| `email_metrics.json` | `validation_by_C.4.positives` | 3581 | 3582 |
| `email_metrics.json` | `validation_by_C.4.accuracy` | 0.9874 | 0.9873 |
| `email_metrics.json` | `validation_by_C.4.precision` | 0.988 | 0.9845 |
| `email_metrics.json` | `validation_by_C.4.recall` | 0.9866 | 0.9899 |
| `email_metrics.json` | `validation_by_C.4.f1` | 0.9873 | 0.9872 |
| `email_metrics.json` | `validation_by_C.4.false_positive_rate` | 0.0117 | 0.0153 |
| `email_metrics.json` | `validation_by_C.4.tn` | 3619 | 3605 |
| `email_metrics.json` | `validation_by_C.4.fp` | 43 | 56 |
| `email_metrics.json` | `validation_by_C.4.fn` | 48 | 36 |
| `email_metrics.json` | `validation_by_C.4.tp` | 3533 | 3546 |
| `email_metrics.json` | `validation_by_C.4.roc_auc` | 0.9989 | 0.999 |
| `email_metrics.json` | `validation_by_C.4.pr_auc` | 0.999 | 0.9991 |
| `email_metrics.json` | `validation_by_C.16.positives` | 3581 | 3582 |
| `email_metrics.json` | `validation_by_C.16.accuracy` | 0.9888 | 0.9881 |
| `email_metrics.json` | `validation_by_C.16.precision` | 0.9907 | 0.9872 |
| `email_metrics.json` | `validation_by_C.16.recall` | 0.9866 | 0.9888 |
| `email_metrics.json` | `validation_by_C.16.f1` | 0.9887 | 0.988 |
| `email_metrics.json` | `validation_by_C.16.false_positive_rate` | 0.009 | 0.0126 |
| `email_metrics.json` | `validation_by_C.16.tn` | 3629 | 3615 |
| `email_metrics.json` | `validation_by_C.16.fp` | 33 | 46 |
| `email_metrics.json` | `validation_by_C.16.fn` | 48 | 40 |
| `email_metrics.json` | `validation_by_C.16.tp` | 3533 | 3542 |
| `email_metrics.json` | `validation_by_C.16.roc_auc` | 0.999 | 0.9992 |
| `email_metrics.json` | `validation_by_C.16.pr_auc` | 0.9991 | 0.9992 |
| `email_metrics.json` | `pooled_test.n` | 7243 | 7244 |
| `email_metrics.json` | `pooled_test.accuracy` | 0.9877 | 0.988 |
| `email_metrics.json` | `pooled_test.precision` | 0.9872 | 0.9899 |
| `email_metrics.json` | `pooled_test.recall` | 0.988 | 0.9858 |
| `email_metrics.json` | `pooled_test.f1` | 0.9876 | 0.9878 |
| `email_metrics.json` | `pooled_test.false_positive_rate` | 0.0126 | 0.0098 |
| `email_metrics.json` | `pooled_test.tn` | 3616 | 3627 |
| `email_metrics.json` | `pooled_test.fp` | 46 | 36 |
| `email_metrics.json` | `pooled_test.fn` | 43 | 51 |
| `email_metrics.json` | `pooled_test.tp` | 3538 | 3530 |
| `email_metrics.json` | `pooled_test.roc_auc` | 0.9992 | 0.999 |
| `email_metrics.json` | `pooled_test.pr_auc` | 0.9992 | 0.9991 |
| `email_metrics.json` | `pooled_test_ci95.precision.0` | 0.9831 | 0.9862 |
| `email_metrics.json` | `pooled_test_ci95.precision.1` | 0.9908 | 0.9934 |
| `email_metrics.json` | `pooled_test_ci95.recall.0` | 0.9837 | 0.9823 |
| `email_metrics.json` | `pooled_test_ci95.recall.1` | 0.9917 | 0.989 |
| `email_metrics.json` | `pooled_test_ci95.f1.0` | 0.9846 | 0.9854 |
| `email_metrics.json` | `pooled_test_ci95.f1.1` | 0.9902 | 0.99 |
| `email_metrics.json` | `pooled_test_at_1pct_fpr.n` | 7243 | 7244 |
| `email_metrics.json` | `pooled_test_at_1pct_fpr.threshold` | 0.4748 | 0.5508 |
| `email_metrics.json` | `pooled_test_at_1pct_fpr.accuracy` | 0.9876 | 0.9883 |
| `email_metrics.json` | `pooled_test_at_1pct_fpr.precision` | 0.9861 | 0.9913 |
| `email_metrics.json` | `pooled_test_at_1pct_fpr.recall` | 0.9888 | 0.9849 |
| `email_metrics.json` | `pooled_test_at_1pct_fpr.f1` | 0.9875 | 0.9881 |
| `email_metrics.json` | `pooled_test_at_1pct_fpr.false_positive_rate` | 0.0137 | 0.0085 |
| `email_metrics.json` | `pooled_test_at_1pct_fpr.tn` | 3612 | 3632 |
| `email_metrics.json` | `pooled_test_at_1pct_fpr.fp` | 50 | 31 |
| `email_metrics.json` | `pooled_test_at_1pct_fpr.fn` | 40 | 54 |
| `email_metrics.json` | `pooled_test_at_1pct_fpr.tp` | 3541 | 3527 |
| `email_metrics.json` | `pooled_test_at_1pct_fpr.roc_auc` | 0.9992 | 0.999 |
| `email_metrics.json` | `pooled_test_at_1pct_fpr.pr_auc` | 0.9992 | 0.9991 |
| `email_metrics.json` | `pooled_test_per_source.CEAS_08.accuracy` | 0.9942 | 0.9945 |
| `email_metrics.json` | `pooled_test_per_source.CEAS_08.precision` | 0.9902 | 0.9919 |
| `email_metrics.json` | `pooled_test_per_source.CEAS_08.recall` | 0.9983 | 0.9971 |
| `email_metrics.json` | `pooled_test_per_source.CEAS_08.f1` | 0.9942 | 0.9945 |
| `email_metrics.json` | `pooled_test_per_source.CEAS_08.false_positive_rate` | 0.01 | 0.0082 |
| `email_metrics.json` | `pooled_test_per_source.CEAS_08.tn` | 1688 | 1691 |
| `email_metrics.json` | `pooled_test_per_source.CEAS_08.fp` | 17 | 14 |
| `email_metrics.json` | `pooled_test_per_source.CEAS_08.fn` | 3 | 5 |
| `email_metrics.json` | `pooled_test_per_source.CEAS_08.tp` | 1722 | 1720 |
| `email_metrics.json` | `pooled_test_per_source.Enron.positives` | 1444 | 1443 |
| `email_metrics.json` | `pooled_test_per_source.Enron.accuracy` | 0.9824 | 0.9837 |
| `email_metrics.json` | `pooled_test_per_source.Enron.precision` | 0.9888 | 0.9943 |
| `email_metrics.json` | `pooled_test_per_source.Enron.recall` | 0.9758 | 0.973 |
| `email_metrics.json` | `pooled_test_per_source.Enron.f1` | 0.9822 | 0.9835 |
| `email_metrics.json` | `pooled_test_per_source.Enron.false_positive_rate` | 0.011 | 0.0055 |
| `email_metrics.json` | `pooled_test_per_source.Enron.tn` | 1432 | 1441 |
| `email_metrics.json` | `pooled_test_per_source.Enron.fp` | 16 | 8 |
| `email_metrics.json` | `pooled_test_per_source.Enron.fn` | 35 | 39 |
| `email_metrics.json` | `pooled_test_per_source.Enron.tp` | 1409 | 1404 |
| `email_metrics.json` | `pooled_test_per_source.Enron.roc_auc` | 0.9987 | 0.9985 |
| `email_metrics.json` | `pooled_test_per_source.FraudEmail.n` | 921 | 922 |
| `email_metrics.json` | `pooled_test_per_source.FraudEmail.positives` | 412 | 413 |
| `email_metrics.json` | `pooled_test_per_source.FraudEmail.accuracy` | 0.9805 | 0.9772 |
| `email_metrics.json` | `pooled_test_per_source.FraudEmail.precision` | 0.969 | 0.9667 |
| `email_metrics.json` | `pooled_test_per_source.FraudEmail.recall` | 0.9879 | 0.9831 |
| `email_metrics.json` | `pooled_test_per_source.FraudEmail.f1` | 0.9784 | 0.9748 |
| `email_metrics.json` | `pooled_test_per_source.FraudEmail.false_positive_rate` | 0.0255 | 0.0275 |
| `email_metrics.json` | `pooled_test_per_source.FraudEmail.tn` | 496 | 495 |
| `email_metrics.json` | `pooled_test_per_source.FraudEmail.fp` | 13 | 14 |
| `email_metrics.json` | `pooled_test_per_source.FraudEmail.fn` | 5 | 7 |
| `email_metrics.json` | `pooled_test_per_source.FraudEmail.tp` | 407 | 406 |
| `email_metrics.json` | `pooled_test_per_source.FraudEmail.roc_auc` | 0.9986 | 0.9978 |
| `email_metrics.json` | `pooled_test_per_source.FraudEmail.pr_auc` | 0.9982 | 0.9975 |
| `email_metrics.json` | `leave_one_corpus_out.CEAS_08.accuracy` | 0.8433 | 0.8434 |
| `email_metrics.json` | `leave_one_corpus_out.CEAS_08.precision` | 0.7774 | 0.7775 |
| `email_metrics.json` | `leave_one_corpus_out.CEAS_08.false_positive_rate` | 0.2795 | 0.2794 |
| `email_metrics.json` | `leave_one_corpus_out.CEAS_08.tn` | 12281 | 12284 |
| `email_metrics.json` | `leave_one_corpus_out.CEAS_08.fp` | 4765 | 4762 |
| `email_metrics.json` | `leave_one_corpus_out.CEAS_08.roc_auc` | 0.9419 | 0.9428 |
| `email_metrics.json` | `leave_one_corpus_out.CEAS_08.pr_auc` | 0.9344 | 0.9354 |
| `email_metrics.json` | `leave_one_corpus_out.Enron.accuracy` | 0.7964 | 0.7946 |
| `email_metrics.json` | `leave_one_corpus_out.Enron.precision` | 0.9712 | 0.9716 |
| `email_metrics.json` | `leave_one_corpus_out.Enron.recall` | 0.6101 | 0.6062 |
| `email_metrics.json` | `leave_one_corpus_out.Enron.f1` | 0.7494 | 0.7465 |
| `email_metrics.json` | `leave_one_corpus_out.Enron.false_positive_rate` | 0.018 | 0.0177 |
| `email_metrics.json` | `leave_one_corpus_out.Enron.tn` | 14224 | 14229 |
| `email_metrics.json` | `leave_one_corpus_out.Enron.fp` | 261 | 256 |
| `email_metrics.json` | `leave_one_corpus_out.Enron.fn` | 5627 | 5684 |
| `email_metrics.json` | `leave_one_corpus_out.Enron.tp` | 8805 | 8748 |
| `email_metrics.json` | `leave_one_corpus_out.Enron.roc_auc` | 0.947 | 0.9469 |
| `email_metrics.json` | `leave_one_corpus_out.Enron.pr_auc` | 0.9481 | 0.948 |
| `email_metrics.json` | `leave_one_corpus_out.FraudEmail.n` | 9217 | 9220 |
| `email_metrics.json` | `leave_one_corpus_out.FraudEmail.positives` | 4126 | 4129 |
| `email_metrics.json` | `leave_one_corpus_out.FraudEmail.accuracy` | 0.8569 | 0.8567 |
| `email_metrics.json` | `leave_one_corpus_out.FraudEmail.precision` | 0.777 | 0.7765 |
| `email_metrics.json` | `leave_one_corpus_out.FraudEmail.recall` | 0.9542 | 0.955 |
| `email_metrics.json` | `leave_one_corpus_out.FraudEmail.false_positive_rate` | 0.222 | 0.2229 |
| `email_metrics.json` | `leave_one_corpus_out.FraudEmail.tn` | 3961 | 3956 |
| `email_metrics.json` | `leave_one_corpus_out.FraudEmail.fp` | 1130 | 1135 |
| `email_metrics.json` | `leave_one_corpus_out.FraudEmail.fn` | 189 | 186 |
| `email_metrics.json` | `leave_one_corpus_out.FraudEmail.tp` | 3937 | 3943 |
| `email_metrics.json` | `leave_one_corpus_out.FraudEmail.roc_auc` | 0.9634 | 0.9636 |
| `email_metrics.json` | `leave_one_corpus_out.FraudEmail.pr_auc` | 0.9634 | 0.9636 |
| `email_metrics.json` | `top_terms_malicious.0.1` | 14.682 | 14.522 |
| `email_metrics.json` | `top_terms_malicious.1.1` | 10.884 | 10.846 |
| `email_metrics.json` | `top_terms_malicious.2.1` | 9.736 | 9.833 |
| `email_metrics.json` | `top_terms_malicious.3.1` | 9.024 | 9.302 |
| `email_metrics.json` | `top_terms_malicious.4.1` | 8.52 | 8.517 |
| `email_metrics.json` | `top_terms_malicious.5.1` | 8.472 | 8.477 |
| `email_metrics.json` | `top_terms_malicious.6.1` | 8.214 | 8.239 |
| `email_metrics.json` | `top_terms_malicious.7.1` | 8.012 | 7.914 |
| `email_metrics.json` | `top_terms_malicious.8.1` | 7.789 | 7.884 |
| `email_metrics.json` | `top_terms_malicious.9.1` | 7.734 | 7.754 |
| `email_metrics.json` | `top_terms_malicious.10.1` | 7.677 | 7.638 |
| `email_metrics.json` | `top_terms_malicious.11.1` | 7.598 | 7.585 |
| `email_metrics.json` | `top_terms_malicious.12.1` | 7.278 | 7.378 |
| `email_metrics.json` | `top_terms_malicious.13.1` | 7.27 | 7.281 |
| `email_metrics.json` | `top_terms_malicious.14.1` | 7.262 | 7.244 |
| `email_metrics.json` | `top_terms_malicious.15.1` | 7.036 | 7.01 |
| `email_metrics.json` | `top_terms_malicious.16.1` | 6.929 | 6.906 |
| `email_metrics.json` | `top_terms_malicious.17.1` | 6.62 | 6.669 |
| `email_metrics.json` | `top_terms_malicious.18.1` | 6.495 | 6.499 |
| `email_metrics.json` | `top_terms_malicious.19.1` | 6.461 | 6.45 |
| `email_metrics.json` | `top_terms_malicious.20.1` | 6.398 | 6.404 |
| `email_metrics.json` | `top_terms_malicious.21.1` | 6.369 | 6.349 |
| `email_metrics.json` | `top_terms_malicious.22.1` | 6.333 | 6.325 |
| `email_metrics.json` | `top_terms_malicious.23.1` | 6.305 | 6.115 |
| `email_metrics.json` | `top_terms_malicious.24.1` | 6.13 | 5.992 |
| `email_metrics.json` | `top_terms_malicious.25.1` | 5.922 | 5.958 |
| `email_metrics.json` | `top_terms_malicious.26.1` | 5.901 | 5.874 |
| `email_metrics.json` | `top_terms_malicious.27.1` | 5.76 | 5.774 |
| `email_metrics.json` | `top_terms_malicious.28.1` | 5.687 | 5.738 |
| `email_metrics.json` | `top_terms_malicious.29.1` | 5.648 | 5.72 |
| `email_metrics.json` | `top_terms_legit.0.1` | -12.799 | -12.832 |
| `email_metrics.json` | `top_terms_legit.1.1` | -11.234 | -11.283 |
| `email_metrics.json` | `top_terms_legit.2.1` | -10.393 | -10.372 |
| `email_metrics.json` | `top_terms_legit.3.1` | -10.324 | -10.329 |
| `email_metrics.json` | `top_terms_legit.4.1` | -9.185 | -9.215 |
| `email_metrics.json` | `top_terms_legit.5.1` | -9.168 | -9.159 |
| `email_metrics.json` | `top_terms_legit.6.1` | -8.98 | -8.962 |
| `email_metrics.json` | `top_terms_legit.7.1` | -8.737 | -8.723 |
| `email_metrics.json` | `top_terms_legit.8.1` | -8.5 | -8.562 |
| `email_metrics.json` | `top_terms_legit.9.1` | -8.238 | -8.381 |
| `email_metrics.json` | `top_terms_legit.10.1` | -8.093 | -8.162 |
| `email_metrics.json` | `top_terms_legit.11.1` | -7.834 | -8.137 |
| `email_metrics.json` | `top_terms_legit.12.1` | -7.592 | -7.553 |
| `email_metrics.json` | `top_terms_legit.13.1` | -7.539 | -7.524 |
| `email_metrics.json` | `top_terms_legit.14.1` | -7.481 | -7.307 |
| `email_metrics.json` | `top_terms_legit.15.1` | -7.076 | -7.096 |
| `email_metrics.json` | `top_terms_legit.16.1` | -7.041 | -7.081 |
| `email_metrics.json` | `top_terms_legit.17.1` | -6.957 | -7.03 |
| `email_metrics.json` | `top_terms_legit.18.1` | -6.909 | -6.944 |
| `email_metrics.json` | `top_terms_legit.19.1` | -6.834 | -6.835 |
| `email_metrics.json` | `top_terms_legit.20.1` | -6.828 | -6.82 |
| `email_metrics.json` | `top_terms_legit.21.1` | -6.8 | -6.775 |
| `email_metrics.json` | `top_terms_legit.22.1` | -6.684 | -6.722 |
| `email_metrics.json` | `top_terms_legit.23.1` | -6.682 | -6.702 |
| `email_metrics.json` | `top_terms_legit.24.1` | -6.626 | -6.698 |
| `email_metrics.json` | `top_terms_legit.25.1` | -6.576 | -6.522 |
| `email_metrics.json` | `top_terms_legit.27.1` | -6.253 | -6.29 |
| `email_metrics.json` | `top_terms_legit.28.1` | -6.196 | -6.177 |
| `email_metrics.json` | `top_terms_legit.29.1` | -5.962 | -5.939 |
| `email_metrics.json` | `loco_mean.f1` | 0.8222999999999999 | 0.8213333333333334 |
| `email_metrics_plain.json` | `data.dedupe.rows_before` | 83021 | 83020 |
| `email_metrics_plain.json` | `data.dedupe.rows_after` | 74979 | 74983 |
| `email_metrics_plain.json` | `data.counts.FraudEmail.1` | 4149 | 4153 |
| `email_metrics_plain.json` | `data.split.train` | 59983 | 59986 |
| `email_metrics_plain.json` | `data.split.test` | 7498 | 7499 |
| `email_metrics_plain.json` | `validation_by_C.1.accuracy` | 0.9841 | 0.9839 |
| `email_metrics_plain.json` | `validation_by_C.1.precision` | 0.982 | 0.9815 |
| `email_metrics_plain.json` | `validation_by_C.1.f1` | 0.984 | 0.9838 |
| `email_metrics_plain.json` | `validation_by_C.1.false_positive_rate` | 0.0177 | 0.0182 |
| `email_metrics_plain.json` | `validation_by_C.1.tn` | 3714 | 3712 |
| `email_metrics_plain.json` | `validation_by_C.1.fp` | 67 | 69 |
| `email_metrics_plain.json` | `validation_by_C.4.accuracy` | 0.9876 | 0.9875 |
| `email_metrics_plain.json` | `validation_by_C.4.precision` | 0.9871 | 0.9866 |
| `email_metrics_plain.json` | `validation_by_C.4.recall` | 0.9879 | 0.9882 |
| `email_metrics_plain.json` | `validation_by_C.4.f1` | 0.9875 | 0.9874 |
| `email_metrics_plain.json` | `validation_by_C.4.false_positive_rate` | 0.0127 | 0.0132 |
| `email_metrics_plain.json` | `validation_by_C.4.tn` | 3733 | 3731 |
| `email_metrics_plain.json` | `validation_by_C.4.fp` | 48 | 50 |
| `email_metrics_plain.json` | `validation_by_C.4.fn` | 45 | 44 |
| `email_metrics_plain.json` | `validation_by_C.4.tp` | 3672 | 3673 |
| `email_metrics_plain.json` | `validation_by_C.16.accuracy` | 0.9892 | 0.9891 |
| `email_metrics_plain.json` | `validation_by_C.16.precision` | 0.9887 | 0.9879 |
| `email_metrics_plain.json` | `validation_by_C.16.recall` | 0.9895 | 0.99 |
| `email_metrics_plain.json` | `validation_by_C.16.f1` | 0.9891 | 0.989 |
| `email_metrics_plain.json` | `validation_by_C.16.false_positive_rate` | 0.0111 | 0.0119 |
| `email_metrics_plain.json` | `validation_by_C.16.tn` | 3739 | 3736 |
| `email_metrics_plain.json` | `validation_by_C.16.fp` | 42 | 45 |
| `email_metrics_plain.json` | `validation_by_C.16.fn` | 39 | 37 |
| `email_metrics_plain.json` | `validation_by_C.16.tp` | 3678 | 3680 |
| `email_metrics_plain.json` | `validation_by_C.16.roc_auc` | 0.9994 | 0.9995 |
| `email_metrics_plain.json` | `validation_by_C.16.pr_auc` | 0.9994 | 0.9995 |
| `email_metrics_plain.json` | `pooled_test.n` | 7498 | 7499 |
| `email_metrics_plain.json` | `pooled_test.positives` | 3715 | 3716 |
| `email_metrics_plain.json` | `pooled_test.accuracy` | 0.9919 | 0.9917 |
| `email_metrics_plain.json` | `pooled_test.precision` | 0.9901 | 0.9911 |
| `email_metrics_plain.json` | `pooled_test.recall` | 0.9935 | 0.9922 |
| `email_metrics_plain.json` | `pooled_test.f1` | 0.9918 | 0.9917 |
| `email_metrics_plain.json` | `pooled_test.false_positive_rate` | 0.0098 | 0.0087 |
| `email_metrics_plain.json` | `pooled_test.tn` | 3746 | 3750 |
| `email_metrics_plain.json` | `pooled_test.fp` | 37 | 33 |
| `email_metrics_plain.json` | `pooled_test.fn` | 24 | 29 |
| `email_metrics_plain.json` | `pooled_test.tp` | 3691 | 3687 |
| `email_metrics_plain.json` | `pooled_test.roc_auc` | 0.9996 | 0.9995 |
| `email_metrics_plain.json` | `pooled_test.pr_auc` | 0.9996 | 0.9995 |
| `email_metrics_plain.json` | `pooled_test_ci95.precision.0` | 0.9868 | 0.9877 |
| `email_metrics_plain.json` | `pooled_test_ci95.precision.1` | 0.9929 | 0.9939 |
| `email_metrics_plain.json` | `pooled_test_ci95.recall.0` | 0.9906 | 0.9893 |
| `email_metrics_plain.json` | `pooled_test_ci95.recall.1` | 0.9962 | 0.9949 |
| `email_metrics_plain.json` | `pooled_test_ci95.f1.0` | 0.9896 | 0.9895 |
| `email_metrics_plain.json` | `pooled_test_ci95.f1.1` | 0.9938 | 0.9937 |
| `email_metrics_plain.json` | `pooled_test_at_1pct_fpr.n` | 7498 | 7499 |
| `email_metrics_plain.json` | `pooled_test_at_1pct_fpr.positives` | 3715 | 3716 |
| `email_metrics_plain.json` | `pooled_test_at_1pct_fpr.threshold` | 0.5262 | 0.5364 |
| `email_metrics_plain.json` | `pooled_test_at_1pct_fpr.accuracy` | 0.9919 | 0.9915 |
| `email_metrics_plain.json` | `pooled_test_at_1pct_fpr.precision` | 0.9911 | 0.9919 |
| `email_metrics_plain.json` | `pooled_test_at_1pct_fpr.recall` | 0.9925 | 0.9909 |
| `email_metrics_plain.json` | `pooled_test_at_1pct_fpr.f1` | 0.9918 | 0.9914 |
| `email_metrics_plain.json` | `pooled_test_at_1pct_fpr.false_positive_rate` | 0.0087 | 0.0079 |
| `email_metrics_plain.json` | `pooled_test_at_1pct_fpr.tn` | 3750 | 3753 |
| `email_metrics_plain.json` | `pooled_test_at_1pct_fpr.fp` | 33 | 30 |
| `email_metrics_plain.json` | `pooled_test_at_1pct_fpr.fn` | 28 | 34 |
| `email_metrics_plain.json` | `pooled_test_at_1pct_fpr.tp` | 3687 | 3682 |
| `email_metrics_plain.json` | `pooled_test_at_1pct_fpr.roc_auc` | 0.9996 | 0.9995 |
| `email_metrics_plain.json` | `pooled_test_at_1pct_fpr.pr_auc` | 0.9996 | 0.9995 |
| `email_metrics_plain.json` | `pooled_test_per_source.CEAS_08.n` | 3574 | 3575 |
| `email_metrics_plain.json` | `pooled_test_per_source.CEAS_08.positives` | 1854 | 1855 |
| `email_metrics_plain.json` | `pooled_test_per_source.CEAS_08.accuracy` | 0.9955 | 0.9964 |
| `email_metrics_plain.json` | `pooled_test_per_source.CEAS_08.precision` | 0.993 | 0.9936 |
| `email_metrics_plain.json` | `pooled_test_per_source.CEAS_08.recall` | 0.9984 | 0.9995 |
| `email_metrics_plain.json` | `pooled_test_per_source.CEAS_08.f1` | 0.9957 | 0.9965 |
| `email_metrics_plain.json` | `pooled_test_per_source.CEAS_08.false_positive_rate` | 0.0076 | 0.007 |
| `email_metrics_plain.json` | `pooled_test_per_source.CEAS_08.tn` | 1707 | 1708 |
| `email_metrics_plain.json` | `pooled_test_per_source.CEAS_08.fp` | 13 | 12 |
| `email_metrics_plain.json` | `pooled_test_per_source.CEAS_08.fn` | 3 | 1 |
| `email_metrics_plain.json` | `pooled_test_per_source.CEAS_08.tp` | 1851 | 1854 |
| `email_metrics_plain.json` | `pooled_test_per_source.Enron.accuracy` | 0.9917 | 0.9897 |
| `email_metrics_plain.json` | `pooled_test_per_source.Enron.recall` | 0.9876 | 0.9834 |
| `email_metrics_plain.json` | `pooled_test_per_source.Enron.f1` | 0.9913 | 0.9892 |
| `email_metrics_plain.json` | `pooled_test_per_source.Enron.fn` | 18 | 24 |
| `email_metrics_plain.json` | `pooled_test_per_source.Enron.tp` | 1428 | 1422 |
| `email_metrics_plain.json` | `pooled_test_per_source.Enron.roc_auc` | 0.9997 | 0.9996 |
| `email_metrics_plain.json` | `pooled_test_per_source.Enron.pr_auc` | 0.9997 | 0.9996 |
| `email_metrics_plain.json` | `pooled_test_per_source.FraudEmail.accuracy` | 0.9784 | 0.9805 |
| `email_metrics_plain.json` | `pooled_test_per_source.FraudEmail.precision` | 0.9604 | 0.9671 |
| `email_metrics_plain.json` | `pooled_test_per_source.FraudEmail.recall` | 0.9928 | 0.9904 |
| `email_metrics_plain.json` | `pooled_test_per_source.FraudEmail.f1` | 0.9763 | 0.9786 |
| `email_metrics_plain.json` | `pooled_test_per_source.FraudEmail.false_positive_rate` | 0.0334 | 0.0275 |
| `email_metrics_plain.json` | `pooled_test_per_source.FraudEmail.tn` | 492 | 495 |
| `email_metrics_plain.json` | `pooled_test_per_source.FraudEmail.fp` | 17 | 14 |
| `email_metrics_plain.json` | `pooled_test_per_source.FraudEmail.fn` | 3 | 4 |
| `email_metrics_plain.json` | `pooled_test_per_source.FraudEmail.tp` | 412 | 411 |
| `email_metrics_plain.json` | `pooled_test_per_source.FraudEmail.roc_auc` | 0.9984 | 0.9985 |
| `email_metrics_plain.json` | `pooled_test_per_source.FraudEmail.pr_auc` | 0.9981 | 0.9982 |
| `email_metrics_plain.json` | `baseline_complement_nb_test.n` | 7498 | 7499 |
| `email_metrics_plain.json` | `baseline_complement_nb_test.positives` | 3715 | 3716 |
| `email_metrics_plain.json` | `baseline_complement_nb_test.accuracy` | 0.9888 | 0.9883 |
| `email_metrics_plain.json` | `baseline_complement_nb_test.precision` | 0.9937 | 0.9943 |
| `email_metrics_plain.json` | `baseline_complement_nb_test.recall` | 0.9836 | 0.982 |
| `email_metrics_plain.json` | `baseline_complement_nb_test.f1` | 0.9886 | 0.9881 |
| `email_metrics_plain.json` | `baseline_complement_nb_test.false_positive_rate` | 0.0061 | 0.0056 |
| `email_metrics_plain.json` | `baseline_complement_nb_test.tn` | 3760 | 3762 |
| `email_metrics_plain.json` | `baseline_complement_nb_test.fp` | 23 | 21 |
| `email_metrics_plain.json` | `baseline_complement_nb_test.fn` | 61 | 67 |
| `email_metrics_plain.json` | `baseline_complement_nb_test.tp` | 3654 | 3649 |
| `email_metrics_plain.json` | `baseline_complement_nb_test.pr_auc` | 0.9993 | 0.9992 |
| `email_metrics_plain.json` | `leave_one_corpus_out.CEAS_08.accuracy` | 0.8182 | 0.8173 |
| `email_metrics_plain.json` | `leave_one_corpus_out.CEAS_08.precision` | 0.7438 | 0.7428 |
| `email_metrics_plain.json` | `leave_one_corpus_out.CEAS_08.recall` | 0.9909 | 0.991 |
| `email_metrics_plain.json` | `leave_one_corpus_out.CEAS_08.f1` | 0.8498 | 0.8491 |
| `email_metrics_plain.json` | `leave_one_corpus_out.CEAS_08.false_positive_rate` | 0.3681 | 0.3701 |
| `email_metrics_plain.json` | `leave_one_corpus_out.CEAS_08.tn` | 10867 | 10833 |
| `email_metrics_plain.json` | `leave_one_corpus_out.CEAS_08.fp` | 6330 | 6364 |
| `email_metrics_plain.json` | `leave_one_corpus_out.CEAS_08.fn` | 168 | 167 |
| `email_metrics_plain.json` | `leave_one_corpus_out.CEAS_08.tp` | 18377 | 18378 |
| `email_metrics_plain.json` | `leave_one_corpus_out.CEAS_08.roc_auc` | 0.9614 | 0.9611 |
| `email_metrics_plain.json` | `leave_one_corpus_out.CEAS_08.pr_auc` | 0.9565 | 0.9563 |
| `email_metrics_plain.json` | `leave_one_corpus_out.Enron.accuracy` | 0.8038 | 0.7996 |
| `email_metrics_plain.json` | `leave_one_corpus_out.Enron.precision` | 0.955 | 0.9548 |
| `email_metrics_plain.json` | `leave_one_corpus_out.Enron.recall` | 0.6225 | 0.6134 |
| `email_metrics_plain.json` | `leave_one_corpus_out.Enron.f1` | 0.7537 | 0.7469 |
| `email_metrics_plain.json` | `leave_one_corpus_out.Enron.false_positive_rate` | 0.0273 | 0.027 |
| `email_metrics_plain.json` | `leave_one_corpus_out.Enron.tn` | 15109 | 15113 |
| `email_metrics_plain.json` | `leave_one_corpus_out.Enron.fp` | 424 | 420 |
| `email_metrics_plain.json` | `leave_one_corpus_out.Enron.fn` | 5460 | 5592 |
| `email_metrics_plain.json` | `leave_one_corpus_out.Enron.tp` | 9004 | 8872 |
| `email_metrics_plain.json` | `leave_one_corpus_out.Enron.roc_auc` | 0.9363 | 0.9353 |
| `email_metrics_plain.json` | `leave_one_corpus_out.Enron.pr_auc` | 0.9349 | 0.9337 |
| `email_metrics_plain.json` | `leave_one_corpus_out.FraudEmail.n` | 9240 | 9244 |
| `email_metrics_plain.json` | `leave_one_corpus_out.FraudEmail.positives` | 4149 | 4153 |
| `email_metrics_plain.json` | `leave_one_corpus_out.FraudEmail.accuracy` | 0.8694 | 0.868 |
| `email_metrics_plain.json` | `leave_one_corpus_out.FraudEmail.precision` | 0.7822 | 0.7806 |
| `email_metrics_plain.json` | `leave_one_corpus_out.FraudEmail.recall` | 0.9826 | 0.9824 |
| `email_metrics_plain.json` | `leave_one_corpus_out.FraudEmail.f1` | 0.8711 | 0.8699 |
| `email_metrics_plain.json` | `leave_one_corpus_out.FraudEmail.false_positive_rate` | 0.2229 | 0.2253 |
| `email_metrics_plain.json` | `leave_one_corpus_out.FraudEmail.tn` | 3956 | 3944 |
| `email_metrics_plain.json` | `leave_one_corpus_out.FraudEmail.fp` | 1135 | 1147 |
| `email_metrics_plain.json` | `leave_one_corpus_out.FraudEmail.fn` | 72 | 73 |
| `email_metrics_plain.json` | `leave_one_corpus_out.FraudEmail.tp` | 4077 | 4080 |
| `email_metrics_plain.json` | `leave_one_corpus_out.FraudEmail.roc_auc` | 0.98 | 0.9797 |
| `email_metrics_plain.json` | `leave_one_corpus_out.FraudEmail.pr_auc` | 0.9785 | 0.9781 |
| `email_metrics_plain.json` | `top_terms_malicious.0.1` | 15.389 | 15.464 |
| `email_metrics_plain.json` | `top_terms_malicious.1.1` | 12.901 | 12.906 |
| `email_metrics_plain.json` | `top_terms_malicious.2.1` | 10.568 | 10.408 |
| `email_metrics_plain.json` | `top_terms_malicious.3.1` | 10.344 | 10.369 |
| `email_metrics_plain.json` | `top_terms_malicious.4.1` | 10.338 | 10.336 |
| `email_metrics_plain.json` | `top_terms_malicious.5.1` | 9.287 | 9.299 |
| `email_metrics_plain.json` | `top_terms_malicious.6.1` | 8.91 | 8.899 |
| `email_metrics_plain.json` | `top_terms_malicious.7.1` | 8.236 | 8.248 |
| `email_metrics_plain.json` | `top_terms_malicious.8.1` | 7.838 | 7.808 |
| `email_metrics_plain.json` | `top_terms_malicious.9.1` | 7.75 | 7.786 |
| `email_metrics_plain.json` | `top_terms_malicious.10.1` | 7.676 | 7.752 |
| `email_metrics_plain.json` | `top_terms_malicious.11.1` | 7.59 | 7.71 |
| `email_metrics_plain.json` | `top_terms_malicious.12.1` | 7.401 | 7.49 |
| `email_metrics_plain.json` | `top_terms_malicious.13.1` | 7.326 | 7.298 |
| `email_metrics_plain.json` | `top_terms_malicious.14.1` | 7.137 | 7.073 |
| `email_metrics_plain.json` | `top_terms_malicious.15.1` | 6.973 | 6.94 |
| `email_metrics_plain.json` | `top_terms_malicious.16.1` | 6.681 | 6.733 |
| `email_metrics_plain.json` | `top_terms_malicious.17.1` | 6.647 | 6.664 |
| `email_metrics_plain.json` | `top_terms_malicious.18.1` | 6.558 | 6.565 |
| `email_metrics_plain.json` | `top_terms_malicious.19.1` | 6.517 | 6.546 |
| `email_metrics_plain.json` | `top_terms_malicious.20.1` | 6.491 | 6.529 |
| `email_metrics_plain.json` | `top_terms_malicious.21.1` | 6.481 | 6.489 |
| `email_metrics_plain.json` | `top_terms_malicious.22.1` | 6.475 | 6.481 |
| `email_metrics_plain.json` | `top_terms_malicious.23.1` | 6.406 | 6.445 |
| `email_metrics_plain.json` | `top_terms_malicious.24.1` | 6.372 | 6.401 |
| `email_metrics_plain.json` | `top_terms_malicious.25.1` | 6.253 | 6.28 |
| `email_metrics_plain.json` | `top_terms_malicious.26.1` | 6.16 | 6.148 |
| `email_metrics_plain.json` | `top_terms_malicious.27.1` | 5.983 | 5.975 |
| `email_metrics_plain.json` | `top_terms_malicious.28.1` | 5.884 | 5.93 |
| `email_metrics_plain.json` | `top_terms_malicious.29.1` | 5.619 | 5.749 |
| `email_metrics_plain.json` | `top_terms_legit.0.1` | -17.379 | -17.36 |
| `email_metrics_plain.json` | `top_terms_legit.1.1` | -12.151 | -12.131 |
| `email_metrics_plain.json` | `top_terms_legit.2.1` | -11.952 | -11.948 |
| `email_metrics_plain.json` | `top_terms_legit.3.1` | -10.065 | -10.077 |
| `email_metrics_plain.json` | `top_terms_legit.4.1` | -9.862 | -9.868 |
| `email_metrics_plain.json` | `top_terms_legit.5.1` | -9.604 | -9.62 |
| `email_metrics_plain.json` | `top_terms_legit.6.1` | -9.55 | -9.544 |
| `email_metrics_plain.json` | `top_terms_legit.8.1` | -9.393 | -9.365 |
| `email_metrics_plain.json` | `top_terms_legit.9.1` | -9.042 | -9.16 |
| `email_metrics_plain.json` | `top_terms_legit.10.1` | -8.59 | -8.655 |
| `email_metrics_plain.json` | `top_terms_legit.11.1` | -8.542 | -8.516 |
| `email_metrics_plain.json` | `top_terms_legit.12.1` | -8.267 | -8.249 |
| `email_metrics_plain.json` | `top_terms_legit.13.1` | -7.532 | -7.598 |
| `email_metrics_plain.json` | `top_terms_legit.14.1` | -7.53 | -7.537 |
| `email_metrics_plain.json` | `top_terms_legit.15.1` | -7.332 | -7.353 |
| `email_metrics_plain.json` | `top_terms_legit.16.1` | -7.299 | -7.316 |
| `email_metrics_plain.json` | `top_terms_legit.17.1` | -7.266 | -7.303 |
| `email_metrics_plain.json` | `top_terms_legit.18.1` | -7.153 | -7.165 |
| `email_metrics_plain.json` | `top_terms_legit.19.1` | -7.088 | -7.071 |
| `email_metrics_plain.json` | `top_terms_legit.20.1` | -6.917 | -6.913 |
| `email_metrics_plain.json` | `top_terms_legit.21.1` | -6.795 | -6.803 |
| `email_metrics_plain.json` | `top_terms_legit.22.1` | -6.783 | -6.785 |
| `email_metrics_plain.json` | `top_terms_legit.23.1` | -6.724 | -6.744 |
| `email_metrics_plain.json` | `top_terms_legit.24.1` | -6.659 | -6.682 |
| `email_metrics_plain.json` | `top_terms_legit.25.1` | -6.524 | -6.677 |
| `email_metrics_plain.json` | `top_terms_legit.26.1` | -6.29 | -6.309 |
| `email_metrics_plain.json` | `top_terms_legit.27.1` | -6.286 | -6.293 |
| `email_metrics_plain.json` | `top_terms_legit.28.1` | -6.272 | -6.218 |
| `email_metrics_plain.json` | `top_terms_legit.29.1` | -6.144 | -6.131 |
| `fusion_metrics.json` | `single_channel_alert_any_event_ge_0.5.accuracy` | 0.9058 | 0.9068 |
| `fusion_metrics.json` | `single_channel_alert_any_event_ge_0.5.precision` | 0.8695 | 0.8708 |
| `fusion_metrics.json` | `single_channel_alert_any_event_ge_0.5.recall` | 0.9533 | 0.9538 |
| `fusion_metrics.json` | `single_channel_alert_any_event_ge_0.5.f1` | 0.9095 | 0.9104 |
| `fusion_metrics.json` | `single_channel_alert_any_event_ge_0.5.false_positive_rate` | 0.141 | 0.1395 |
| `fusion_metrics.json` | `single_channel_alert_any_event_ge_0.5.tn` | 5192 | 5201 |

194 more differences not listed.

## Model files

| File | v2 SHA-256 | Final run on cp1-rc1 SHA-256 | Same bytes |
|---|---|---|---|
| `email_model.joblib` | `b8f8ea9f4434fa11...` | `37fb42d036032f75...` | no |
| `email_model_plain.joblib` | `6d4bbced6ecd7158...` | `5f4af8cd7d86f111...` | no |
| `fusion_model.joblib` | `179294b428e3ab52...` | `27565edc43611aec...` | no |
| `sms_model.joblib` | `34f5ad3b99326dd6...` | `e9992c44c8757983...` | no |
| `url_features_all_features.joblib` | `c70a746d0b22df78...` | `e877dbc4881f700d...` | no |
| `url_features_lexical_only.joblib` | `e4eb1ac5379dea6c...` | `58052731be8ad9e7...` | no |
| `url_string_model.joblib` | `466e710ab3f212ab...` | `670623455f507105...` | no |

Pickled models can differ in bytes while making identical predictions (pickle stores object ids and dict order). The metrics above are the comparison that matters.

## End of the run log

```
single_channel           {'precision': 0.8708, 'recall': 0.9538, 'f1': 0.9104, 'false_positive_rate': 0.1395}
parallel_multichannel    {'precision': 0.9703, 'recall': 0.926, 'f1': 0.9476, 'false_positive_rate': 0.028}
whole_bundle_model       {'precision': 0.9678, 'recall': 0.9333, 'f1': 0.9503, 'false_positive_rate': 0.0306}
deployed_engine_60min    {'precision': 0.8942, 'recall': 0.9491, 'f1': 0.9208, 'false_positive_rate': 0.1107}
patent_noisy_or          not evaluated: the owner decided on 7 Nov 2026 that the patent will be written from this build; the old draft's noisy-OR method and its generated numbers are not used
wrote results.md 15936 chars
```

