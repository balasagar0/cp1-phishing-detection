"""Builds reports/results.md from the metrics JSON files (numbers are never typed by hand)."""
import json
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "reports"
L_ = lambda n: json.load(open(R / n, encoding="utf-8"))
E, EP, S, U, FU, PR = L_("email_metrics.json"), L_("email_metrics_plain.json"), L_("sms_metrics.json"), L_("url_metrics.json"), L_("fusion_metrics.json"), L_("probe_results.json")
UA, UB = U["string_model"], U["feature_benchmark"]
pct = lambda x: f"{100 * x:.1f}%"
def row(name, m, note=""):
    return f"| {name} | {m['n']:,} | {pct(m['precision'])} | {pct(m['recall'])} | {pct(m['f1'])} | {pct(m['false_positive_rate'])} | {m.get('roc_auc', float('nan')):.3f} | {note} |"
HDR = "| Evaluation | n | Precision | Recall | F1 | False-positive rate | ROC-AUC | Note |\n|---|---|---|---|---|---|---|---|"
avg = lambda d, k: sum(v[k] for v in d["leave_one_corpus_out"].values()) / 3
ci = lambda c: f"95% CI F1 {pct(c['f1'][0])}-{pct(c['f1'][1])}"
L = ["# CP1 detectors - training results\n",
     "Every number below is produced by the scripts in `src/` from public data, on held-out rows. Nothing is hand-typed. Positive class = *not benign* (spam / phishing / fraud / smishing / malicious URL).\n",
     "## 1. What is trained\n", "| Model | Type | Training data (after cleaning + de-duplication) | Used live? |\n|---|---|---|---|"]
ec = E["data"]["counts"]; sc = S["data"]["class_counts"]
L.append(f"| Email | TF-IDF 1-2-grams (numbers masked, vocabulary limited to terms seen in >=2 corpora) + logistic regression | {sum(sum(v.values()) for v in ec.values()):,} emails: " + "; ".join(f"{k} {sum(v.values()):,}" for k, v in ec.items()) + " | yes |")
L.append(f"| SMS | 3-class (ham / spam / smishing) word + character TF-IDF + logistic regression | LSDST: {sum(sc.values()):,} messages (ham {sc['ham']:,}, spam {sc['spam']:,}, smishing {sc['smishing']:,}) | yes |")
L.append(f"| URL | character 3-5-gram hashing + TF-IDF + 3 domain-popularity flags + logistic regression, raw URL string in | {UA['data']['rows_used']:,} URLs ({pct(UA['data']['bad_share'])} labelled bad) + {UA['data']['constructed_sets']['train_login_urls']:,} constructed login URLs on popular domains | yes |")
L.append(f"| URL (benchmark) | gradient boosting on {UB['data']['n_features_all']} pre-computed features | {UB['data']['rows_after']:,} rows | no - {len(UB['data']['network_dependent_features'])} features need DNS/WHOIS/SSL/Google lookups |")
L.append(f"| Correlation | gradient boosting on bundle features (per-channel scores, shared identity, time span), applied inside a time window (default 60 min) | {FU['n_bundles']['train']:,} SIMULATED bundles built from real held-out messages | yes (`POST /correlate`) |")
L.append("| Voice, video | not trained | no accessible training data | no |\n")

