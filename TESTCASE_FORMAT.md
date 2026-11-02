# Review-2 multi-channel test cases: file format

This is the format for recording real bundles of events (SMS, email, links, calls) so the correlation model can be tested and refit on real data.
Today it is trained on simulated bundles, because no public dataset links one attacker's events across channels.

## 1. What you record

One row is one event: a message, a link or a call. A **bundle** is everything one person or test account saw in one session
that could be related. Normal traffic is a bundle too. Benign bundles that look linked (a courier sends an SMS and an email about the same parcel) are the most useful ones: they show whether the model over-reacts to links.

Use the workbook `review2_testcase_workbook.xlsx` (sheet **Events**, start at row 7) or a CSV with the same headers.

## 2. Columns

| Column | Required | What goes in it | Example |
|---|---|---|---|
| bundle_id | yes | One id per bundle. Every event of the bundle repeats it. | B014 |
| event_id | no | Unique id of the event. | B014-2 |
| channel | yes | email, sms, url or call. Calls are recorded but not scored yet. | sms |
| time | yes | When it happened, ISO format with timezone. | 2026-11-03T10:02:00+05:30 |
| identity | no | Sender number, sender address or domain, if known. Used to link events. | +91 90000 22222 |
| subject | no | Email subject only. | Re: meeting |
| content | yes | The message text, the URL, or a short note for a call. | Dear customer, your account... |
| event_label | yes | malicious or benign. Decide before you see any model score. | malicious |
| campaign_id | for malicious | Events of the same attacker campaign share one id. | C07 |
| source_type | yes | lab_simulation, collected_real or public_dataset. (example is for the blue rows.) | lab_simulation |
| basis | for collected_real | Why you may use the message. | own account |
| notes | no | Anything useful. | |
| detector_score | no | 0 to 1, only if a detector outside this project scored the event. Otherwise leave empty and the project detectors score it. | |

The bundle labels are worked out for you. A bundle is **malicious** if any event is malicious.
It is **coordinated** if one campaign_id has malicious events on at least two different channels (calls count here).

## 3. Labelling rules

- Label every event on its own, from what it is. Never from a model score.
- Give malicious events from one attacker campaign the same campaign_id, even across bundles (the same SMS sent to two testers is one campaign).
- Put at least a third of your benign bundles in the "linked" kind: several benign events that share a sender or a link.
- If you are unsure, leave the event out. Do not guess.

## 4. Collecting safely

- Use your own accounts, test accounts, or teammates who agreed. Never send phishing to people who did not agree.
- A lab simulation (a teammate plays the attacker with a made-up domain) is fine. Say so in source_type.
- Real messages from your own inbox are fine. Put "own account" in basis. Remove names, numbers and account details of real people: keep the attacker's domain and number, because they are the link evidence.
- Do not open live malicious links. Write them defanged (hxxp://bad[.]top/x). The loader restores them.
- public_dataset rows can pad the benign side, but their times and links are not real behaviour. They are not used to suggest the time window.

## 5. Running the check

```
python src/refit_fusion.py testcases/review2_testcase_workbook.xlsx                 # errors, warnings, evaluation
python src/refit_fusion.py testcases/review2_testcase_workbook.xlsx --save          # also refit and save (needs enough bundles)
python src/refit_fusion.py my_cases.xlsx --target coordinated                       # test the "coordinated attack" claim
python src/refit_fusion.py my_cases.xlsx --window 30 --save                         # use a 30-minute window and keep it in the refit model
```
It always tests the simulation-trained model on your real bundles first, next to the single-channel baseline.
It also prints the three hypothesis tests (H1 to H3) with the decision rules fixed in the Review-2 test plan.
It reports how your measured link rate, timing and weak-campaign share compare with what the simulation assumed.
With at least 20 coordinated bundles from lab or real timing it also suggests the time-clustering window (the 90th percentile of the bundle time span, rounded up to 5 minutes).
The evaluation applies the same time window as the API: 60 minutes unless the model stores another. Events of a bundle further apart than the window are not combined, and the bundle takes the risk of its highest-risk window. Test another value with `--window N`, or use `--no-window` for no limit. With `--save` the window you used is stored in the refit model and the API applies it. To adopt the suggestion, run again with `--window <suggested value> --save`.
After `--save`, restart the API. It uses `models/fusion_model_real.joblib` automatically, and the console footer changes to say so.

## 6. How many bundles

Width of the 95% confidence interval (Wilson) around a measured recall, by number of malicious bundles:

| Malicious bundles | If recall is 90% | If recall is 70% |
|---|---|---|
| 20 | +/- 14 points | +/- 19 points |
| 40 | +/- 10 points | +/- 14 points |
| 80 | +/- 7 points | +/- 10 points |
| 160 | +/- 5 points | +/- 7 points |

Targets (my choices, not measured facts):

- To evaluate only: 40 coordinated bundles and 40 benign bundles.
- To refit: 150 bundles with at least 40 of each class. The default refit has 5 parameters. The script refuses below this.
  A plan that meets it: 50 coordinated, 20 isolated malicious, 40 benign linked, 40 benign unlinked.
- `--model lr` (all 15 features) needs at least 150 bundles per class and is refused below that.

## 7. Leakage

Cross-validation groups bundles by campaign_id, so one campaign never sits in both the training and the test fold. Keep it that way if you split by hand.
Confidence intervals resample whole campaigns for the same reason.

## 8. What this can and cannot show

- If every attack bundle is lab-made by the team, the results describe lab conditions. Say that in the review.
- The refit model learns what is in your file. Timing and linking in a lab reflect how your team plays the attacker.
- Calls are recorded for the record and for the coordinated label. The model cannot score them until a voice detector exists.
- The check command has smoke tests: `python tests/smoke_test.py` (needs `run_all.sh` outputs). They use synthetic rows that are all marked `example`.
- The window splits a bundle. A coordinated campaign whose events are further apart than the window is not recognised as one campaign, and that is the window's trade-off. Keep the real timestamps in the file; do not shift or pad them to fit a window.
