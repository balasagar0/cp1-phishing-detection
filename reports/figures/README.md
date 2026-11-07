# Figures

Drawn by `scripts/make_figures.py` from the reports of `cp1-final` (commit `18ba1d9`). Each figure is a PNG at 300 dpi and an SVG. They read in grayscale: the second series is hatched and every value is printed. Simulated results are titled SIMULATED.

| Figure | What it shows | Data | Caption |
|---|---|---|---|
| `fig1_honest_vs_flattering.png` / `.svg` | F1 per detector, honest and flattering | `email_metrics.json` (leave_one_corpus_out mean; pooled_test), `sms_metrics.json` (test_smishing_vs_rest; test_unwanted_vs_ham), `url_metrics.json` (string_model.grouped_test; feature_benchmark.hgb_all_features) | Honest: email trained on two corpora and tested on the third (mean of three runs); SMS smishing against everything else; URL with no host in both train and test. Flattering measures are shown only beside them. |
| `fig2_correlation_simulated.png` / `.svg` | Correlation against baselines (SIMULATED) | `comparison_metrics.json` (rows: precision, recall, f1, false_positive_rate, ci95) | SIMULATED bundles. Single-channel alerting, the fusion model without link and timing features, the correlation model on the whole bundle, and the deployed 60-minute engine. Error bars are 95% bootstrap intervals. |
| `fig3_confusion_matrices.png` / `.svg` | Confusion matrices, honest measures | `email_metrics.json` (leave_one_corpus_out: tn, fp, fn, tp), `sms_metrics.json` (test_smishing_vs_rest), `url_metrics.json` (string_model.grouped_test) | Each cell shows the count and its share of the true class; darker means a larger share. Email is shown once per held-out corpus. |
| `fig4_url_login_tradeoff.png` / `.svg` | URL login-page trade-off | `url_metrics.json` (string_model.ablation: a, b, c) | Each step adds to the one before. The final model stops flagging login pages of popular domains, and catches fewer bad URLs hosted on popular domains. Quote both halves. |
| `fig5_latency.png` / `.svg` | Latency over real HTTP | `benchmark.json` (per_channel, full_case, machine) | Measured on the build laptop, which is not confirmed as the demo laptop. The targets are far off this scale. |