L.append("## 2. Per-channel results (held-out data)\n\n### Email\n"); L.append(HDR)
L.append(row("Pooled random test (final model)", E["pooled_test"], ci(E["pooled_test_ci95"])))
for s, m in E["pooled_test_per_source"].items(): L.append(row(f"  of which {s}", m))
L.append("| **Leave-one-corpus-out** (train on two corpora, test on the third) | | | | | | | |")
for s, m in E["leave_one_corpus_out"].items(): L.append(row(f"  held-out {s}", m))
L.append("| Baseline: plain pipeline (no masking / vocabulary filter) | | | | | | | |"); L.append(row("  pooled random test", EP["pooled_test"]))
for s, m in EP["leave_one_corpus_out"].items(): L.append(row(f"  held-out {s}", m))
L.append(f"\nAverage over the three held-out corpora: final F1 {pct(avg(E,'f1'))} / AUC {avg(E,'roc_auc'):.3f}; plain F1 {pct(avg(EP,'f1'))} / AUC {avg(EP,'roc_auc'):.3f}. No measurable cross-corpus gain from the robust variant. It is deployed because it no longer relies on years and numbers, which identify a corpus.\n")
L.append("### SMS\n"); L.append(HDR)
L.append(row("Smishing vs everything else (20% test)", S["test_smishing_vs_rest"], ci(S["test_smishing_vs_rest_ci95"])))
L.append(row("Spam-or-smishing vs ham (20% test)", S["test_unwanted_vs_ham"], ci(S["test_unwanted_vs_ham_ci95"])))
L.append(row("Smishing vs rest, 5-fold out-of-fold (all data)", S["oof5_smishing_vs_rest"]))
if "external_combined_unwanted_vs_ham" in S: L.append(row("External set, spam-or-smishing vs ham (texts not in training)", S["external_combined_unwanted_vs_ham"], "different collection; domain-shift check"))
t3 = S["test_3class"]; L.append(f"\n3-class macro-F1 on the test split: {pct(t3['macro_f1'])}. Per class: " + "; ".join(f"{k} P {pct(v['precision'])} / R {pct(v['recall'])} (n={v['support']})" for k, v in t3["per_class"].items()) + ".\n")
L.append("### URL\n"); L.append(HDR)
L.append(row("String model, host-grouped test (final)", UA["grouped_test"], ci(UA["grouped_test_ci95"])))
L.append(row("Feature benchmark, gradient boosting, all features", UB["hgb_all_features"], "random split; offline only"))
L.append(row("Feature benchmark, gradient boosting, lexical-only features", UB["hgb_lexical_only"], f"{UB['data']['n_features_lexical_only']} features"))
L.append(row("Feature benchmark, random forest, all features", UB["rf_all_features"]))
ab = UA["ablation"]; nm = {"a_ngrams_only": "(a) n-grams only (first version)", "b_plus_popularity_flags": "(b) + domain-popularity flags", "c_plus_login_training_urls_FINAL": "(c) + login URLs on popular domains (final)"}
L.append("\n**Fixing false alarms on login pages** - same host-grouped split, same settings, three variants:\n")
L.append("| Variant | F1 | ROC-AUC | False alarms on login URLs of 1,000 held-out popular domains | Detection of 2,000 brand-impersonation probes | Recall on bad URLs hosted on top-10k domains |\n|---|---|---|---|---|---|")
for k, v in ab.items():
    bt = v["recall_on_bad_urls_hosted_on_top10k_domains"]
    L.append(f"| {nm[k]} | {pct(v['grouped_test']['f1'])} | {v['grouped_test']['roc_auc']:.3f} | {pct(v['false_positive_rate_on_login_urls_of_1000_held_out_popular_domains'])} | {pct(v['detection_rate_on_2000_brand_impersonation_probes'])} | {pct(bt['recall'])} (n={bt['n']}) |")
L.append(f"\nThe login URLs and brand-impersonation probes are *constructed* (path and host templates in `src/url_features.py`), not real traffic. The popularity list has {UA['data']['popularity_list_domains']:,} domains; {pct(UA['data']['share_of_good_urls_on_top10k_domain'])} of the dataset's good URLs and {pct(UA['data']['share_of_bad_urls_on_top10k_domain'])} of its bad URLs sit on one, so the flags are a strong signal in this data.\n")

