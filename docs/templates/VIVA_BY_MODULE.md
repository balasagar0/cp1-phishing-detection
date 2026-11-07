# Viva preparation by module (R3-24)

For the mock viva and the review. Each module has its owner, how it works in this build, the five hardest questions a panel could ask, and a
short answer that cites a file and a number. Build `{{build.tag}}`. Every number is in `reports/FINAL_NUMBERS.md`.

Two rules for every answer: quote the honest number first, and say "simulated" whenever a correlation number comes up.

## Email and SMS detectors: Krishna

**How it works.** `src/train_email.py` cleans the text (`src/common.py`, `clean_text`), masks numbers, keeps only terms that appear in at least
two corpora, and trains logistic regression on TF-IDF word 1-2-grams. `src/train_sms.py` trains three classes (ham, spam, smishing) on word and
character TF-IDF. `src/predict.py` (`Detectors.score_email`, `score_sms`) scores a message and returns the words that moved the score. The SMS
alert score is 1 - P(ham).

1. **"Papers report near-perfect scores on phishing email. Why is yours lower?"** Ours is {{email.flattering.f1}} on a pooled random split, which is
   what those papers usually report. Trained on two corpora and tested on the third, it is {{email.honest.f1}}. Each corpus has its own style,
   so a random split rewards learning the style. We quote {{email.honest.f1}} (`reports/email_metrics.json`, `leave_one_corpus_out`).
2. **"Why not add more phishing data?"** We tried, {{email.retrain_attempts}} times: extra corpora, a higher alert line, and legitimate
   transactional mail. Each improved the honest F1 but failed our adoption rule, which was written before each run: hard phishing samples got
   worse, or a demo outcome changed. So v2's model stays (`reports/candidates/`).
3. **"How does it do on real mail?"** Badly on legitimate transactional mail. On {{email.realmail.n}} real legitimate emails from one
   consenting user's mailbox it flagged {{email.realmail.fpr}}. The public corpora have little modern bank, order and OTP mail. That is our
   first data limitation.
4. **"Your SMS F1 has a wide interval. Why?"** The test split has only {{sms.smishing_support}} smishing messages, so the 95% interval on the
   smishing F1 of {{sms.honest.f1}} runs from {{sms.honest.f1_ci_low}} to {{sms.honest.f1_ci_high}}. Spam-or-smishing against ham is
   {{sms.flattering.f1}}, but that mixes in easy spam. Two SMS defects are open: D-09 and D-16 (`reports/defect_log.md`).
5. **"Where is the voice detector?"** Not built. We found no voice data we could use. A call is accepted as an event and shown as "not
   assessed"; `/score` answers HTTP 501 for voice. It is never called safe (`tests/test_demo_cases.py::test_tc03_voice_call_is_not_assessed`).

## URL detector, API and console: Viraj

**How it works.** `src/url_features.py` makes the URL canonical (`canon`) and builds character n-grams plus three popularity flags;
`src/train_url.py` trains logistic regression. No network request is ever made. `api.py` serves the routes and the built React console from
`console/`. `check_url` refuses strings that are not URLs.

1. **"Does the URL model visit the site or check a blocklist?"** No. It reads only the URL text: no DNS, no fetch, no lookup.
   `scripts/offline_check.py` blocks every socket and runs all demo cases: {{tests.offline}}.
2. **"Your benchmark says {{url.flattering.f1}}, your slide says {{url.honest.f1}}. Which is right?"** {{url.honest.f1}}, with hosts held out:
   no host appears in both training and test. The {{url.flattering.f1}} is a random split of a feature dataset, where a model can score well
   by checking whether the URL has a path. We quote the host-grouped figure (`reports/url_metrics.json`, `string_model.grouped_test`).
3. **"Why does a real PayPal login page not alert?"** We added three popularity flags and {{url.constructed.train_login_urls}} constructed
   login URLs on popular domains. False alarms on login pages of held-out popular domains fell from {{url.login_fpr.before}} to
   {{url.login_fpr.after}}. The price: recall on bad URLs hosted on popular domains fell from {{url.popular_recall.before}} to
   {{url.popular_recall.after}}. We report both halves.
4. **"What happens if I type rubbish into the URL field?"** HTTP 422 with the reason, for example "it contains spaces" or "no domain ending"
   (`check_url`, defect D-02, `tests/test_defects.py::test_D02_api_refuses_malformed_urls_and_unknown_channels`).
5. **"Is it fast enough for real time?"** Over real HTTP, one at a time, the median was {{latency.url.median}} for a URL, {{latency.email.median}}
   for an email and {{latency.case.median}} for a full case; the slowest full case took {{latency.case.max}} (`reports/benchmark.md`). That was
   the build laptop; the demo laptop still needs its own run.

## Correlation engine and event store: Bala

