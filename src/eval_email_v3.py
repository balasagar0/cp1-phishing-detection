"""Phase 3.1, email model v3: the third attempt, authorised by the project owner on 7 Nov 2026 after attempts 1 and 2 failed the adoption rule.
Run:  python src/eval_email_v3.py      (about 20 minutes; needs the own-inbox export, see below)
Written, and its rule fixed, BEFORE it was run.

Why: attempts 1 and 2 flagged a legitimate payment receipt (E-L08). The extra phishing corpus is modern transactional language, while every
legitimate corpus is old personal and office mail, so the model learnt "sounds like a transaction, so phishing". v3 adds LEGITIMATE modern
transactional email to training.

v3 = attempt 2's recipe (today's cleaner; CEAS_08, Enron, FraudEmail + Nazario, SpamAssassin, Ling-Spam; C from attempt 1; the alert line set by
attempt 2's rule: no more false alarms than the v2 recipe on held-out legitimate SpamAssassin and Ling-Spam emails, applied as an intercept shift)
PLUS three legitimate sources, all label 0:
  GeneratedLegit  imnim/multiclass-email-classification, MIT: 2,105 emails GENERATED with GPT-3.5 (synthetic, not real messages)
  Templates       Postmark and Mailgun transactional templates, MIT: real company wording, placeholders removed
  OwnInbox        the account owner's own legitimate mail (receipts, bank, order, shipping, OTP and account notices), exported by them, with consent
The adoption rule is unchanged: (a) honest metric (mean F1, held-out CEAS_08, Enron, FraudEmail) not worse than v2's 95% interval; (b) the D-10 and
D-17 workbook cases improve and no EML group falls; (c) TC-01 to TC-08 keep their alert outcome; (d) every test passes after adoption.
Reported beside the rule, not part of it: the false-alarm rate on each legitimate source held out (OwnInbox held out = real receipts the model never
saw), for v3 and for v2's live model. Needs at least 100 own-inbox emails after cleaning; with fewer it stops without training.
The workbook emails, the scenarios and TC-01 to TC-08 are never trained on and never used to set anything; they are only checked afterwards.
Data path (changed BEFORE the first run, 7 Nov 2026, to follow the owner's privacy spec; the rule above is unchanged): the own inbox is never
loaded into a table of texts. src/private_email_training.py streams the .mbox read-only, one message at a time, keeps only integer n-gram counts
for n-grams already in the public candidate vocabulary, and drops each text. The run blocks outbound sockets, checks the archive is byte-identical
before and after, logs counts and metrics only, and saves the model with access limited to the current user. See PRIVACY_AND_ETHICS.md.
Writes reports/candidates/email_candidates_v3.md and .json, and models/candidates/email_model_v3.joblib (git-ignored)."""
import sys, json, math, socket
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import *
import joblib
from scipy import sparse
import train_email as TE
import eval_email_candidates as E1
from eval_email_attempt2 import boot_mean_f1_at, CAL
import private_email_training as P
import email_stream

LEGIT_SRC = ["GeneratedLegit", "Templates", "OwnInbox"]
MIN_OWN = 100
log = TE.log


from network_guard import NoExternalNetwork as Offline          # blocks every connection that would leave the machine; loopback allowed

def main():
    with Offline() as net:
        run(net)


