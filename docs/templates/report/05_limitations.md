# Chapter 5. Limitations

Each limitation below is measured on build `{{build.tag}}`.

1. **Correlation is measured only on simulated bundles.** The events are real; the campaigns are constructed. On them the deployed engine
   has F1 {{corr.engine.f1}} and a false-positive rate of {{corr.engine.fpr}}, against {{corr.single.f1}} and {{corr.single.fpr}} for
   single-channel alerting. No real coordinated bundle has been collected yet (R2-10).
2. **The risk is not a calibrated probability.** The alert line {{alert_line}} is tied to the simulation's mix ({{corr.malicious_share}} of the test bundles are malicious).
3. **The correlation model is not stable on borderline bundles.** A retrain moved TC-06 from {{finalrun.tc06.live}} to
   {{finalrun.tc06.retrained}} while the simulated F1 moved from {{finalrun.sim_f1.live}} to {{finalrun.sim_f1.retrained}}.
4. **Email does not transfer across sources.** F1 {{email.honest.f1}} on unseen corpora; false-positive rates there of
   {{email.honest.fpr_range}}; {{email.realmail.fpr}} false alarms on {{email.realmail.n}} real legitimate emails of one user. The labels mix
   spam and fraud with phishing.
5. **The URL fix costs recall.** Bad URLs hosted on popular domains are caught less often: {{url.popular_recall.before}} before the fix,
   {{url.popular_recall.after}} after. Login pages on small unknown sites are still likely to be flagged.
6. **SMS smishing is a small class.** {{sms.smishing_support}} test messages; F1 interval {{sms.honest.f1_ci}}.
7. **The correlated score can be lower than the best single score** (D-18): a lone high score next to weaker events is pulled down a little.
8. **A detector false positive stays a false positive.** Correlation does not repair it (TC-08).
9. **Voice and video are not assessed.** No detector was trained.
10. **The corpora are mostly English and several years old.** Regional-language and current phishing are under-represented.
11. **Speed was measured on the build laptop**, one request at a time; the demo laptop and concurrent load are untested.