**How it works.** `src/predict.py` (`extract_ids`) takes identity tokens from each event: registered domains, phone numbers and an optional
identity. `src/fusion.py` groups events into windows of {{window.minutes}} minutes (`time_windows`), describes each window with
{{corr.n_features}} features (`bundle_features`) and scores it with a gradient-boosting model; the bundle takes its highest window
(`window_risks`). `src/event_store.py` keeps each recipient's events hashed and turns windows into campaigns with one alert each.

1. **"Your correlation model is trained on fake data. Why believe it?"** The events are real held-out messages; only the links are
   simulated, because no public dataset links one attacker across channels. We never present the numbers as real: on simulated bundles the
   engine has F1 {{corr.engine.f1}} against {{corr.single.f1}} for single-channel alerting, and false positives {{corr.engine.fpr}} against
   {{corr.single.fpr}}. Most of the gain comes from combining scores: ROC-AUC {{corr.auc.single}}, then {{corr.auc.nocorr}} without link
   and timing features, then {{corr.auc.fusion}} with them. Real bundles (R2-10) will settle it; `src/refit_fusion.py` is ready for them.
2. **"Why {{window.minutes}} minutes?"** It is set at `{{window.file_line}}` and was fixed before the evaluation ran. In the simulation
   {{corr.fit60}} of linked attack bundles fit inside it. We did not pick it from the results table. Without a window the model scores
   better on the simulation (F1 {{corr.nowindow.f1}}), but only because the simulation labels unlinked bundles as a whole; we keep the window
   as the cautious choice, and `refit_fusion.py` will suggest a value from real bundles.
3. **"Is TC-06 robust?"** No, and we say so. It is one hand-written campaign near the line. A retrain on almost the same simulated data moved
   it from {{finalrun.tc06.live}} to {{finalrun.tc06.retrained}}, while the simulated F1 barely moved. We did not adopt that retrain
   (`reports/final_run/README.md`).
4. **"What do you store about people?"** Per event: channel, time, score, label and model version. The recipient and the identity tokens are
   HMAC-SHA256 hashes; message text is not kept unless a setting turns it on. Old events are deleted by `POST /purge`
   (`tests/test_event_store.py::test_recipient_tokens_and_text_are_not_stored_in_clear`, `docs/PRIVACY.md`).
5. **"Your patent draft reports other numbers. Which are true?"** The draft's numbers were generated, not measured, and are retired. The
   patent will be written from this build (owner's decision, 7 Nov 2026). `docs/PATENT_BASIS.md` lists what is built, with code, tests and
   measured numbers.

## Testing and documentation: Manoj

**How it works.** `tests/test_final_cases.py` ports the plan's {{tests.cases.total}} cases to this build. pytest runs every test file;
`tests/smoke_test.py` checks the workbook and refit path. `scripts/make_final_numbers.py` writes the one set of numbers; documents are filled
from it by `scripts/render_docs.py`.

1. **"How many tests pass?"** pytest: {{tests.pytest.passed}} passed, {{tests.pytest.xfailed}} expected failures linked to open defects,
   {{tests.pytest.skipped}} skipped, {{tests.pytest.failed}} failed. The ported plan: {{tests.cases.pass}} of {{tests.cases.total}} pass,
   {{tests.cases.fail}} fail on open defects, {{tests.cases.na}} are N/A (`reports/FINAL_TEST_REPORT.md`).
2. **"You changed the test plan. Isn't that cheating?"** The plan was written for an older codebase with 0-100 scores and verdict bands. We
   kept every ID and the intent: {{tests.cases.tag.ported}} cases are the same check, {{tests.cases.tag.replaced}} keep the intent with this
   build's alert line, {{tests.cases.tag.na}} test features this build does not have. No expectation was weakened; failures are defects.
3. **"Which exit criteria are not met?"** {{tests.exit.met}} of {{tests.exit.of}} rows are met. Not met: sample groups
   ({{tests.exit.3.current}} groups meet their target), the honest measures against the plan's line ({{tests.exit.4b.current}}), correlation
   changing a verdict with real models (SYS-14: {{tests.exit.5.current}}), and open High defects ({{tests.exit.7.current}} open). Targets were never moved after a result (`reports/exit_criteria.md`).
4. **"Why are defects still open?"** {{defects.open}} are open: {{defects.open_list}}. Some need data we do not have (more legitimate
   transactional SMS and email); some need real bundles. Proposals are in `reports/defect_log.md`; accepting one is the team's decision.
5. **"How do we know the numbers on the slides are right?"** They come from one file, `reports/FINAL_NUMBERS.md`, written by a script on
   `{{build.tag}}`. That script refuses to run if the models or code differ from the tag. The retired numbers are listed there and searched
   for across the repository; `tests/test_documents.py` fails if a document carries one.