def run(net):
    paths = email_stream.mbox_paths(ROOT / "data" / "raw" / "email_own")
    before = {p.name: P.sha256(p) for p in paths}
    d_pub, dd = TE.load_email(extra=True, legit=True)                 # public sources only; the inbox never enters this table
    cv, Xp = P.candidate_vocab(d_pub.text)
    Xo, st = P.stream_private(paths, cv)
    log("own inbox stream (counts only):", st)
    if st["kept"] < MIN_OWN:
        sys.exit(f"Only {st['kept']} own-inbox emails after cleaning (need {MIN_OWN}). Nothing was trained.")
    X = sparse.vstack([Xp, Xo]).tocsr(); y = np.concatenate([d_pub.label.values.astype(int), np.zeros(Xo.shape[0], dtype=int)])
    src = np.concatenate([d_pub.source.values.astype(object), np.array(["OwnInbox"] * Xo.shape[0], dtype=object)])
    a1 = json.loads((REPORTS / "candidates" / "email_candidates.json").read_text())
    C = a1["C1_candidate"]["chosen_C"]; v2_ci = a1["B0_v2_recipe"]["mean_f1_ci95"]
    counts = {s_: {0: int(((src == s_) & (y == 0)).sum()), 1: int(((src == s_) & (y == 1)).sum())} for s_ in sorted(set(src.tolist()))}
    log("data:", counts)
    d1, _ = TE.load_email(extra=False, legit=False)
    ref = E1.final_model(d1, 16)
    legit_cal = d_pub[d_pub.source.isin(CAL) & (d_pub.label == 0)]
    ref_fpr = float((E1.score_with(ref, legit_cal.text) >= .5).mean())
    log("v3 held-out scores (each source scored by a model trained without it)")
    held, preds = P.held_out(X, y, src, C, E1.V2_CORPORA + E1.NEW + LEGIT_SRC, E1.measure, log)
    cal_neg = np.concatenate([preds[s_][1][preds[s_][0] == 0] for s_ in CAL])
    t = next((float(x) for x in np.round(np.arange(0.5, 0.9951, 0.005), 3) if (cal_neg >= x).mean() <= ref_fpr), 0.995)
    shift = lambda p: 1 / (1 + np.exp(-(np.log(np.clip(p, 1e-12, 1 - 1e-12) / (1 - np.clip(p, 1e-12, 1 - 1e-12))) - math.log(t / (1 - t)))))
    at_t = {s_: E1.measure(preds[s_][0], shift(preds[s_][1])) for s_ in preds}
    mean_t = round(float(np.mean([at_t[s_]["f1"] for s_ in E1.V2_CORPORA])), 4)
    log(f"alert line t={t}; honest mean F1 {mean_t}")
    F = P.MatrixFeat(X, src, np.arange(X.shape[0])); clf = P.fit_lr(F.Xtrain, y, C); clf.intercept_ = clf.intercept_ - math.log(t / (1 - t))
    cand = P.text_model(cv, F, clf, {"channel": "email", "trained_with_private_mail": True, "private_emails": int(Xo.shape[0]),
                                     "sources": sorted(set(src.tolist())), "C": C})
    saved = P.save_private(cand, E1.OUTM / "email_model_v3.joblib")
    live = joblib.load(MODELS / "email_model.joblib")
    live_fpr = {s_: round(float((E1.score_with(live, d_pub[d_pub.source == s_].text) >= .5).mean()), 4) for s_ in ("GeneratedLegit", "Templates")}
    flagged, n_seen, seen = 0, 0, set()                                 # the live model on the inbox: streamed again, counts only
    for text in email_stream.iter_texts(paths):
        c_ = clean_text(text, mask_numbers=True); text = None
        if len(c_) < 25 or norm_key(c_) in seen: c_ = None; continue
        seen.add(norm_key(c_)); n_seen += 1; flagged += int(E1.score_with(live, [c_])[0] >= .5); c_ = None
    live_fpr["OwnInbox"] = round(flagged / max(n_seen, 1), 4)
    after = {p.name: P.sha256(p) for p in paths}
    res = {"attempt": "v3 (third, authorised by the project owner on 7 Nov 2026)", "rule_fixed_before_running": __doc__.split("v3 = ")[1].split("Data path")[0].strip(),
           "chosen_C": C, "alert_line_t": t, "data": {"public_dedupe": dd, "own_inbox_stream": st, "counts": counts},
           "privacy": {"outbound_connection_attempts": net.attempts, "archive_unchanged": before == after, "archives": len(paths), "model_file": saved,
                       "note": "The first run (7 Nov 2026) stopped at the demo-case step: its network guard also blocked loopback, which Windows' asyncio needs. This run is the same procedure; the guard now allows loopback and still blocks and counts everything that would leave the machine."},
           "calibration": {"corpora": CAL, "v2_recipe_false_positive_rate": round(ref_fpr, 4), "v3_false_positive_rate_at_0.5": round(float((cal_neg >= .5).mean()), 4),
                           "v3_false_positive_rate_at_t": round(float((cal_neg >= t).mean()), 4)},
           "held_out_at_t": at_t, "mean_f1_at_t": mean_t, "mean_f1_at_t_ci95": boot_mean_f1_at({s_: preds[s_] for s_ in E1.V2_CORPORA}, t), "v2_mean_f1_ci95": v2_ci,
           "legit_sources_false_alarms": {s_: {"v3_held_out": at_t[s_].get("false_positive_rate"), "live_v2": live_fpr[s_], "n": at_t[s_]["n"]} for s_ in LEGIT_SRC},
           "samples_live": E1.sample_checks(live, "live v2 model"), "samples_candidate": E1.sample_checks(cand, "v3")}
    res["demo_cases"] = E1.demo_outcomes(cand)
    sl, sc = res["samples_live"], res["samples_candidate"]
    keys = ["EML-01 standard phishing", "EML-02 standard legitimate", "EML-03 hard phishing", "EML-03 hard legitimate"]
    a = mean_t >= v2_ci[0]
    b = (len(sc["D-10 cases correct"]) + len(sc["D-17 cases correct"]) > len(sl["D-10 cases correct"]) + len(sl["D-17 cases correct"])) and all(sc[k] >= sl[k] for k in keys)
    c = all(v["live"] is None and v["candidate"] is None or (v["live"] and v["candidate"] and v["live"]["alert"] == v["candidate"]["alert"]) for v in res["demo_cases"].values())
    res["adoption"] = {"a_honest_metric_not_worse_than_v2_beyond_ci": a, "a_detail": f"v3 mean held-out F1 {mean_t} vs v2 95% interval {v2_ci}",
                       "b_target_defect_cases_improve": b, "c_demo_cases_keep_alert_outcome": c, "d_every_test_passes": "checked after adoption by running the tests",
                       "privacy_audit": "scripts/privacy_audit_email.py must pass before the model is used (PRIVACY_AND_ETHICS.md)",
                       "decision": "v3 passes (a) to (c); the privacy audit comes next" if a and b and c else "keep v2's model; v3 is a negative result"}
    save_json(res, E1.OUTR / "email_candidates_v3.json"); write_md(res); log("decision:", res["adoption"]["decision"])