L.append("### Correlation model (simulated bundles)\n")
f1, fm, fn, fa = FU["single_channel_alert_any_event_ge_0.5"], FU["fusion_at_matched_fpr"], FU["fusion_without_correlation_features_at_matched_fpr"], FU["fusion_at_0.5"]
L.append(HDR)
L.append(row("Single-channel: alert if any event >= 0.5", f1, f"AUC of max score {FU['auc']['single_channel_max_score']}"))
L.append(row("Correlation model at 0.5, whole bundle, no window (see the window table below for the deployed engine)", fa))
L.append(row("Correlation model at the single-channel false-positive rate", fm, "threshold set on validation bundles"))
L.append(row("  same, link + timing features removed", fn, f"AUC {FU['auc']['fusion_without_correlation_features']}"))
hc = FU["campaigns_missed_by_every_single_channel_filter"]
L.append(f"\nCampaigns where every event scores below 0.5 (missed by all single-channel filters): {hc['n']} of the linked attacks ({pct(hc['share_of_linked_attacks'])}); the correlation model catches {pct(hc['caught_by_fusion'])} of them, {pct(hc['caught_by_fusion_without_correlation_features'])} without link and timing features.")
L.append("\nShare of bundles flagged, by bundle type (single-channel / correlation model at matched false-positive rate): " + "; ".join(f"{t} {pct(FU['flag_rate_by_bundle_type_single_channel'][t])} / {pct(FU['flag_rate_by_bundle_type_fusion'][t])}" for t in FU["flag_rate_by_bundle_type_fusion"]) + ".\n")
L.append("**This is a simulation.** Bundles are built from real held-out messages scored by the real detectors, but the bundle structure is assumed:\n")
L += [f"- {k.replace('_', ' ')}: {v}" if isinstance(v, str) else f"- bundle mix: " + ", ".join(f"{a} {int(b*100)}%" for a, b in v.items()) for k, v in FU["assumptions"].items()]

WMP = R / "window_metrics.json"; pc = lambda x: pct(x) if x is not None else "n/a"
if WMP.exists():
    WM = json.load(open(WMP, encoding="utf-8")); d0 = f"{WM['default_window_minutes']:g}"
    L.append("\n### Correlation engine with the time window (same simulated test bundles, alert line 0.5)\n"); L.append(HDR)
    L.append(row("Single-channel: alert if any event >= 0.5", WM["single_channel_alert_any_event_ge_0.5"]))
    L.append(row("Correlation model on the whole bundle (rows above)", WM["whole_bundle_model_at_0.5"], "no time limit; a lone event is scored by the model"))
    L.append(row("Engine without a window", WM["engine_no_window_at_0.5"], "a lone event = its detector score"))
    for w, m in WM["engine_by_window_at_0.5"].items(): L.append(row(f"Engine, window {w} min" + (" (default)" if w == d0 else ""), m))
    fit, fl, hc2 = WM["share_of_bundles_that_fit_in_one_default_window"], WM["flag_rate_by_bundle_type_at_0.5"], WM["campaigns_missed_by_every_single_channel_filter"]
    L.append(f"\nShare of simulated bundles whose events all fit in one {d0}-minute window: " + "; ".join(f"{t} {pct(v)}" for t, v in fit.items()) + ".")
    L.append(f"\nShare of bundles flagged at 0.5, by type (single-channel / whole-bundle model / engine with the {d0}-minute window): " + "; ".join(f"{t} {pct(fl['single_channel'][t])} / {pct(fl['whole_bundle_model'][t])} / {pct(fl['engine_default_window'][t])}" for t in fl["single_channel"]) + ".")
    L.append(f"\nCampaigns where every event scores below 0.5: {hc2['n']}; flagged by the whole-bundle model {pc(hc2['caught_whole_bundle_model_at_0.5'])}, by the engine with the window {pc(hc2['caught_engine_default_window_at_0.5'])}.")
    L.append(f"\nThe {d0}-minute window and the single-event rule were fixed before this evaluation was run. The other window sizes are shown for information and were not used to pick anything. The model itself was not retrained.")

CMP = R / "comparison_metrics.json"
if CMP.exists():
    CM = json.load(open(CMP, encoding="utf-8")); skipped = []
    L.append("\n### R3-09: correlation against the baselines (SIMULATED bundles, alert line 0.5)\n")
    L.append("| Method | n | Precision | Recall | F1 (95% CI) | False-positive rate (95% CI) | Simulated campaigns every filter misses, flagged |\n|---|---|---|---|---|---|---|")
    for k, m in CM["rows"].items():
        if "f1" not in m: skipped.append(m); continue          # no empty cells: a method that was not evaluated gets a sentence below, not a row of dashes
        L.append(f"| {m['name']} | {m['n']:,} | {pct(m['precision'])} | {pct(m['recall'])} | {pct(m['f1'])} ({pct(m['ci95']['f1'][0])}-{pct(m['ci95']['f1'][1])}) | "
                 f"{pct(m['false_positive_rate'])} ({pct(m['ci95']['false_positive_rate'][0])}-{pct(m['ci95']['false_positive_rate'][1])}) | {pc(m.get('hard_campaigns_flagged'))} |")
    L.append(f"\n{CM['title']}. Parallel multi-channel = the same fusion recipe trained without link and timing features (src/eval_comparison.py). Real bundles: {CM['real_bundles']}.")
    for m in skipped: L.append(f"\n{m['name']}: {m['status']}.")

