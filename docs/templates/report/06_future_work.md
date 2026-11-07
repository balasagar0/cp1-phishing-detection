# Chapter 6. Future work (Capstone 2)

The detailed backlog, with the file and function where each item plugs in, is `docs/CP2_BACKLOG.md`. The road to a usable real-time app is in
`PROJECT_STATUS_AND_ROADMAP.md`. In order of importance:

1. **Collect real bundles with consent.** At least 40 coordinated and 40 benign to evaluate, and 150 to refit
   (`testcases/review2_testcase_workbook.xlsx`, rules in `TESTCASE_FORMAT.md`). Run `python src/refit_fusion.py <file>`: it checks the file,
   evaluates the current model, measures the simulation's assumptions, suggests a window and, with enough bundles, refits. Report the results
   as they come out, including "not shown".
2. **Choose the window from real bundles**, not from the simulation. Today it is {{window.minutes}} minutes, set at `{{window.file_line}}`.
3. **Better email data.** Add modern legitimate transactional mail and real phishing, then retrain under the same adoption rule. The
   current model flags {{email.realmail.fpr}} of one user's real legitimate mail.
4. **More smishing and legitimate transactional SMS**, from sources whose licence can be checked (defects D-09 and D-16).
5. **Voice and deepfake detectors**, once usable data is found. The API already accepts calls and video as "not assessed".
6. **Calibrate the risk** on real bundles so the alert line means something outside the simulation.
7. **A live intake path**: a mail or SMS connector and a message queue in front of `POST /events`, a scheduled purge, and a deployment with
   access control.
