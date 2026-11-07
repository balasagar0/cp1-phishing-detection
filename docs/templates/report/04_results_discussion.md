# Chapter 4. Results and discussion

All numbers are from build `{{build.tag}}` (`reports/FINAL_NUMBERS.md`). Correlation results are on simulated bundles.

## 4.1 Detectors

![Honest and flattering F1 per detector](../../reports/figures/fig1_honest_vs_flattering.png)

{{block:detectors}}

**Email.** The honest figure is the mean F1 of three leave-one-corpus-out runs: {{email.honest.f1}}, against {{email.flattering.f1}} on a pooled
random split. The gap is the corpus style that a random split rewards. On unseen corpora the false-positive rate ranges from
{{email.honest.fpr_range}}: the threshold does not transfer. On {{email.realmail.n}} real legitimate emails of one consenting user, the live
model raised a false alarm on {{email.realmail.fpr}}. {{email.retrain_attempts}} attempts to retrain with more data were made under a rule
fixed in advance; none passed, so v2's model stays.

**SMS.** Smishing against everything else: F1 {{sms.honest.f1}} (95% CI {{sms.honest.f1_ci}}). The interval is wide because only
{{sms.smishing_support}} test messages are smishing.

**URL.** With hosts held out, F1 {{url.honest.f1}}. The login-page fix took false alarms on popular login pages from
{{url.login_fpr.before}} to {{url.login_fpr.after}}, and recall on bad URLs on popular domains from {{url.popular_recall.before}} to
{{url.popular_recall.after}}.

![URL login-page trade-off](../../reports/figures/fig4_url_login_tradeoff.png)

![Confusion matrices](../../reports/figures/fig3_confusion_matrices.png)

## 4.2 Correlation (simulated bundles)

![Correlation against baselines, simulated](../../reports/figures/fig2_correlation_simulated.png)

{{block:corr}}

On simulated bundles the deployed engine beats single-channel alerting by a little, mostly through fewer false alarms. The same model
without link and timing features is almost as good, so most of the gain comes from combining scores (ROC-AUC {{corr.auc.single}},
{{corr.auc.nocorr}}, {{corr.auc.fusion}}). The window costs score on this simulation, because the simulation labels unlinked bundles as a
whole; we keep it as the cautious choice. Only {{corr.hard.n}} simulated linked attacks ({{corr.hard.share}}) are missed by every
single-channel filter, and the engine flags {{corr.engine.hard_flagged}} of them. These numbers describe the simulation, not field
performance.

## 4.3 Demo cases (hand-written, not a test set)

{{block:demo}}

TC-06 is the one case where the bundle alerts and no single event does. It is near the line: a retrain on almost the same simulated data moved
it from {{finalrun.tc06.live}} to {{finalrun.tc06.retrained}}. TC-08 shows that a detector false positive (the courier SMS) stays a false
positive after correlation.

## 4.4 Speed

![Latency](../../reports/figures/fig5_latency.png)

Median {{latency.email.median}} per email, {{latency.sms.median}} per SMS, {{latency.url.median}} per URL and {{latency.case.median}} per full
case, over real HTTP on the build laptop.

## 4.5 Discussion

The detectors are standard methods; what this work adds is the honest evaluation and the engine around them. Reporting the honest split
beside the flattering one changes the story for email most of all. The correlation engine is built and tested end to end, but its value can
only be judged on real coordinated bundles; on simulated ones it helps a little, and its verdict on borderline cases is not stable under
retraining.