L.append("\n## 3. How to read these numbers\n")
L.append("- **Pooled email scores are flattering.** The leave-one-corpus-out rows are the honest estimate: ranking stays fairly good (AUC " + f"{min(v['roc_auc'] for v in E['leave_one_corpus_out'].values()):.2f}-{max(v['roc_auc'] for v in E['leave_one_corpus_out'].values()):.2f}" + ") but a 0.5 threshold does not transfer. False-positive rates on unseen corpora: " + ", ".join(f"{k} {pct(v['false_positive_rate'])}" for k, v in E["leave_one_corpus_out"].items()) + "; recall: " + ", ".join(f"{k} {pct(v['recall'])}" for k, v in E["leave_one_corpus_out"].items()) + ".")
FP = ["enron", "vince", "louise", "houston", "tony", "opensuse", "perl", "python", "uai", "2001", "2004", "2005", "2007", "2008", "2009", "2010", "numtok", "yeartok"]
hit = lambda d: [t for t, _ in d["top_terms_legit"] + d["top_terms_malicious"] if t in FP or any(f in t.split() for f in ("2004", "2005", "2008"))]
L.append("- **Email models partly learn corpus fingerprints.** Fingerprint-like terms among the 60 strongest features - plain: `" + "`, `".join(hit(EP)) + "`; final: `" + "`, `".join(hit(E)) + "`.")
a, c = ab["a_ngrams_only"], ab["c_plus_login_training_urls_FINAL"]
L.append(f"- **The URL fix has a price.** False alarms on login pages of popular domains fell from {pct(a['false_positive_rate_on_login_urls_of_1000_held_out_popular_domains'])} to {pct(c['false_positive_rate_on_login_urls_of_1000_held_out_popular_domains'])}, overall F1 stayed at {pct(c['grouped_test']['f1'])}, but detection of brand-impersonation probes went from {pct(a['detection_rate_on_2000_brand_impersonation_probes'])} to {pct(c['detection_rate_on_2000_brand_impersonation_probes'])} and recall on bad URLs hosted on popular domains from {pct(a['recall_on_bad_urls_hosted_on_top10k_domains']['recall'])} to {pct(c['recall_on_bad_urls_hosted_on_top10k_domains']['recall'])}. The login test shares path templates with the training URLs, so it shows generalisation to new domains, not to new path styles.")
L.append(f"- **Correlation: most of the gain comes from combining scores, not from link and timing evidence.** AUC {FU['auc']['single_channel_max_score']} (max score) -> {FU['auc']['fusion_without_correlation_features']} (learned combination) -> {FU['auc']['fusion']} (with link and timing). The detectors already catch nearly every attack in the pools, so little is left for correlation to find. Real multi-channel data is needed before claiming more.")
if WMP.exists(): L.append(f"- **The time window is not part of the trained model.** The API applies it on top (events further apart than the window are not combined or linked; a lone event is judged by its detector). In the simulation {pct(fit['attack_linked'])} of linked attack bundles fit in one {d0}-minute window, which is why that value is the default. **The window costs score on the simulation:** inside it the engine has F1 {pct(WM['engine_default_window_at_0.5']['f1'])} and false-positive rate {pct(WM['engine_default_window_at_0.5']['false_positive_rate'])}; without a window {pct(WM['engine_no_window_at_0.5']['f1'])} and {pct(WM['engine_no_window_at_0.5']['false_positive_rate'])}; single-channel alerting {pct(WM['single_channel_alert_any_event_ge_0.5']['f1'])} and {pct(WM['single_channel_alert_any_event_ge_0.5']['false_positive_rate'])}. The simulation's unlinked bundles hold events up to 72 hours apart and are labelled as a whole, so pooling them helps there, and the window stops that pooling. Read the default-window row as the cautious estimate of what correlation adds. The simulation cannot settle the window, so do not pick it from this table; the real value has to come from real bundles: `refit_fusion.py` suggests one from your coordinated test cases.")
L.append("- **SMS has few smishing examples** (" + str(t3["per_class"]["smishing"]["support"]) + " in the test split), hence the wide confidence intervals.\n")

