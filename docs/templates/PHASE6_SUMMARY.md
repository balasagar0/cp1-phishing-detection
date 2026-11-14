# CP1 wrap-up (Phase 6)

The summary for the owner at the end of the CP1 finish task. Build `{{build.tag}}`, commit `{{build.commit7}}` ({{build.tag_date}}). Full status
of all 69 items: `CHECKLIST_STATUS.md`. Every number: `reports/FINAL_NUMBERS.md`.

## 1. What is done

| Phase | What | Where |
|---|---|---|
| 0. Baseline | v2 reproduced from scratch; models and reports backed up; repository, rules and checklist set up | `reports/baseline_check.md`, `_baseline_v2/` (local), tag `v2-baseline`, `CLAUDE.md`, `CHECKLIST_STATUS.md` |
| 1. Tests and defects | The plan's {{tests.cases.total}} cases ported (Ported, Replaced or N/A); {{defects.closed}} defects fixed, each with a regression test | `tests/test_final_cases.py`, `tests/test_defects.py`, `reports/defect_log.md`, `reports/Test_Cases_and_Test_Data_FINAL.xlsx` |
| 2. Live flow | Event store with hashed identities, campaigns and alerts; the console served by the API; offline and UI checks | `src/event_store.py`, `api.py`, `console/`, `scripts/offline_check.py`, `scripts/ui_checks.py`, `reports/screenshots/` |
| 3. Models | {{email.retrain_attempts}} email retrain attempts and URL and SMS checks; none adopted under the rule fixed in advance; the private-mail pipeline built and audited | `reports/candidates/`, `PRIVACY_AND_ETHICS.md`, `reports/privacy/` |
| 4. Freeze | Tags `cp1-rc1` and `cp1-final`; the final run recorded and not adopted; every check run on `cp1-final` | `reports/final_run/`, `reports/final_run_check.md`, `reports/e2e_check.md`, `reports/benchmark.md`, `reports/nfr05_fresh_clone.json`, `reports/exit_criteria.md` |
| 5. Documents | One set of numbers and every document generated from it | `reports/FINAL_NUMBERS.md`, `reports/FINAL_TEST_REPORT.md`, `reports/figures/`, `docs/DEMO_SCRIPT.md`, `docs/PATENT_BASIS.md`, `docs/MANUSCRIPT_METHOD_RESULTS.md`, `docs/VIVA_BY_MODULE.md`, `docs/DIARY_ENTRIES.md`, `docs/report/`, `README.md`, `docs/USER_MANUAL.md`, `docs/PRIVACY.md`, `docs/CP2_BACKLOG.md`, `docs/diagrams/` |
| 6. Wrap-up | This summary; the checklist finished | `docs/PHASE6_SUMMARY.md`, `CHECKLIST_STATUS.md` |

Checks on `{{build.tag}}`: pytest {{tests.pytest.passed}} passed, {{tests.pytest.xfailed}} expected failures on open defects,
{{tests.pytest.failed}} failed; end-to-end {{tests.e2e.passed}} of {{tests.e2e.steps}} steps; offline {{tests.offline}}; fresh clone from the
README {{tests.nfr05}}; exit criteria {{tests.exit.met}} of {{tests.exit.of}} rows met.

## 2. Numbers since Review-3

{{review3.same}} of {{review3.n}} Review-3 figures are unchanged on `{{build.tag}}`: the shipped models are v2's, the ones Review-3 described.

{{block:review3}}

**Numbers a retrain would have changed (not adopted).** A full retrain on this build, where only the email text cleaner had changed, moves
the honest email F1 from {{finalrun.email_f1.live}} to {{finalrun.email_f1.retrained}}, the simulated engine F1 from {{finalrun.sim_f1.live}} to
{{finalrun.sim_f1.retrained}}, and the hand-written TC-06 from {{finalrun.tc06.live}} (alert) to {{finalrun.tc06.retrained}} (no alert). It failed
the adoption rule, so none of these is live (`reports/final_run/README.md`).

**New numbers since Review-3** (measured for the first time, not changes):

- Correlation against a parallel multi-channel baseline (simulated): F1 {{corr.parallel.f1}}, false-positive rate {{corr.parallel.fpr}}; 95%
  intervals on every correlation row (`reports/FINAL_NUMBERS.md`, section 2).
- The live email model on real legitimate mail: {{email.realmail.fpr}} false alarms on {{email.realmail.n}} emails of one consenting user; on
  generated legitimate transactional mail: {{email.generatedlegit.fpr}} of {{email.generatedlegit.n}}.
- Latency over real HTTP: median {{latency.email.median}} per email, {{latency.sms.median}} per SMS, {{latency.url.median}} per URL,
  {{latency.case.median}} per full case; slowest full case {{latency.case.max}}.
- Tests: the ported plan {{tests.cases.pass}} pass, {{tests.cases.fail}} fail, {{tests.cases.na}} N/A; exit criteria {{tests.exit.met}} of {{tests.exit.of}}.

**Numbers that must change in other documents.** The Review-2 deck, the Review-3 posters, paper and deck, and the old patent draft carry
retired numbers. Replace each with the figure from `reports/FINAL_NUMBERS.md`; the retired list is its section 9.

## 3. What is left for people, by owner

From `CHECKLIST_STATUS.md` (items that are partial, blocked or for people, with their next step).

{{block:people}}

## 4. Decisions for the owner

1. **Which defects to accept in writing.** {{defects.open}} are open. {{tests.exit.7.current}} of them are High and block exit criterion 7. Accepting one is the team's call;
   write the decision and the reason into the defect log.

{{block:open_defects}}

2. **Voice scope for CP1.** It is `no` now: calls and video are "not assessed", and the review says so. Keep `no`, or switch to `yes` and follow
   the brief's Appendix A, which needs usable voice data first.
3. **The patent.** Decided on 7 Nov 2026: it will be written from this build (`docs/PATENT_BASIS.md`). Still open: whether to file before or
   after real bundles test the correlation claim (`docs/PATENT_BASIS.md`, section 6).
4. **The v3 email model and your mail export.** Both are kept on the build laptop only, outside git. Keep them or delete them; deleting the
   export does not remove what the v3 model learned, so delete both together if you delete.
5. **The demo laptop.** Name it, and have Viraj run `scripts/preflight.py` and `scripts/benchmark.py` on it, and one run with Wi-Fi off.
6. **Real bundles (R2-10).** Who collects the coordinated and benign bundles (40 and 40 to evaluate, 150 to refit), from whose accounts, with what
   written consent. Nothing in CP1's correlation claim can be tested without them.