def write_md(r):
    pct = lambda x: "–" if x is None else f"{100 * x:.1f}%"
    cal, pv = r["calibration"], r["privacy"]
    L = ["# Email model v3 (Phase 3.1, third attempt)\n", "Written by `src/eval_email_v3.py`. Its rule was fixed in the script before it ran:\n", "> " + r["rule_fixed_before_running"].replace("\n", " ") + "\n",
         "## Training data\n", "| Source | Legitimate | Unwanted |", "|---|---|---|"]
    for s, c in r["data"]["counts"].items(): L.append(f"| {s} | {c.get(0, 0):,} | {c.get(1, 0):,} |")
    st = r["data"]["own_inbox_stream"]
    L += ["", "GeneratedLegit is synthetic (GPT-3.5). Templates are company templates with placeholders removed. OwnInbox is the account owner's own legitimate mail, "
          "used with their consent, streamed (never stored as text) and never committed.", "",
          f"Own-inbox stream: {st['read']:,} messages read, {st['skipped_spam_trash']:,} skipped as Spam or Trash, {st['failed']:,} unreadable, {st['empty'] + st['too_short']:,} too short, "
          f"{st['duplicates_dropped']:,} exact duplicates, {st['kept']:,} used.", "",
          f"Privacy of this run: outbound connection attempts {pv['outbound_connection_attempts']}; archive byte-identical before and after: {pv['archive_unchanged']}; "
          f"model file: {pv['model_file']['permissions']}, encrypted: {pv['model_file']['encrypted']}. {pv['note']}", "",
          f"## The alert line\n\nFalse alarms on held-out legitimate {', '.join(cal['corpora'])} emails: v2 recipe {pct(cal['v2_recipe_false_positive_rate'])}; v3 at 0.5 {pct(cal['v3_false_positive_rate_at_0.5'])}; "
          f"v3 at the chosen line {pct(cal['v3_false_positive_rate_at_t'])}. Chosen line t = **{r['alert_line_t']}** (an intercept shift, so the API keeps 0.5).", "",
          "## Held-out sources at the chosen line\n", "| Source held out | v3 |", "|---|---|"]
    for s, m in r["held_out_at_t"].items():
        L.append(f"| {s} | " + (f"F1 {pct(m['f1'])} (P {pct(m['precision'])}, R {pct(m['recall'])}, FPR {pct(m['false_positive_rate'])})" if "f1" in m else
                               (f"recall {pct(m['recall'])} (n={m['n']:,})" if "recall" in m else f"false-alarm rate {pct(m['false_positive_rate'])} (n={m['n']:,})")) + " |")
    L += ["", f"Honest metric (mean F1 over held-out CEAS_08, Enron, FraudEmail): v3 **{pct(r['mean_f1_at_t'])}** (95% interval {pct(r['mean_f1_at_t_ci95'][0])} to {pct(r['mean_f1_at_t_ci95'][1])}); "
          f"v2's 95% interval {pct(r['v2_mean_f1_ci95'][0])} to {pct(r['v2_mean_f1_ci95'][1])}.", "",
          "## False alarms on legitimate transactional email the model never saw (reported, not part of the rule)\n", "| Source | n | v3 (source held out) | live v2 model |", "|---|---|---|---|"]
    for s, v in r["legit_sources_false_alarms"].items(): L.append(f"| {s} | {v['n']:,} | {pct(v['v3_held_out'])} | {pct(v['live_v2'])} |")
    L += ["", "## Workbook emails (hand-written, not a test set; never trained on, never used to set anything)\n", "| Check | live v2 model | v3 |", "|---|---|---|"]
    sl, sc = r["samples_live"], r["samples_candidate"]
    for k in ("EML-01 standard phishing", "EML-02 standard legitimate", "EML-03 hard phishing", "EML-03 hard legitimate"): L.append(f"| {k} | {pct(sl[k])} | {pct(sc[k])} |")
    L.append(f"| D-10 emails right (E-L08, E-H06, E-H04, E-L06) | {', '.join(sl['D-10 cases correct']) or 'none'} | {', '.join(sc['D-10 cases correct']) or 'none'} |")
    L.append(f"| D-17 emails right (E-P03, E-P06, E-P07, E-P09, E-H01) | {', '.join(sl['D-17 cases correct']) or 'none'} | {', '.join(sc['D-17 cases correct']) or 'none'} |")
    L += ["", "## Demo cases (hand-written): alert outcome\n", "| Case | live | v3 |", "|---|---|---|"]
    for cid, v in r["demo_cases"].items():
        f = lambda x: "CANNOT_ASSESS" if x is None else f"{x['risk']:.3f} ({'alert' if x['alert'] else 'no alert'})"
        L.append(f"| {cid} | {f(v['live'])} | {f(v['candidate'])} |")
    a = r["adoption"]
    L += ["", "## Adoption rule\n", f"- (a) honest metric not worse than v2's beyond its 95% interval: **{a['a_honest_metric_not_worse_than_v2_beyond_ci']}** ({a['a_detail']})",
          f"- (b) the target defects' cases improve (D-10, D-17): **{a['b_target_defect_cases_improve']}**", f"- (c) TC-01 to TC-08 keep their alert outcome: **{a['c_demo_cases_keep_alert_outcome']}**",
          f"- (d) every test passes: {a['d_every_test_passes']}", f"- privacy: {a['privacy_audit']}", f"\n**Decision: {a['decision']}.**"]
    (E1.OUTR / "email_candidates_v3.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
