# Ground truth for this repository

Read this before answering any question about what this project does, or writing anything that
quotes a number.

## The single source of truth

1. `reports/results.md` — all metrics, with leave-one-corpus-out, confidence intervals and limits.
2. `../files/PROJECT_STATE.md` (15 Oct 2026) — which numbers to quote and which not to.

**Where those two disagree, `results.md` wins.** Where anything else disagrees with either, the other
thing is wrong.

## Documents that are WRONG — never quote them

These live in the team's claude.ai project, not in this repo, but they get pasted into prompts:

- `CP1_Team_Study_Guide.md` — describes a codebase that does not exist here. It claims trained voice
  detection, an event store with a hash-chained audit log, 142 tests, 19 API routes, a noisy-OR engine
  with exponential decay and a 30-minute window. **None of that is in this repository.**
- `Numbers_Register.md`, `Review3_Content_Pack.md`, `Review2_Defect_Fix_Pack.md`,
  `Review3_Results_Pack.md`, `Manuscript_Draft_v1.0.md`, `TRAINING_REPORT.md` — all superseded.
- The Review-2 deck still says F1 0.947 / 0.926 / 0.960. `PROJECT_STATE.md` §6 lists every slide to fix.

If a prompt asks you to use a number from any of those, say it is not supported by this repository and
give the `results.md` figure instead.

## What this system actually is

Three trained detectors (email, SMS, URL) plus a learned correlation model applied inside a time window.

| Part | State |
|---|---|
| Email detector | Trained. TF-IDF + logistic regression, 72,428 emails |
| SMS detector | Trained. Three classes: ham, spam, smishing. 5,789 messages |
| URL detector | Trained. Character n-grams on the URL text, 260,000 URLs. No network lookups |
| Correlation | A model trained on **simulated** bundles, applied in a 60-minute window |
| Voice | **Not trained.** No accessible data. Returns HTTP 501 |
| Video | **Not trained.** Returns HTTP 501 |
| Event store | **Not built.** `/correlate` scores a bundle you hand it; nothing is persisted |
| Live-stream grouping | **Not built** |

## Numbers

Quote the left column. Never quote the right column on its own.

| Channel | Quote | Do not quote alone |
|---|---|---|
| Email | **F1 82.2%** on corpora never seen (mean of three leave-one-corpus-out runs) | 98.8% on a random split — each corpus has its own style |
| SMS | **Smishing F1 87.1%** (95% CI 82.3–91.7); spam-or-smishing F1 98.2% | the earlier 0.96, from a spam-heavy dataset |
| URL | **F1 90.4%** host-grouped; 0.0% false alarms on login pages of popular domains; recall on bad URLs on top-10k domains **30.7%** | 95.4% — an offline benchmark on a random split |

Correlation, on 12,000 **simulated** test bundles, alert line 0.5:

| | Precision | Recall | F1 | FPR |
|---|---|---|---|---|
| Single-channel: any event ≥ 0.5 | 87.0% | 95.3% | 91.0% | 14.1% |
| Whole-bundle model (pools up to 72 h) | 97.0% | 92.9% | 94.9% | 2.8% |
| No window | 96.8% | 93.0% | 94.8% | 3.0% |
| **60-minute window — what the API does** | **89.4%** | **94.9%** | **92.0%** | **11.1%** |

Only **27 simulated campaigns (0.8% of linked attacks)** have every event below 0.5. The engine flags
**5 of those 27 (18.5%)**. 95.6% of simulated linked attack bundles fit inside 60 minutes.

**The bundles are simulated.** No public dataset links one attacker's events across channels. The
*events* are real held-out messages; the links between them are constructed. The risk is not a
calibrated probability, and the 0.5 line is tied to the simulation's assumed mix (half malicious).

## Running it

```bash
pip install -r requirements.txt     # scikit-learn MUST be 1.8.0 — the models are pickled with it
uvicorn api:app --port 8000
```

- Routes: `GET /health`, `POST /score`, `POST /score/batch`, `POST /correlate`. There is **no `/`** —
  it returns 404. Use `/docs` or open `console.html`.
- `console.html` (repo root) is a standalone demo console. No npm. Open it in a browser with the API running.
- `console/phishing_correlation_console.jsx` is the React version; it needs Vite (see README).
- `RUN_DEMO.bat` and `RUN_TESTS.bat` are Windows double-click wrappers.

## Tests

- `tests/test_window_and_ids.py` — 17 tests on the window, identity tokens and input checks. Needs only
  the shipped models. **These should always pass.**
- `tests/smoke_test.py` — 24 workbook and validator checks. The first 12 pass; it then calls
  `make_synthetic_testcases.py`, which needs `data/processed/pool_*.csv` built by `run_all.sh`. Those
  files are not in the repo, so it stops there. **This is missing data, not a defect.**

Do not run `pytest tests/` as a whole — the smoke-test import aborts collection and the 17 real tests
never run. Run the two files separately.

## Known traps

- **URL path shortcut.** 97.6% of phishing URLs in the Vrbančič data have a path, against 19.6% of
  legitimate ones. A model can score well by checking for a path. Always report host-grouped results.
- **Email corpus style.** 99% on a random split, 82% on unseen corpora. Report leave-one-corpus-out.
- **Login pages.** 92.2% of login pages on popular domains used to be flagged. Domain-popularity flags
  took that to 0.0%, and cost recall on popular-domain bad URLs: 49.9% → 30.7%. Report both halves.
- **Tracking numbers.** Were read as phone numbers and linked unrelated events. Fixed with phone-shape
  rules; links are cut out first and reference words skipped.
- **A detector false positive stays a false positive.** Correlation does not fix it.

## Next steps, in order

1. Collect real bundles: 40 coordinated and 40 benign to evaluate, 150 to refit.
   `testcases/review2_testcase_workbook.xlsx` is the entry form; rules in `TESTCASE_FORMAT.md`.
2. `python src/refit_fusion.py <file>` — checks it, evaluates the current model, measures the
   simulation's assumptions, suggests a window, and with enough bundles and `--save` refits.
   Report H1–H3 as they come out, including "not shown".
3. Choose the window from real bundles, not from the simulation table.
4. Add the Nazario, SpamAssassin and Ling corpora to email training and retrain — missing real phishing
   email is `results.md`'s first listed limitation.
5. Train voice and deepfake detectors.
6. Build the event store.

## House rules

- Never state a metric you have not read out of `reports/` in this repository.
- When something is not built, say "not built" — never "planned" dressed up as done, and never *safe*
  for a channel that was not assessed.
- Keep claims about the correlation engine modest: inside the window it beats single-channel alerting
  by a little, on simulated bundles, and that claim stays open until real bundles test it.