L.append("## 4. Hand-written probes (not an evaluation)\n\n| Channel | Truth | Score | Input |\n|---|---|---|---|")
L += [f"| {p['channel']} | {p['truth']} | {p['score']:.2f} | {p['input'][:80]} |" for p in PR]
L.append("\nLegitimate inputs scoring high (url Google Docs link, sms courier tracking message) are known false positives: legitimate cloud-document links and transactional SMS are under-represented as negatives in the public data.\n")
L.append("## 5. Known limitations (state these in the review)\n")
L.append("1. **Email labels are 'unwanted / fraudulent', not strictly phishing.** Corpora used: CEAS_08 (spam + phishing mix), Enron-Spam, a Nigerian-fraud corpus. Three retrain attempts that added Nazario (real phishing), SpamAssassin, Ling-Spam and legitimate transactional mail all failed the adoption rule (reports/candidates/), so the deployed model still uses these three corpora. Earlier text, kept for the record: Nazario (real phishing emails), SpamAssassin and Ling are not in this run; they are on GitHub and can be added (README, 'Retrain from scratch').")
L.append("2. **URL login-page fix is partial.** It works for the 10,000 most popular domains; login pages on unknown small sites are still likely to be flagged, and phishing hosted on popular domains is caught less often (section 3).")
L.append("3. **Known false positives:** legitimate Google Docs links and courier tracking SMS (section 4).")
L.append("4. **Thresholds are not portable across sources** (email, section 3). The 0.5 operating point was not re-validated on any new environment.")
L.append("5. **The correlation model is trained on simulated bundles.** Its numbers describe the simulation, not field performance. The API adds a time window (default 60 minutes, `window_minutes` per request) and judges a lone event by its detector; both came after training, so the model was not retrained, and the window value has to come from real bundles. Refit and evaluate on the Review-2 test-case set.")
L.append("6. **No real-traffic or time-split evaluation.** All corpora are static public collections.")
L.append("7. **Voice and video detectors are not trained** (no accessible data).")
FRC = R / "final_run" / "tc_cross_check.json"
if FRC.exists():   # written by scripts/final_run_record.py from the Phase 4.1 final run
    X = json.load(open(FRC, encoding="utf-8")); t6 = X["TC-06"]
    L.append(f"8. **The correlation model is sensitive to small changes in its simulated training data.** A full retrain on this build (`run_all.sh` on `{X['build']}`), where the only training change since v2 is the email text cleaner fix (D-11, D-15), "
             f"moves the simulated 60-minute engine's F1 from {pct(X['simulated_f1_60min']['live'])} to {pct(X['simulated_f1_60min']['retrained'])}, but moves the hand-written TC-06 bundle from "
             f"{t6['live detectors + live correlation']:.3f} to {t6['retrained detectors + retrained correlation']:.3f}, below the alert line. The change comes from the correlation model, not the detectors "
             f"(live correlation with retrained detectors: {t6['retrained detectors + live correlation']:.3f}). The retrain failed the adoption rule and was not adopted; the record is in `reports/final_run/`.\n")
else: L[-1] += "\n"
L.append("## 6. Reproduce\n\n```\npip install -r requirements.txt\nbash download_data.sh      # public GitHub sources only\nbash run_all.sh            # trains everything, rewrites reports/\nuvicorn api:app --port 8000\n```\n")
if FRC.exists(): L.append(f"On this build, `run_all.sh` gives models close to but not identical with the shipped ones, because the email text cleaner was fixed after v2 (D-11, D-15). The shipped models are v2's; `reports/final_run/` holds what a retrain gives.\n")
(R / "results.md").write_text("\n".join(L), encoding="utf-8"); print("wrote results.md", len("\n".join(L)), "chars")
